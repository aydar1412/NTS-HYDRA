# -*- coding: utf-8 -*-
# NTS-HYDRA - drilling hydraulics calculation
# Copyright 2026 Aydar Rakhmatullin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
==========================================================================
 ПОИНТЕРВАЛЬНЫЙ / ПОСЕКЦИОННЫЙ ГИДРАВЛИЧЕСКИЙ РАСЧЁТ
==========================================================================
 Логика:
   1) для каждого интервала долотной программы собирается бурильная
      колонна: КНБК снизу + бурильные трубы до устья;
   2) ствол разбивается узлами: смена элемента колонны, башмак колонны,
      кровля открытого ствола;
   3) на каждом участке считаются потери внутри колонны и в затрубье;
   4) суммируются потери, считается давление на насосе, ЭЦП, вынос шлама.
==========================================================================
"""

import math
import re
from dataclasses import dataclass, field

import numpy as np

import hydraulics_config as CFG
from hydraulics_extra import resolve
from hydraulics_lang import t
from hydraulics_rheology import (
    Rheology, pipe_flow, annulus_flow, eccentricity_at, gel_break_pressure,
    density_at, temperature_profile,
)
from hydraulics_holecleaning import hole_cleaning, required_flow
from hydraulics_core import (
    Fluid, InputData, Trajectory, BhaItem, to_float, parse_range,
    grad_pipe, grad_ann, bit_hydraulics, nozzle_area,
    slip_velocity, cuttings_concentration, warn,
)

MM = 1e-3


# ==========================================================================
#  1. СБОРКА ИНТЕРВАЛОВ
# ==========================================================================

SECTION_ALIAS = {
    "направление": "Направление",
    "кондуктор": "Кондуктор",
    "экс.колонна": "Экс.колонна",
    "эксплуатационная колонна": "Экс.колонна",
    "хвостовик": "Хвостовик",
}


def make_intervals(data: InputData):
    """
    Превращает строки долотной программы в список расчётных интервалов
    с уникальными ключами ('Кондуктор 1', 'Кондуктор 2', ...).
    """
    if getattr(data, "format", "legacy") == "template":
        return _intervals_from_template(data)

    counters = {}
    intervals = []
    for row in data.bitprog:
        sec_raw = row["секция"].strip()
        sec = SECTION_ALIAS.get(sec_raw.lower(), sec_raw)
        counters[sec] = counters.get(sec, 0) + 1
        same = sum(1 for r in data.bitprog
                   if SECTION_ALIAS.get(r["секция"].strip().lower(),
                                        r["секция"].strip()) == sec)
        key = sec if same == 1 else f"{sec} {counters[sec]}"

        mud = data.mud.get(sec, {})
        rho = to_float(mud.get("Плотность, г/см3"), 1.15)
        bit = to_float(mud.get("Номинальный диаметр ствола, мм"))
        pv = to_float(mud.get("Пластическая вязкость, сПз"),
                      CFG.DEFAULT_RHEOLOGY["pv_cP"])
        yp = to_float(mud.get("ДНС, фунт/100кв.футов"),
                      CFG.DEFAULT_RHEOLOGY["yp_lb100ft2"])
        q = parse_range(row["расход_raw"], CFG.FLOW_CHOICE)

        # уточнённая реология из листа «Реология» имеет приоритет
        ex = getattr(data, "extra", {}) or {}
        fann = (ex.get("rheology", {}).get(key)
                or ex.get("rheology", {}).get(sec))
        if fann and fann.get("t600") and fann.get("t300"):
            pv = fann["t600"] - fann["t300"]
            yp = fann["t300"] - pv
            if fann.get("rho"):
                rho = fann["rho"]

        if bit is None:
            warn(f"Для секции «{sec}» не найден номинальный диаметр ствола.")
            bit = 295.3

        intervals.append(dict(
            key=key, section=sec,
            md_from=row["от"], md_to=row["до"],
            rop=row["мсп"], drive=row["привод"],
            q_lps=q, q_raw=row["расход_raw"],
            bit_mm=bit, rho=rho, pv=pv, yp=yp,
        ))
    return intervals


def _intervals_from_template(data):
    """Интервалы из листа «05 Интервалы бурения» шаблона NTS-HYDRA."""
    ex = data.extra
    out = []
    for i in ex["intervals"]:
        key = i["key"]
        sec = SECTION_ALIAS.get(re.sub(r"\s*\d+$", "", key).strip().lower(),
                                re.sub(r"\s*\d+$", "", key).strip())
        mud = (ex.get("mud", {}).get(key)
               or ex.get("mud", {}).get(sec) or {})
        rho = mud.get("rho")
        if rho is None:
            rho = 1.15
            warn(f"Для интервала «{key}» не задана плотность раствора - "
                 f"принята {rho:.2f} г/см³.")
        if mud.get("t600") and mud.get("t300"):
            pv = mud["t600"] - mud["t300"]
            yp = mud["t300"] - pv
        else:
            pv = CFG.DEFAULT_RHEOLOGY["pv_cP"]
            yp = CFG.DEFAULT_RHEOLOGY["yp_lb100ft2"]
        bit = i["bit_mm"]
        if bit is None:
            bit = 295.3
            warn(f"Для интервала «{key}» не задан диаметр долота - "
                 f"принят {bit} мм.")
        q = i["q_lps"]
        if q is None:
            q = 40.0
            warn(f"Для интервала «{key}» не задан расход - принят {q:.0f} л/с.")
        model = mud.get("модель")
        if model in (None, "auto"):
            if mud.get("t6") and mud.get("t3"):
                model = "herschel_bulkley"
            elif mud.get("t600") and mud.get("t300"):
                model = "power_law"
            else:
                model = "bingham"
        out.append(dict(
            key=key, section=sec, md_from=i["md_from"], md_to=i["md_to"],
            rop=i["rop"] or 10.0, drive=i["drive"] or "-",
            q_lps=q, q_raw=str(i["q_raw"]),
            bit_mm=bit, bit_type=i.get("bit_type", ""),
            rho=rho, pv=pv, yp=yp, model=model,
        ))
    data.models_used = [o["model"] for o in out]
    return out


def get_bha(data: InputData, key, section):
    """КНБК для интервала: из листа Excel либо из шаблона конфигурации."""
    sheet = CFG.BHA_SHEET_FOR.get(key)
    if sheet is None:
        sheet = CFG.BHA_SHEET_FOR.get(section)
    if sheet and sheet in data.bha_sheets:
        return list(data.bha_sheets[sheet]), False

    # автоподбор: лист «КНБК (<секция>)» или «КНБК (<интервал>)»
    def norm(t):
        return re.sub(r"[^а-яa-z0-9]", "", str(t).lower())

    for cand in (key, section):
        for name in data.bha_sheets:
            inner = name[name.find("(") + 1:name.rfind(")")] if "(" in name else name
            if norm(inner) == norm(cand):
                return list(data.bha_sheets[name]), False

    tmpl = CFG.BHA_TEMPLATE.get(key) or CFG.BHA_TEMPLATE.get(section)
    if tmpl:
        warn(f"Для интервала «{key}» в файле нет листа КНБК - "
             f"использован ОРИЕНТИРОВОЧНЫЙ шаблон из hydraulics_config.py. "
             f"Дополните файл фактической компоновкой.")
        from hydraulics_core import classify_element
        return [BhaItem(n, L, od, idd, classify_element(n))
                for (n, L, od, idd) in tmpl], True
    warn(f"Для интервала «{key}» нет ни листа КНБК, ни шаблона - интервал пропущен.")
    return None, True


def get_dp(data, key, section):
    d = pick(data, "drillpipe", key, section, CFG.DRILLPIPE)
    if d is None:
        d = {"имя": "СБТ 127", "od_mm": 127.0, "id_mm": 108.6}
    return d


def cfg_for(dic, key, section, default=None):
    if key in dic:
        return dic[key]
    if section in dic:
        return dic[section]
    return default


def pick(data, group, key, section, cfg_dict, default=None):
    """Значение из Excel (приоритет) либо из конфигурации."""
    ex = getattr(data, "extra", {}) or {}
    val, src = resolve(ex, group, key, section, cfg_dict, default)
    return val


# ==========================================================================
#  2. ГЕОМЕТРИЯ
# ==========================================================================

@dataclass
class StringPart:
    """Участок бурильной колонны по глубине (сверху вниз)."""
    name: str
    md_top: float
    md_bot: float
    od_mm: float
    id_mm: float
    kind: str

    @property
    def length(self):
        return self.md_bot - self.md_top


def build_string(bha, td, dp_info, key, section):
    """
    Сборка колонны от забоя (td) до устья.
    Список КНБК идёт сверху листа = от долота вверх.
    """
    parts = []
    md = td
    for it in bha:
        L = it.length_m or 0.0
        if md - L < 0:
            L = md
        top = md - L
        idd = it.id_mm
        if idd is None:
            idd = {"bit": 0.0, "motor": None, "mwd": None}.get(it.kind, None)
        parts.append(StringPart(it.name, top, md, it.od_mm,
                                idd if idd else 0.0, it.kind))
        md = top
        if md <= 1e-6:
            break
    if md > 1e-6:
        parts.append(StringPart(dp_info["имя"], 0.0, md,
                                dp_info["od_mm"], dp_info["id_mm"], "dp"))
    parts.sort(key=lambda p: p.md_top)
    return parts


def outer_diameter_at(md, casings, bit_mm, md_from, cav):
    """
    Наружная граница затрубного пространства на глубине md, мм.
    Ниже башмака последней спущенной колонны - открытый ствол.
    """
    # колонны, уже спущенные к моменту бурения интервала
    set_casings = [c for c in casings if c.md_m <= md_from + 1e-6]
    # из них те, что перекрывают данную глубину
    covering = [c for c in set_casings if c.md_m >= md - 1e-6]
    if covering:
        c = min(covering, key=lambda x: x.id_mm)
        return c.id_mm, f"ОК {c.od_mm:.0f} (Ø вн. {c.id_mm:.1f})"
    return bit_mm * cav, f"откр. ствол {bit_mm:.1f}×{cav:.2f}"


# ==========================================================================
#  3. РАСЧЁТ ОДНОГО ИНТЕРВАЛА
# ==========================================================================

@dataclass
class SegResult:
    zone: str
    name: str
    md_top: float
    md_bot: float
    d_out: float
    d_in: float
    V: float
    Re: float
    mode: str
    grad: float          # Па/м
    dp: float            # Па
    note: str = ""


def calc_interval(itv, data: InputData, traj: Trajectory, q_lps=None,
                  quiet=False, td_override=None):
    """
    Полный гидравлический расчёт интервала. По умолчанию - на конечной
    глубине; td_override позволяет посчитать ту же компоновку на любой
    другой глубине, например в начале интервала.
    """
    key, section = itv["key"], itv["section"]
    td = td_override if td_override is not None else itv["md_to"]
    md_from = itv["md_from"]
    Q = (q_lps if q_lps is not None else itv["q_lps"]) / 1000.0     # м3/с
    fann = pick(data, "rheology", key, section, None)
    rho = itv["rho"]
    if fann and fann.get("rho"):
        rho = fann["rho"]
    model = itv.get("model") or CFG.RHEOLOGY_MODEL
    fluid = Fluid(rho, itv["pv"], itv["yp"], section, fann=fann, model=model)
    itv = dict(itv)
    itv["rho"] = rho
    rpm = pick(data, "rpm", key, section,
               getattr(CFG, "ROTATION_RPM", {}), 0.0) or 0.0

    bha, is_template = get_bha(data, key, section)
    if bha is None:
        return None
    dp_info = get_dp(data, key, section)
    parts = build_string(bha, td, dp_info, key, section)

    bit_mm = itv["bit_mm"]
    bit_d_m = bit_mm * MM
    cav = pick(data, "caving", key, section, CFG.CAVING_FACTOR, 1.10)

    # -------------------------------------- потери в наземной обвязке ---
    surf_list = (getattr(data, "extra", {}) or {}).get("surface") or []
    if surf_list:
        dp_surface = 0.0
        for nm, L, d in surf_list:
            dp_surface += pipe_flow(Q, d * MM, fluid).dpdl * L
    else:
        surf = cfg_for(CFG.SURFACE_EQUIP, key, section, (200.0, 96.8))
        dp_surface = pipe_flow(Q, surf[1] * MM, fluid).dpdl * surf[0]

    # --------------------------------------------- внутри бурильной ----
    inside = []
    dp_motor = dp_mwd = 0.0
    motor_cfg = pick(data, "motor", key, section, CFG.MOTOR)
    mwd_cfg = pick(data, "mwd", key, section, CFG.MWD)

    for p in parts:
        if p.kind == "bit":
            continue
        if p.kind == "motor":
            if motor_cfg:
                qr = motor_cfg["q_ref_лс"] / 1000.0
                dpm = (motor_cfg["dp_xx_МПа"] * (Q / qr) ** 2 +
                       motor_cfg["dp_load_МПа"]) * 1e6
            else:
                dpm = 0.0
                if not quiet:
                    warn(f"«{p.name}» в интервале {key}: не задан перепад давления.")
            dp_motor += dpm
            inside.append(SegResult("внутри", p.name, p.md_top, p.md_bot,
                                    p.od_mm, p.id_mm, 0, 0, "-",
                                    dpm / max(p.length, 1e-6), dpm,
                                    "перепад по паспорту"))
            continue
        if p.kind == "mwd" and mwd_cfg:
            qr = mwd_cfg["q_ref_лс"] / 1000.0
            dpw = mwd_cfg["dp_МПа"] * (Q / qr) ** 2 * 1e6
            dp_mwd += dpw
            fr = pipe_flow(Q, max(p.id_mm, 1.0) * MM, fluid)
            g, V, Re, mode = fr.dpdl, fr.V, fr.Re, fr.mode
            total = g * p.length + dpw
            inside.append(SegResult("внутри", p.name, p.md_top, p.md_bot,
                                    p.od_mm, p.id_mm, V, Re, mode,
                                    total / max(p.length, 1e-6), total,
                                    "вкл. перепад телесистемы"))
            continue
        if p.id_mm <= 0:
            if not quiet:
                warn(f"«{p.name}» ({key}): не задан внутренний диаметр - "
                     f"потери внутри элемента не учтены.")
            inside.append(SegResult("внутри", p.name, p.md_top, p.md_bot,
                                    p.od_mm, p.id_mm, 0, 0, "-", 0, 0,
                                    "нет Ø вн."))
            continue
        fr = pipe_flow(Q, p.id_mm * MM, fluid)
        g, V, Re, mode = fr.dpdl, fr.V, fr.Re, fr.mode
        k = 1.0
        if p.kind == "dp":
            k = _tooljoint_factor(Q, dp_info, fluid)
        dpp = g * p.length * k
        inside.append(SegResult("внутри", p.name, p.md_top, p.md_bot,
                                p.od_mm, p.id_mm, V, Re, mode, g * k, dpp))

    dp_inside = sum(s.dp for s in inside)

    # ------------------------------------------------------- долото ----
    nz = pick(data, "nozzles", key, section, CFG.NOZZLES, [16, 16, 16])
    bh = bit_hydraulics(Q, nz, fluid.rho, bit_d_m)
    dp_bit = bh["dp_Pa"]

    # ------------------------------------------------------ затрубье ---
    # Долото в затрубье не моделируется как труба (это насадочный узел):
    # его длина присоединяется к вышележащему элементу.
    ann_parts = []
    for p in parts:
        if p.kind == "bit" and ann_parts:
            ann_parts[-1] = StringPart(ann_parts[-1].name, ann_parts[-1].md_top,
                                       p.md_bot, ann_parts[-1].od_mm,
                                       ann_parts[-1].id_mm, ann_parts[-1].kind)
        elif p.kind != "bit":
            ann_parts.append(p)
    if not ann_parts:
        ann_parts = parts

    # ------------------------------------------------ узлы разбиения ----
    nodes = {0.0, td, md_from}
    for p in ann_parts:
        nodes.add(p.md_top)
        nodes.add(p.md_bot)
    for c in data.casings:
        if 0 < c.md_m < td:
            nodes.add(c.md_m)
    nodes = sorted(n for n in nodes if -1e-6 <= n <= td + 1e-6)

    ann = []
    ct = pick(data, "cuttings", key, section, None) or {}
    strat_rho = ct.get("rho") or _strat_density(data, md_from, td)
    rho_cut = strat_rho * 1000.0
    d_part = (ct.get("d_mm") or CFG.CUTTINGS_SIZE_MM) * MM
    # критерии из исходных данных имеют приоритет над общими
    crit = dict(CFG.CRIT)
    if ct.get("c_max"):
        crit["Cшлам_макс_%"] = ct["c_max"]
    if ct.get("v_min"):
        crit["Vкц_мин_верт_мс"] = ct["v_min"]
        crit["Vкц_мин_наклон_мс"] = max(ct["v_min"],
                                        CFG.CRIT["Vкц_мин_наклон_мс"] * 0.0
                                        + ct["v_min"])

    for i in range(len(nodes) - 1):
        m0, m1 = nodes[i], nodes[i + 1]
        if m1 - m0 < 1e-4:
            continue
        mid = 0.5 * (m0 + m1)
        p = _part_at(ann_parts, mid)
        if p is None:
            continue
        d_out, tag = outer_diameter_at(mid, data.casings, bit_mm,
                                       md_from, cav)
        d_in = p.od_mm
        if d_out <= d_in:
            d_out = d_in + 6.0
            if not quiet:
                warn(f"Интервал {key}, {m0:.0f}-{m1:.0f} м: наружный диаметр "
                     f"элемента «{p.name}» ({d_in:.1f} мм) не проходит в "
                     f"Ø{tag} - проверьте геометрию!")
        inc = traj.inc_at(mid)
        ecc = eccentricity_at(inc)
        do_m, di_m = d_out * MM, d_in * MM

        # лопастные элементы: поток идёт между лопастями, а не по
        # сплошному кольцу - подбираем эквивалентный диаметр по площади
        # поправка применяется, только если указан диаметр ПО ЛОПАСТЯМ:
        # если в данных стоит диаметр корпуса, зазор и так свободен
        if (getattr(p, "kind", "") == "stab"
                and di_m > do_m * getattr(CFG, "BLADE_MIN_RATIO", 0.85)):
            di_m = _bladed_equivalent(do_m, di_m)

        hc = hole_cleaning(fluid, Q, do_m, di_m, inc, d_part, rho_cut,
                           itv["rop"], bit_d_m, rpm, crit=crit)

        # шламовая подушка сужает сечение: считаем поток по остаточной
        # площади через эквивалентный наружный диаметр
        do_eff = do_m
        if hc["bed_frac"] > 1e-6:
            do_eff = math.sqrt(4.0 * hc["A_flow"] / math.pi + di_m ** 2)

        fr = annulus_flow(Q, do_eff, di_m, fluid, ecc, rpm)
        g, V, Re, mode = fr.dpdl, fr.V, fr.Re, fr.mode

        conc = hc["conc"]
        rho_eff = fluid.rho * (1 - conc) + rho_cut * conc
        if CFG.ACCOUNT_CUTTINGS_IN_ECD:
            g = g * (rho_eff / fluid.rho)

        seg = SegResult("затруб", p.name, m0, m1, d_out, d_in, V, Re, mode,
                        g, g * (m1 - m0), tag)
        seg.inc = inc
        seg.ecc = ecc
        seg.rpm = rpm
        seg.A_ann = hc["A_ann"]
        seg.A_flow = hc["A_flow"]
        seg.v_slip = hc["v_slip"]
        seg.v_crit = hc.get("V_crit", 0.0)
        seg.regime = hc["regime"]
        seg.bed_frac = hc["bed_frac"]
        seg.bed_h = hc["bed_h"]
        seg.conc = conc
        seg.rho_eff = rho_eff / 1000.0
        seg.mu_eff = hc["mu_eff"]
        seg.k_ecc = fr.k_ecc
        seg.k_rot = fr.k_rot
        seg.Ta = fr.Ta
        seg.tau_w = fr.tau_w
        ann.append(seg)

    ann.sort(key=lambda s: s.md_top)
    dp_ann = sum(s.dp for s in ann)

    # ------------------------------------------- давления и профили ----
    p_pump = dp_surface + dp_inside + dp_bit + dp_ann

    temps = (getattr(data, "extra", {}) or {}).get("temperature") or []

    def hydrostatic(tvd, nst=24):
        """Гидростатика с учётом сжимаемости и нагрева раствора."""
        if not getattr(CFG, "ACCOUNT_TEMPERATURE", False) or tvd <= 0:
            return fluid.rho * CFG.G * max(tvd, 0.0)
        z, P = 0.0, 0.0
        for i in range(nst):
            z1 = tvd * (i + 1) / nst
            T = temperature_profile(temps, 0.5 * (z + z1))
            rho = density_at(fluid.rho, T, P + 101325.0)
            P += rho * CFG.G * (z1 - z)
            z = z1
        return P

    # эпюра давления в затрубье и ЭЦП
    prof_md, prof_p, prof_ecd, prof_tvd = [0.0], [0.0], [itv["rho"]], [0.0]
    for s in ann:
        tvd = traj.tvd_at(s.md_bot)
        # суммарные потери в затрубье ВЫШЕ рассматриваемой точки
        fric_above = sum(x.dp for x in ann if x.md_bot <= s.md_bot + 1e-6)
        p_abs = hydrostatic(tvd) + fric_above
        ecd = p_abs / (CFG.G * max(tvd, 1e-3)) / 1000.0
        prof_md.append(s.md_bot)
        prof_tvd.append(tvd)
        prof_p.append(p_abs)
        prof_ecd.append(ecd)

    ecd_bottom = prof_ecd[-1] if prof_ecd else itv["rho"]

    # эпюра давления внутри колонны
    in_md, in_p = [0.0], [p_pump - dp_surface]
    acc = p_pump - dp_surface
    for s in inside:
        acc = acc - s.dp + (hydrostatic(traj.tvd_at(s.md_bot)) -
                            hydrostatic(traj.tvd_at(s.md_top)))
        in_md.append(s.md_bot)
        in_p.append(acc)

    # ------------------------------------------------------- насосы ----
    pump = dict(CFG.PUMPS)
    pump.update((getattr(data, "extra", {}) or {}).get("pumps") or {})
    q_one = (pump.get("цилиндров", 3) *
             math.pi * (pump["диаметр_втулки_мм"] * MM) ** 2 / 4.0 *
             (pump["длина_хода_мм"] * MM) * pump["коэффициент_наполнения"])
    spm = Q / max(pump["количество_рабочих"], 1) / q_one * 60.0
    hp = p_pump * Q / 1000.0                     # кВт гидравлическая
    hp_shaft = hp / pump["КПД_насоса"]

    return {
        "itv": itv, "key": key, "section": section, "td": td,
        "is_start": td_override is not None,
        "md_from": md_from, "Q": Q, "q_lps": Q * 1000.0,
        "fluid": fluid, "parts": parts, "bha": bha, "is_template": is_template,
        "inside": inside, "ann": ann,
        "dp_surface": dp_surface, "dp_inside": dp_inside, "dp_bit": dp_bit,
        "dp_ann": dp_ann, "dp_motor": dp_motor, "dp_mwd": dp_mwd,
        "p_pump": p_pump, "bit": bh, "nozzles": nz,
        "prof_md": prof_md, "prof_tvd": prof_tvd, "prof_p": prof_p,
        "prof_ecd": prof_ecd, "ecd_bottom": ecd_bottom,
        "in_md": in_md, "in_p": in_p,
        "spm": spm, "power_kW": hp, "power_shaft_kW": hp_shaft,
        "rho_cut": strat_rho, "pump": pump, "rpm": rpm, "crit": crit,
        "mud_type": (fann or {}).get("тип", ""), "model": fluid.model,
        "openhole": (getattr(data, "extra", {}) or {}).get("openhole") or [],
        "rho_bottom": (hydrostatic(traj.tvd_at(td)) /
                       (CFG.G * max(traj.tvd_at(td), 1e-6)) / 1000.0),
        "T_bottom": temperature_profile(temps, traj.tvd_at(td)),
        "gel": gel_break_pressure(
            (fann or {}).get("снс10мин"), parts, ann),
        "bed_max": max((getattr(x, "bed_frac", 0) for x in ann), default=0),
        "inc_max": max((getattr(x, "inc", 0) for x in ann), default=0),
        "surface_list": surf_list, "motor_cfg": motor_cfg, "mwd_cfg": mwd_cfg,
        "window": _window(data, traj, 0.0, td),
        "load_pct": p_pump / (pump["макс_давление_МПа"] * 1e6) * 100.0,
    }


def _window(data, traj, md_from, md_to):
    """
    Поровое давление и давление гидроразрыва в интервале, приведённые
    к эквивалентной плотности. Возвращает списки по MD.
    """
    ex = getattr(data, "extra", {}) or {}
    pr_md = ex.get("pressure_md") or []
    pr = ex.get("pressure") or []
    if not pr_md and not pr:
        return None

    out = {"md": [], "pore": [], "frac": [], "loss": []}
    step = max((md_to - md_from) / 60.0, 1.0)
    md = md_from
    while md <= md_to + 1e-6:
        out["md"].append(md)
        if pr_md:
            # давления заданы по пачкам разреза - ступенчатая функция по MD
            band = next((b for b in pr_md
                         if b["md_from"] - 1e-6 <= md <= b["md_to"] + 1e-6),
                        None)
            if band is None:
                band = min(pr_md, key=lambda b: min(abs(md - b["md_from"]),
                                                    abs(md - b["md_to"])))
            for k in ("pore", "frac", "loss"):
                out[k].append(band.get(k))
        else:
            tvd = traj.tvd_at(md)
            for k in ("pore", "frac", "loss"):
                xs = [(d["tvd"], d[k]) for d in pr if d.get(k) is not None]
                out[k].append(np.interp(tvd, [x[0] for x in xs],
                                        [x[1] for x in xs]) if len(xs) >= 2
                              else (xs[0][1] if xs else None))
        md += step
    if all(v is None for v in out["pore"]) and all(v is None for v in out["frac"]):
        return None
    return out


def _bladed_equivalent(d_hole, d_blade):
    """
    Эквивалентный наружный диаметр тела для калибратора или центратора.
    Свободная площадь: кольцо между стволом и корпусом за вычетом
    площади, занятой лопастями.
    """
    cov = getattr(CFG, "BLADE_COVERAGE", 0.35)
    k_body = getattr(CFG, "BODY_TO_BLADE", 0.62)
    d_body = min(d_blade * k_body, d_hole * 0.95)
    A = math.pi / 4.0
    a_free = (A * (d_hole ** 2 - d_body ** 2)
              - cov * A * (d_blade ** 2 - d_body ** 2))
    a_free = max(a_free, A * (d_hole ** 2 - d_blade ** 2) * 1.05, 1e-6)
    d_eq = math.sqrt(max(d_hole ** 2 - 4.0 * a_free / math.pi, 1e-9))
    return min(max(d_eq, d_body), d_blade)


def _tooljoint_factor(Q, dp_info, fluid):
    """
    Поправка на замковые соединения внутри бурильной колонны.
    Если геометрия замка задана, потери считаются по фактическим длинам
    тела трубы и замка; иначе берётся общий коэффициент из конфигурации.
    """
    tj_id = (dp_info or {}).get("tj_id_mm")
    body_id = (dp_info or {}).get("id_mm")
    if not tj_id or not body_id or tj_id >= body_id:
        return CFG.TOOLJOINT_FACTOR
    L_tj = (dp_info.get("tj_len_m") or 0.5)
    L_j = (dp_info.get("joint_len_m") or 9.5)
    g_body = pipe_flow(Q, body_id * MM, fluid).dpdl
    g_tj = pipe_flow(Q, tj_id * MM, fluid).dpdl
    if g_body <= 0:
        return CFG.TOOLJOINT_FACTOR
    return ((g_body * (L_j - L_tj) + g_tj * L_tj) / L_j) / g_body


def _part_at(parts, md):
    for p in parts:
        if p.md_top - 1e-6 <= md <= p.md_bot + 1e-6:
            return p
    return parts[-1] if parts else None


def _strat_density(data: InputData, md_from, md_to):
    """Средневзвешенная плотность породы в интервале, г/см3."""
    if not data.strat:
        return CFG.DEFAULT_CUTTINGS_DENSITY
    tot_len, tot = 0.0, 0.0
    for s in data.strat:
        a = max(s["от"], md_from)
        b = min(s["до"], md_to)
        if b > a:
            tot_len += (b - a)
            tot += (b - a) * s["ро"]
    if tot_len <= 0:
        return CFG.DEFAULT_CUTTINGS_DENSITY
    return tot / tot_len


# ==========================================================================
#  4. АНАЛИЗ ПО РАСХОДУ
# ==========================================================================

def sweep_flow(itv, data, traj, npts=None):
    npts = npts or CFG.Q_SWEEP_POINTS
    q0 = itv["q_lps"]
    qs = np.linspace(q0 * CFG.Q_SWEEP_MIN_FRAC, q0 * CFG.Q_SWEEP_MAX_FRAC, npts)
    out = {"q": [], "p": [], "ecd": [], "hsi": [], "vann": [], "dpbit": []}
    for q in qs:
        r = calc_interval(itv, data, traj, q_lps=q, quiet=True)
        if r is None:
            continue
        out["q"].append(q)
        out["p"].append(r["p_pump"])          # Па
        out["ecd"].append(r["ecd_bottom"])
        out["hsi"].append(r["bit"]["hsi_kW_cm2"])
        out["dpbit"].append(r["dp_bit"])      # Па
        out["vann"].append(max((s.V for s in r["ann"]), default=0))
    return out


# ==========================================================================
#  5. ОЦЕНКА РЕЗУЛЬТАТА
# ==========================================================================

def assess(res):
    """Список (параметр, значение, критерий, статус)."""
    rows = []
    c = res.get("crit") or CFG.CRIT
    itv = res["itv"]

    ann = res["ann"]
    v_min = min((s.V for s in ann), default=0)
    long_seg = [s for s in ann if (s.md_bot - s.md_top) >= 5.0]
    v_max = max((s.V for s in (long_seg or ann)), default=0)
    inc_max = max((getattr(s, "inc", 0) for s in ann), default=0)
    v_req = c["Vкц_мин_наклон_мс"] if inc_max > 30 else c["Vкц_мин_верт_мс"]

    rows.append((t("k_vmin"), f"{v_min:.2f} " + t("u_ms"),
                 f"≥ {v_req:.2f}", "ok" if v_min >= v_req else "bad"))
    rows.append((t("k_vmax"), f"{v_max:.2f} " + t("u_ms"),
                 f"≤ {c['Vкц_макс_мс']:.2f}",
                 "ok" if v_max <= c["Vкц_макс_мс"] else "warn"))

    conc = max((getattr(s, "conc", 0) for s in ann), default=0) * 100
    rows.append((t("k_conc"), f"{conc:.2f} %",
                 f"≤ {c['Cшлам_макс_%']:.1f}",
                 "ok" if conc <= c["Cшлам_макс_%"] else "bad"))

    # запас считается ПОУЧАСТКОВО: минимум скорости и максимум требуемой
    # обычно приходятся на разные глубины
    marg = [(s.V - getattr(s, "v_crit", 0.0), s) for s in ann]
    m_val, m_seg = min(marg, key=lambda t: t[0]) if marg else (0.0, None)
    rows.append((t("k_margin"), f"{m_val:+.2f} " + t("u_ms"),
                 t("k_at", a=f"{m_seg.md_top:.0f}", b=f"{m_seg.md_bot:.0f}")
                 if m_seg else "> 0",
                 "ok" if m_val >= 0 else "bad"))

    bed = res.get("bed_max", 0.0) * 100
    lim_bed = c.get("Подушка_макс_доля", 0.10) * 100
    rows.append((t("k_bed"), f"{bed:.1f} " + t("of_hole"),
                 f"≤ {lim_bed:.0f} %",
                 "ok" if bed <= lim_bed else "bad"))

    hsi = res["bit"]["hsi_kW_cm2"]
    rows.append((t("k_hsi"), f"{hsi:.3f} " + t("u_kwcm2"),
                 f"≥ {c['HSI_мин_кВт_см2']:.3f}",
                 "ok" if hsi >= c["HSI_мин_кВт_см2"] else "warn"))

    ecd = res["ecd_bottom"]
    dro = ecd - itv["rho"]
    rows.append((t("k_ecd"), f"{ecd:.3f} " + t("u_gcm3"),
                 f"≤ ρ+{c['ЭЦП_запас_гсм3']:.2f} = "
                 f"{itv['rho'] + c['ЭЦП_запас_гсм3']:.2f}",
                 "ok" if dro <= c["ЭЦП_запас_гсм3"] else "bad"))

    load = res["load_pct"]
    rows.append((t("k_load"), f"{load:.1f} %",
                 f"≤ {c['Загрузка_насоса_%']:.0f}",
                 "ok" if load <= c["Загрузка_насоса_%"] else "bad"))

    pump = res.get("pump", CFG.PUMPS)
    spm = res["spm"]
    rows.append((t("k_spm"), f"{spm:.0f} " + t("u_spm"),
                 f"≤ {pump['макс_ходов_в_мин']:.0f}",
                 "ok" if spm <= pump["макс_ходов_в_мин"] else "bad"))

    share = res["dp_bit"] / max(res["p_pump"], 1) * 100
    rows.append((t("k_share"), f"{share:.1f} %", "45…65 %",
                 "ok" if 45 <= share <= 65 else "warn"))

    w = res.get("window")
    if w:
        fr = [v for v in w["frac"] if v is not None]
        po = [v for v in w["pore"] if v is not None]
        if fr:
            zap = min(fr) - ecd
            rows.append((t("k_frac"), f"{zap:+.3f} " + t("u_gcm3"),
                         "> 0", "ok" if zap > 0.02 else "bad"))
        if po:
            zap2 = itv["rho"] - max(po)
            rows.append((t("k_pore"), f"{zap2:+.3f} " + t("u_gcm3"),
                         "> 0", "ok" if zap2 > 0 else "bad"))
    return rows
