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
 ЧТЕНИЕ ШАБЛОНА NTS-HYDRA
==========================================================================
 Читает файл «NTS-HYDRA_исходные_данные_ШАБЛОН.xlsx» и совместимые с ним.
 Каждый лист необязателен: чего нет - берётся из hydraulics_config.py.
==========================================================================
"""

import re

import pandas as pd

import hydraulics_config as CFG

# логическое имя -> варианты названий листа (регистр не важен)
# Названия листов на трёх языках: шаблон может быть переведён, структура
# столбцов при этом не меняется.
SHEETS = {
    "general":   ["01 Общие сведения", "Общие сведения",
                  "01 General", "General",
                  "01 Informations generales", "Informations generales"],
    "casing":    ["02 Конструкция", "Конструкция скважины",
                  "02 Casing", "Casing", "02 Tubages", "Tubages"],
    "survey":    ["03 Инклинометрия", "Инклинометрия", "Профиль скважины",
                  "03 Survey", "Survey", "03 Deviation", "Deviation"],
    "strat":     ["04 Разрез и давления", "Стратиграфия",
                  "04 Geology and pressures", "Geology",
                  "04 Geologie et pressions", "Geologie"],
    "intervals": ["05 Интервалы бурения", "Долотная программа",
                  "05 Intervals", "Intervals",
                  "05 Intervalles", "Intervalles"],
    "mud":       ["06 Буровой раствор", "Реология",
                  "Параметры бурового раствора",
                  "06 Drilling fluid", "Drilling fluid",
                  "06 Boue de forage", "Boue de forage"],
    "nozzles":   ["07 Насадки долот", "Насадки долот",
                  "07 Bit nozzles", "Bit nozzles",
                  "07 Duses", "Duses"],
    "motor":     ["08 ВЗД", "ВЗД", "08 Mud motor", "Mud motor",
                  "08 Moteur de fond", "Moteur de fond"],
    "mwd":       ["09 Телесистема", "Телесистема", "09 MWD", "MWD"],
    "bha":       ["10 КНБК", "10 BHA", "BHA",
                  "10 Garniture de fond", "Garniture de fond"],
    "drillpipe": ["11 Бурильная колонна", "Бурильная колонна",
                  "11 Drill string", "Drill string",
                  "11 Garniture de forage", "Garniture de forage"],
    "pumps":     ["12 Буровые насосы", "Буровые насосы",
                  "12 Mud pumps", "Mud pumps",
                  "12 Pompes a boue", "Pompes a boue"],
    "surface":   ["13 Наземная обвязка", "Наземная обвязка",
                  "13 Surface equipment", "Surface equipment",
                  "13 Equipement de surface", "Equipement de surface"],
    "cuttings":  ["14 Шлам", "Шлам и очистка ствола",
                  "14 Cuttings", "Cuttings", "14 Deblais", "Deblais"],
    "temp":      ["15 Температура", "Температура",
                  "15 Temperature", "Temperature"],
}

# первая ячейка шапки таблицы на трёх языках
HEADER_ALIASES = {
    "Интервал": ("Интервал", "Interval", "Intervalle"),
    "Колонна": ("Колонна", "Casing", "Tubage"),
    "Показатель": ("Показатель", "Item", "Rubrique"),
    "Параметр": ("Параметр", "Parameter", "Parametre"),
    "Элемент": ("Элемент", "Element", "Element"),
    "Свита": ("Свита", "Formation", "Formation"),
    "Глубина": ("Глубина", "Depth", "Profondeur"),
    "MD": ("MD", "MD", "MD"),
}

NO_MOTOR = {"нет", "не применяется", "без взд", "роторное бурение",
            "не используется", "отсутствует",
            "no", "none", "not used", "not applicable", "n/a - none",
            "non", "aucun", "sans moteur", "non utilise"}


def is_template(sheetnames):
    """
    Признак шаблона NTS-HYDRA: несколько листов с номерными префиксами
    и обязательный лист интервалов бурения.
    """
    numbered = sum(1 for n in sheetnames if re.match(r"^\s*\d{2}\s", str(n)))
    want = {re.sub(r"^\s*\d+\s*", "", w).strip().lower()
            for w in SHEETS["intervals"]}
    has_iv = any(re.sub(r"^\s*\d+\s*", "", str(n)).strip().lower() in want
                 for n in sheetnames)
    return numbered >= 5 and has_iv


def find_sheet(sheetnames, key):
    """Находит лист по логическому имени с учётом номерных префиксов."""
    want = SHEETS.get(key, [])
    low = {n.strip().lower(): n for n in sheetnames}
    for w in want:
        if w.lower() in low:
            return low[w.lower()]
    # мягкий поиск: совпадение по «хвосту» после номера
    for w in want:
        tail = re.sub(r"^\d+\s*", "", w).lower()
        for n_low, n in low.items():
            if re.sub(r"^\d+\s*", "", n_low) == tail:
                return n
    return None


def rows(path, sheetnames, key, hdr_first=None, ncols=None):
    """
    Строки данных листа. Ищется строка заголовка (по первой ячейке),
    после неё идут данные. Строка «ПРИМЕР» и всё ниже отбрасывается.
    """
    name = find_sheet(sheetnames, key)
    if name is None:
        return []
    try:
        df = pd.read_excel(path, sheet_name=name, header=None)
    except Exception:
        return []
    raw = df.values.tolist()

    variants = [hdr_first] if hdr_first else []
    variants += list(HEADER_ALIASES.get(hdr_first, ()))
    variants = [v.lower() for v in variants if v]

    start = None
    for i, v in enumerate(raw):
        first = "" if not v else str(v[0]).strip().lower()
        if any(first.startswith(w) for w in variants):
            start = i + 1
            break
    if start is None:
        start = 4

    out = []
    for v in raw[start:]:
        first = "" if not v else str(v[0]).strip()
        if first.upper().startswith("ПРИМЕР"):
            break
        if ncols:
            v = list(v) + [None] * max(0, ncols - len(v))
        out.append(list(v))
    return out


MODEL_ALIASES = {
    "herschel": "herschel_bulkley", "power law": "power_law",
    "power-law": "power_law", "bingham": "bingham",
    "loi de puissance": "power_law", "auto": "auto", "automatic": "auto",
    "automatique": "auto",
    "гершеля-балкли": "herschel_bulkley", "гершель-балкли": "herschel_bulkley",
    "гершеля-балкли": "herschel_bulkley", "herschel": "herschel_bulkley",
    "hb": "herschel_bulkley", "гб": "herschel_bulkley",
    "степенная": "power_law", "степенной": "power_law",
    "power": "power_law", "оствальда": "power_law", "пл": "power_law",
    "бингама": "bingham", "бингам": "bingham", "bingham": "bingham",
    "пластическая": "bingham", "бп": "bingham",
    "авто": "auto", "автоматически": "auto",
}


def _cell_text(v):
    """Текст ячейки. Даты выводятся без времени."""
    import datetime as _dt
    if isinstance(v, (_dt.datetime, _dt.date)):
        return v.strftime("%d.%m.%Y")
    t = str(v).strip()
    # дата, прочитанная как строка вида 2026-09-11 00:00:00
    if len(t) >= 19 and t[4] == "-" and t.endswith("00:00:00"):
        try:
            return _dt.datetime.strptime(t[:10], "%Y-%m-%d").strftime(
                "%d.%m.%Y")
        except ValueError:
            pass
    return t


def _rheology_model(v):
    """Название модели реологии из ячейки -> внутренний код."""
    from hydraulics_core import is_no_data
    if is_no_data(v):
        return None
    t = " ".join(str(v).strip().lower().split())
    for k, m in MODEL_ALIASES.items():
        if t.startswith(k):
            return m
    return None


def _clean(rws, col=0):
    """Убирает строки, у которых пустая опорная ячейка."""
    from hydraulics_core import is_no_data
    return [r for r in rws if not is_no_data(r[col])]


def read_template(path, sheetnames):
    """Основная функция: возвращает словарь со всеми данными шаблона."""
    from hydraulics_core import to_float, parse_range, is_no_data

    ex = {"_gaps": [], "_found": []}
    gaps = ex["_gaps"]

    def mark(sheet, key, what):
        gaps.append((sheet, key, what))

    def found(name, data):
        if data:
            ex["_found"].append(name)

    # ------------------------------------------------- общие сведения ----
    gen = {}
    for v in _clean(rows(path, sheetnames, "general", "Показатель")):
        if is_no_data(v[1] if len(v) > 1 else None):
            continue
        gen[str(v[0]).strip().rstrip(":").lower()] = _cell_text(v[1])
    ex["general"] = gen
    found("Общие сведения", gen)

    # ---------------------------------------------------- конструкция ----
    casings, openhole = [], []
    for v in _clean(rows(path, sheetnames, "casing", "Колонна", 7)):
        name = str(v[0]).strip()
        od, wall, md = to_float(v[1]), to_float(v[2]), to_float(v[3])
        if not (od and md):
            continue
        low = name.lower()
        # строка «открытый ствол» описывает незакреплённый интервал,
        # а не обсадную колонну: толщина стенки у неё отсутствует
        if ("открыт" in low or "без креплен" in low or "необсажен" in low
                or wall in (None, 0)):
            openhole.append({
                "name": name, "d_mm": od, "md_to": md,
                "tvd_to": to_float(v[4]) or md,
                "note": str(v[6]) if len(v) > 6 and not is_no_data(v[6])
                else "",
            })
            continue
        casings.append({
            "name": name, "od_mm": od, "wall_mm": wall,
            "md_m": md, "tvd_m": to_float(v[4]) or md,
            "top_m": to_float(v[5]),
        })
    casings.sort(key=lambda c: c["md_m"])
    ex["casings"] = casings
    ex["openhole"] = openhole
    found("Конструкция", casings)

    # -------------------------------------------------- инклинометрия ----
    sv = []
    for v in _clean(rows(path, sheetnames, "survey", "MD", 5)):
        md, inc = to_float(v[0]), to_float(v[1])
        if md is None or inc is None:
            continue
        sv.append((md, inc, to_float(v[3])))
    sv.sort(key=lambda t: t[0])
    ex["survey"] = sv
    found("Инклинометрия", sv)

    # ------------------------------------------- разрез и давления -------
    strat, press = [], []
    for v in _clean(rows(path, sheetnames, "strat", "Свита", 9)):
        a, b = to_float(v[1]), to_float(v[2])
        if a is None or b is None:
            continue
        strat.append({"название": str(v[0]).strip(), "от": a, "до": b,
                      "литология": str(v[3]) if not is_no_data(v[3]) else "",
                      "ро": to_float(v[4]) or CFG.DEFAULT_CUTTINGS_DENSITY})
        po, fr, ls = to_float(v[5]), to_float(v[6]), to_float(v[7])
        if any(x is not None for x in (po, fr, ls)):
            press.append({"md_from": a, "md_to": b, "pore": po,
                          "frac": fr, "loss": ls,
                          "strat": str(v[0]).strip()})
    ex["strat"] = strat
    ex["pressure_md"] = press
    found("Разрез и давления", strat)

    # ------------------------------------------------------ интервалы ----
    intervals = []
    for v in _clean(rows(path, sheetnames, "intervals", "Интервал", 12)):
        key = str(v[0]).strip()
        a, b = to_float(v[1]), to_float(v[2])
        if a is None or b is None:
            continue
        intervals.append({
            "key": key, "md_from": a, "md_to": b,
            "bit_mm": to_float(v[3]), "bit_type": str(v[4] or "").strip(),
            "drive": str(v[5] or "").strip(),
            "q_raw": v[6], "q_lps": parse_range(v[6], CFG.FLOW_CHOICE),
            "rop": to_float(v[7]), "caving": to_float(v[8]),
            "rpm": to_float(v[9]),
        })
        if intervals[-1]["bit_mm"] is None:
            mark("05 Интервалы бурения", key, "диаметр долота")
        if intervals[-1]["q_lps"] is None:
            mark("05 Интервалы бурения", key, "расход")
    ex["intervals"] = intervals
    found("Интервалы бурения", intervals)

    # -------------------------------------------------- буровой раствор --
    mud = {}
    for v in _clean(rows(path, sheetnames, "mud", "Интервал", 16)):
        key = str(v[0]).strip()
        f = {"тип": str(v[1] or "").strip(), "rho": to_float(v[2]),
             "t600": to_float(v[3]), "t300": to_float(v[4]),
             "t200": to_float(v[5]), "t100": to_float(v[6]),
             "t6": to_float(v[7]), "t3": to_float(v[8]),
             "снс10с": to_float(v[9]), "снс10мин": to_float(v[10]),
             "t_degc": to_float(v[11]), "водоотдача": to_float(v[12]),
             "pv": to_float(v[13]), "yp": to_float(v[14]),
             "модель": _rheology_model(v[15] if len(v) > 15 else None)}
        if f["rho"] is None:
            mark("06 Буровой раствор", key, "плотность")
        if not (f["t600"] and f["t300"]) and not (f["pv"] and f["yp"]):
            mark("06 Буровой раствор", key,
                 "реология (ни показания вискозиметра, ни ПВ с ДНС)")
        if f["rho"] or f["t600"] or f["pv"]:
            mud[key] = f
    ex["mud"] = mud
    found("Буровой раствор", mud)

    # --------------------------------------------------------- насадки ---
    nz = {}
    for v in _clean(rows(path, sheetnames, "nozzles", "Интервал", 11)):
        key = str(v[0]).strip()
        d = [to_float(x) for x in v[1:9]]
        d = [x for x in d if x and x > 0]
        if d:
            nz[key] = d
        else:
            tfa = to_float(v[9])
            if tfa and tfa > 0:
                nz[key] = {"tfa_in2": tfa}
            else:
                mark("07 Насадки долот", key, "диаметры насадок / TFA")
    ex["nozzles"] = nz
    found("Насадки долот", nz)

    # ------------------------------------------------------------- ВЗД ---
    mt = {}
    for v in _clean(rows(path, sheetnames, "motor", "Интервал", 12)):
        key = str(v[0]).strip()
        name = str(v[1] or "").strip()
        if name.lower() in NO_MOTOR:
            mt[key] = None
            continue
        if is_no_data(name):
            mark("08 ВЗД", key, "типоразмер")
            continue
        q = to_float(v[5]) or to_float(v[4])
        dxx, dld = to_float(v[6]), to_float(v[7])
        if q and dxx is not None:
            mt[key] = {"имя": name, "q_ref_лс": q,
                       "dp_xx_atm": dxx, "dp_load_atm": dld or 0.0,
                       "od_mm": to_float(v[2]), "id_mm": to_float(v[3]),
                       "момент": to_float(v[8]), "обороты": to_float(v[9]),
                       "перекос": to_float(v[10])}
        else:
            mark("08 ВЗД", key, "расход или перепад давления")
    ATM = 0.0980665     # МПа в одной технической атмосфере
    for k, v in mt.items():
        if v:
            v["dp_xx_МПа"] = v.pop("dp_xx_atm") * ATM
            v["dp_load_МПа"] = v.pop("dp_load_atm") * ATM
    ex["motor"] = mt
    found("ВЗД", mt)

    # ------------------------------------------------------ телесистема --
    mw = {}
    for v in _clean(rows(path, sheetnames, "mwd", "Интервал", 8)):
        key = str(v[0]).strip()
        name = str(v[1] or "").strip()
        if name.lower() in NO_MOTOR or name.lower() == "нет":
            mw[key] = None
            continue
        if is_no_data(name):
            mark("09 Телесистема", key, "тип")
            continue
        q, dp = to_float(v[4]), to_float(v[5])
        if q and dp is not None:
            mw[key] = {"имя": name, "q_ref_лс": q, "dp_atm": dp}
        else:
            mark("09 Телесистема", key, "расход или перепад давления")
    for k, v in mw.items():
        if v:
            v["dp_МПа"] = v.pop("dp_atm") * ATM
    ex["mwd"] = mw
    found("Телесистема", mw)

    # ------------------------------------------------------------ КНБК ---
    bha = {}
    cur = None
    for v in rows(path, sheetnames, "bha", "Интервал", 6):
        sec = str(v[0]).strip() if not is_no_data(v[0]) else None
        name = str(v[1]).strip() if not is_no_data(v[1]) else None
        if sec:
            cur = sec
            bha.setdefault(cur, [])
        if not name or cur is None:
            continue
        if name.startswith("↑"):
            continue
        od = to_float(v[3])
        if od is None:
            continue
        bha.setdefault(cur, []).append({
            "name": name, "length_m": to_float(v[2]) or 0.0,
            "od_mm": od, "id_mm": to_float(v[4]),
            "note": str(v[5]) if len(v) > 5 and not is_no_data(v[5]) else "",
        })
    bha = {k: v for k, v in bha.items() if v}
    ex["bha"] = bha
    found("КНБК", bha)

    # --------------------------------------------- бурильная колонна -----
    dp = {}
    for v in _clean(rows(path, sheetnames, "drillpipe", "Интервал", 7)):
        key = str(v[0]).strip()
        od, idd = to_float(v[2]), to_float(v[3])
        if od and idd:
            dp[key] = {"имя": str(v[1] or "СБТ").strip(),
                       "od_mm": od, "id_mm": idd,
                       "tj_od_mm": to_float(v[4]),
                       "tj_id_mm": to_float(v[5]),
                       "tj_len_m": 0.5, "joint_len_m": 9.5}
        else:
            mark("11 Бурильная колонна", key, "диаметры труб")
    ex["drillpipe"] = dp
    found("Бурильная колонна", dp)

    # ---------------------------------------------------------- насосы ---
    pumps = {}
    MAP = {
        "тип насоса": "тип",
        "количество насосов": "количество_рабочих",
        "число цилиндров": "цилиндров",
        "диаметр втулки": "диаметр_втулки_мм",
        "длина хода": "длина_хода_мм",
        "коэффициент наполнения": "коэффициент_наполнения",
        "максимальное число ходов": "макс_ходов_в_мин",
        "максимальное давление насоса": "_p_pump_atm",
        "максимальное давление обвязки": "_p_line_atm",
        "мощность одного насоса": "мощность_на_насос_кВт",
        "кпд насоса": "КПД_насоса",
    }
    for v in _clean(rows(path, sheetnames, "pumps", "Параметр", 4)):
        label = str(v[0]).strip().lower()
        val = v[1] if len(v) > 1 else None
        for pat, field in MAP.items():
            if label.startswith(pat):
                if field == "тип":
                    if not is_no_data(val):
                        pumps[field] = str(val).strip()
                else:
                    fv = to_float(val)
                    if fv is not None:
                        pumps[field] = fv
                break
    if "_p_pump_atm" in pumps or "_p_line_atm" in pumps:
        vals = [pumps.pop(k) for k in ("_p_pump_atm", "_p_line_atm")
                if k in pumps]
        pumps["макс_давление_МПа"] = min(vals) * ATM
    ex["pumps"] = pumps
    found("Буровые насосы", pumps)

    # ------------------------------------------------ наземная обвязка ---
    surf = []
    for v in _clean(rows(path, sheetnames, "surface", "Элемент", 4)):
        L, d = to_float(v[1]), to_float(v[2])
        if L and d:
            surf.append((str(v[0]).strip(), L, d))
    ex["surface"] = surf
    found("Наземная обвязка", surf)

    # ------------------------------------------------------------ шлам ---
    ct = {}
    for v in _clean(rows(path, sheetnames, "cuttings", "Интервал", 5)):
        key = str(v[0]).strip()
        row = {"d_mm": to_float(v[1]), "c_max": to_float(v[2]),
               "v_min": to_float(v[3])}
        if any(x is not None for x in row.values()):
            ct[key] = row
    ex["cuttings"] = ct
    found("Шлам", ct)

    # ----------------------------------------------------- температура ---
    tp = []
    for v in _clean(rows(path, sheetnames, "temp", "Глубина", 4)):
        tvd, t = to_float(v[0]), to_float(v[1])
        if tvd is not None and t is not None:
            tp.append((tvd, t))
    ex["temperature"] = sorted(tp)
    found("Температура", tp)

    return ex


def resolve(ex, group, key, section, cfg_dict, default=None):
    """Значение: сначала Excel (по интервалу, затем по секции), потом конфиг."""
    src = (ex or {}).get(group, {})
    if isinstance(src, dict):
        if key in src:
            return src[key], "Excel"
        if section in src:
            return src[section], "Excel"
    if cfg_dict is not None:
        if key in cfg_dict:
            return cfg_dict[key], "конфиг"
        if section in cfg_dict:
            return cfg_dict[section], "конфиг"
    return default, "по умолчанию"
