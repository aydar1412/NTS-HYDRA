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
 ВАЛИДАЦИЯ РАСЧЁТНОГО ЯДРА NTS-HYDRA
==========================================================================
 Запуск:  python tests_validation.py
 Тесты проверяют физику, а не совпадение с прошлым результатом:

  1. Предельные переходы. При n=1 и tau0=0 степенная и Гершель-Балкли
     обязаны сойтись к аналитическим решениям Пуазейля (труба) и
     плоской щели (затрубье).
  2. Согласованность моделей между собой в общих предельных случаях.
  3. Независимая проверка через промысловые формулы в других единицах:
     если СИ-расчёт и формула в фунтах/галлонах дают одно и то же -
     ошибки в коэффициентах и переводах исключены.
  4. Балансы: сумма потерь по участкам равна общей, ЭЦП при нулевом
     расходе равна плотности раствора.
  5. Монотонность и физичность: потери растут с расходом, скорость
     осаждения растёт с размером частицы и т.д.
==========================================================================
"""

import math
import sys
import traceback

import numpy as np

import hydraulics_config as CFG
from hydraulics_lang import t as _t
from hydraulics_core import (
    Fluid, pipe_pressure_gradient, annulus_pressure_gradient,
    bingham_pipe_gradient, bingham_annulus_gradient,
    bit_hydraulics, nozzle_area, slip_velocity, _friction_factor,
)
from hydraulics_rheology import (
    Rheology, DIAL_TO_PA, SHEAR, pipe_flow, annulus_flow,
    eccentricity_factor, eccentricity_at, rotation_effect,
)
from hydraulics_holecleaning import (
    hole_cleaning, critical_velocity, bed_area, equilibrium_bed,
)

PASS, FAIL = [], []


def check(name, got, want, rel=0.02, note=""):
    """Сравнение с относительным допуском."""
    if want == 0:
        ok = abs(got) < 1e-9
        err = abs(got)
    else:
        err = abs(got - want) / abs(want)
        ok = err <= rel
    line = (f"{name:<58s} расчёт={got:>12.5g}  эталон={want:>12.5g}  "
            f"расхожд.={err * 100:5.2f}%")
    if note:
        line += f"   [{note}]"
    (PASS if ok else FAIL).append(line)
    return ok


def check_true(name, cond, note=""):
    line = f"{name:<58s} {'да' if cond else 'НЕТ'}"
    if note:
        line += f"   [{note}]"
    (PASS if cond else FAIL).append(line)
    return cond


# ==========================================================================
#  1. ПРЕДЕЛЬНЫЕ ПЕРЕХОДЫ К НЬЮТОНОВСКОЙ ЖИДКОСТИ
# ==========================================================================

def newtonian_fluid(mu_pas=0.030, rho=1200.0):
    """
    Жидкость, на которой все модели обязаны выродиться в ньютоновскую.
    Показания шкалы строятся из констант вискозиметра Fann 35:
        gamma = 1,7023 * об/мин,  tau[Па] = 0,511266 * показание.
    """
    d = {f"t{r}": mu_pas * SHEAR[r] / DIAL_TO_PA
         for r in (600, 300, 200, 100, 6, 3)}
    return Fluid(rho / 1000.0, fann=d), mu_pas


def test_poiseuille():
    """Ламинарное течение в трубе: dP/dL = 32*mu*V/D^2."""
    f, mu = newtonian_fluid()
    D, Q = 0.1086, 0.004                       # 108,6 мм; 4 л/с
    V = Q / (math.pi * D ** 2 / 4)
    want = 32.0 * mu * V / D ** 2
    got, V2, Re, mode = pipe_pressure_gradient(Q, D, f)
    check("Труба, ламинарный: закон Пуазейля", got, want, 0.01)
    check("Труба: средняя скорость", V2, V, 1e-6)
    check("Труба: число Рейнольдса = rho*V*D/mu",
          Re, f.rho * V * D / mu, 0.01)
    check_true("Труба: режим определён как ламинарный",
               mode == _t("fl_laminar"), f"Re={Re:.0f}")


def test_slot():
    """Ламинарное течение в щели (затрубье): dP/dL = 48*mu*V/Dh^2."""
    f, mu = newtonian_fluid()
    do, di, Q = 0.2159, 0.127, 0.004
    A = math.pi * (do ** 2 - di ** 2) / 4
    V = Q / A
    dh = do - di
    want = 48.0 * mu * V / dh ** 2
    got, V2, Re, mode = annulus_pressure_gradient(Q, do, di, f)
    check("Затрубье, ламинарный: решение для щели", got, want, 0.01)
    check("Затрубье: средняя скорость", V2, V, 1e-6)
    check_true("Затрубье: режим определён как ламинарный",
               mode == _t("fl_laminar"), f"Re={Re:.0f}")


def test_bingham_limit():
    """При tau0 -> 0 модель Бингама должна совпасть с ньютоновской."""
    f = Fluid(1.20, 30.0, 0.0, model="bingham")   # PV=30 сПз, ДНС=0
    mu = 0.030
    D, Q = 0.1086, 0.004
    V = Q / (math.pi * D ** 2 / 4)
    got, _, _, _ = bingham_pipe_gradient(Q, D, f)
    check("Бингам при ДНС=0 -> Пуазейль (труба)",
          got, 32.0 * mu * V / D ** 2, 0.01)

    do, di = 0.2159, 0.127
    V = Q / (math.pi * (do ** 2 - di ** 2) / 4)
    got, _, _, _ = bingham_annulus_gradient(Q, do, di, f)
    check("Бингам при ДНС=0 -> решение для щели (затрубье)",
          got, 48.0 * mu * V / (do - di) ** 2, 0.01)


def test_powerlaw_vs_bingham():
    """
    Для ньютоновской жидкости обе модели обязаны дать один результат.
    Это перекрёстная проверка независимых веток кода.
    """
    f, mu = newtonian_fluid()
    D, Q = 0.1086, 0.004
    a, _, _, _ = pipe_pressure_gradient(Q, D, f)
    b, _, _, _ = bingham_pipe_gradient(Q, D, f)
    check("Степенная и Бингама совпадают на ньютоновской жидкости",
          a, b, 0.02)


# ==========================================================================
#  2. ПРОВЕРКА ЧЕРЕЗ ПРОМЫСЛОВЫЕ ФОРМУЛЫ (ДРУГИЕ ЕДИНИЦЫ)
# ==========================================================================

def test_bit_nozzles_field_units():
    """
    Промысловая формула:  dP[psi] = rho[ppg] * Q[gpm]^2 / (12031 * Cd^2 * A[in2]^2)
    Расчёт в СИ обязан дать то же число после перевода единиц.
    """
    rho_ppg, q_gpm, nozzles = 10.0, 600.0, [16, 16, 16]
    A_in2 = sum(math.pi / 4 * (d / 32) ** 2 for d in nozzles)
    want_psi = rho_ppg * q_gpm ** 2 / (12031.0 * CFG.CD_NOZZLE ** 2 * A_in2 ** 2)

    rho_si = rho_ppg * 119.826
    q_si = q_gpm * 6.30902e-5
    bh = bit_hydraulics(q_si, nozzles, rho_si, 0.2159)
    got_psi = bh["dp_Pa"] / 6894.757
    check("Долото: перепад на насадках (сверка с формулой в psi)",
          got_psi, want_psi, 0.01)
    check("Долото: TFA", bh["tfa_in2"], A_in2, 1e-6)


def test_hydraulic_power_field_units():
    """Промысловая формула: HHP = dP[psi] * Q[gpm] / 1714."""
    dp_psi, q_gpm = 1200.0, 600.0
    want_hp = dp_psi * q_gpm / 1714.0
    dp_pa, q_si = dp_psi * 6894.757, q_gpm * 6.30902e-5
    got_hp = dp_pa * q_si / 745.7
    check("Гидравлическая мощность (сверка с формулой в л.с.)",
          got_hp, want_hp, 0.005)


def test_annular_velocity_field_units():
    """Промысловая формула: V[ft/min] = 24.5 * Q[gpm] / (D^2 - d^2)[in2]."""
    q_gpm, D_in, d_in = 600.0, 8.5, 5.0
    want_fpm = 24.5 * q_gpm / (D_in ** 2 - d_in ** 2)
    q_si = q_gpm * 6.30902e-5
    A = math.pi / 4 * ((D_in * 0.0254) ** 2 - (d_in * 0.0254) ** 2)
    got_fpm = q_si / A / 0.3048 * 60.0
    check("Скорость в затрубье (сверка с формулой в фут/мин)",
          got_fpm, want_fpm, 0.01)


def test_hsi_units():
    """HSI: 1 л.с./дюйм2 = 0,11559 кВт/см2. Проверка переводного множителя."""
    rho_si, q_si = 1200.0, 0.030
    bh = bit_hydraulics(q_si, [14, 14, 14, 14, 14, 14], rho_si, 0.2159)
    check("HSI: согласованность кВт/см2 и л.с./дюйм2",
          bh["hsi_kW_cm2"], bh["hsi_hp_in2"] * 0.11559, 0.001)


# ==========================================================================
#  3. РЕЖИМЫ ТЕЧЕНИЯ И КОЭФФИЦИЕНТ ТРЕНИЯ
# ==========================================================================

def test_friction_factor():
    """f = 16/Re в ламинарной области; непрерывность на границах."""
    for n in (0.4, 0.7, 1.0):
        Re = 1000.0
        f, mode = _friction_factor(Re, n)
        check(f"Коэф. трения f=16/Re при n={n}", f, 16.0 / Re, 1e-6)

    # непрерывность: слева и справа от нижней критической точки
    n = 0.6
    Re_lam = 3470.0 - 1370.0 * n
    f1, _ = _friction_factor(Re_lam * 0.999, n)
    f2, _ = _friction_factor(Re_lam * 1.001, n)
    check("Непрерывность f на нижней границе перехода", f2, f1, 0.01)

    Re_tur = 4270.0 - 1370.0 * n
    f3, _ = _friction_factor(Re_tur * 0.999, n)
    f4, _ = _friction_factor(Re_tur * 1.001, n)
    check("Непрерывность f на верхней границе перехода", f4, f3, 0.01)


def test_regime_transition():
    """С ростом расхода режим обязан смениться ламинарный -> турбулентный."""
    f, _ = newtonian_fluid(mu_pas=0.005)
    modes = []
    for q in (0.0005, 0.005, 0.05):
        _, _, _, m = pipe_pressure_gradient(q, 0.1086, f)
        modes.append(m)
    check_true("Смена режима с ростом расхода",
               modes[0] == _t("fl_laminar") and modes[-1] == _t("fl_turbulent"),
               " -> ".join(modes))


# ==========================================================================
#  4. МОНОТОННОСТЬ И ФИЗИЧНОСТЬ
# ==========================================================================

def test_monotonic():
    f = Fluid(1.20, 20.0, 15.0)
    grads = [pipe_pressure_gradient(q, 0.1086, f)[0]
             for q in (0.002, 0.004, 0.008, 0.016)]
    check_true("Потери в трубе растут с расходом",
               all(b > a for a, b in zip(grads, grads[1:])))

    # при удвоении расхода в ламинарном режиме потери растут вдвое
    fN, _ = newtonian_fluid(mu_pas=0.2)          # заведомо ламинарный
    g1 = pipe_pressure_gradient(0.001, 0.1086, fN)[0]
    g2 = pipe_pressure_gradient(0.002, 0.1086, fN)[0]
    check("Ламинарный режим: dP пропорционально расходу", g2 / g1, 2.0, 0.01)

    ann = [annulus_pressure_gradient(0.03, 0.2159, d, f)[0]
           for d in (0.089, 0.127, 0.168)]
    check_true("Потери в затрубье растут при сужении зазора",
               all(b > a for a, b in zip(ann, ann[1:])))


def test_bit_scaling():
    """Перепад на долоте пропорционален квадрату расхода."""
    rho = 1200.0
    a = bit_hydraulics(0.020, [14] * 6, rho, 0.2159)["dp_Pa"]
    b = bit_hydraulics(0.040, [14] * 6, rho, 0.2159)["dp_Pa"]
    check("Долото: dP пропорционально квадрату расхода", b / a, 4.0, 0.001)

    c = bit_hydraulics(0.020, [14] * 3, rho, 0.2159)["dp_Pa"]
    check("Долото: вдвое меньше насадок -> вчетверо больше перепад",
          c / a, 4.0, 0.001)


def test_slip_velocity():
    """Скорость осаждения: предел Стокса и монотонность по размеру."""
    f = Fluid(1.20, 25.0, 20.0)
    vs = [slip_velocity(d / 1000.0, 2600.0, f.rho, f, 0.8, 0.05)[0]
          for d in (1.0, 3.0, 6.0, 10.0)]
    check_true("Скорость осаждения растёт с размером частицы",
               all(b > a for a, b in zip(vs, vs[1:])),
               ", ".join(f"{v:.3f}" for v in vs))

    # мелкая частица в вязком растворе -> область Стокса
    d = 0.0005
    v, mu_eff = slip_velocity(d, 2600.0, f.rho, f, 0.8, 0.05)
    want = (2600.0 - f.rho) * CFG.G * d ** 2 / (18.0 * mu_eff)
    check("Скорость осаждения: предел Стокса", v, want, 0.05)

    heavy = slip_velocity(0.005, 2900.0, f.rho, f, 0.8, 0.05)[0]
    light = slip_velocity(0.005, 2200.0, f.rho, f, 0.8, 0.05)[0]
    check_true("Тяжёлая порода осаждается быстрее лёгкой", heavy > light,
               f"{heavy:.3f} > {light:.3f}")


# ==========================================================================
#  5. СКВОЗНОЙ РАСЧЁТ: БАЛАНСЫ
# ==========================================================================

def test_yield_stress():
    """
    Жидкость с предельным напряжением сдвига: при Q -> 0 градиент
    давления стремится не к нулю, а к порогу страгивания tau0/H.
    Это принципиальное отличие Гершеля-Балкли от степенной модели.
    """
    d = {"t600": 74, "t300": 52, "t200": 42, "t100": 31, "t6": 9, "t3": 7}
    rh = Rheology(1.23, fann=d, model="herschel_bulkley")
    check_true("Гершель-Балкли: предельное напряжение больше нуля",
               rh.tau0 > 0, f"tau0 = {rh.tau0:.3f} Па")

    do, di = 0.2159, 0.127
    H = (do - di) / 4.0
    g = annulus_flow(1e-13, do, di, rh).dpdl
    check("Порог страгивания в затрубье: dP/dL -> tau0/H",
          g, rh.tau0 / H, 0.02)

    D = 0.1086
    g = pipe_flow(1e-13, D, rh).dpdl
    check("Порог страгивания в трубе: dP/dL -> 4*tau0/D",
          g, 4.0 * rh.tau0 / D, 0.02)

    pl = Rheology(1.23, fann=d, model="power_law")
    g_pl = annulus_flow(1e-13, do, di, pl).dpdl
    check_true("Степенная модель: порога страгивания нет",
               g_pl < 0.01 * rh.tau0 / H,
               f"{g_pl:.3g} против порога {rh.tau0 / H:.1f}")


def test_eccentricity():
    """Эксцентриситет снижает потери в затрубье, но не более чем втрое."""
    d = {"t600": 74, "t300": 52, "t200": 42, "t100": 31, "t6": 9, "t3": 7}
    rh = Rheology(1.23, fann=d)
    do, di, Q = 0.2159, 0.127, 0.030
    conc = annulus_flow(Q, do, di, rh, ecc=0.0).dpdl
    vals = [annulus_flow(Q, do, di, rh, ecc=e).dpdl
            for e in (0.0, 0.3, 0.6, 0.9)]
    check_true("Эксцентриситет снижает потери в затрубье",
               all(b <= a + 1e-12 for a, b in zip(vals, vals[1:])),
               " > ".join(f"{v:.1f}" for v in vals))
    check("Концентричное затрубье: поправка равна единице",
          eccentricity_factor(0.0, 0.6, di, do), 1.0, 1e-9)
    check_true("Поправка на эксцентриситет в разумных пределах",
               0.35 <= vals[-1] / conc <= 1.0,
               f"{vals[-1] / conc:.3f}")
    check_true("Эксцентриситет растёт с зенитным углом",
               eccentricity_at(0) < eccentricity_at(40) < eccentricity_at(85))


def test_rotation():
    """Вращение: эффект ограничен и исчезает при нулевых оборотах."""
    d = {"t600": 74, "t300": 52, "t200": 42, "t100": 31, "t6": 9, "t3": 7}
    rh = Rheology(1.23, fann=d)
    do, di, Q = 0.2159, 0.127, 0.030
    base = annulus_flow(Q, do, di, rh, rpm=0).dpdl
    check("Нулевые обороты: результат не меняется",
          annulus_flow(Q, do, di, rh, rpm=0).dpdl, base, 1e-9)
    for rpm in (60, 120, 200):
        v = annulus_flow(Q, do, di, rh, rpm=rpm).dpdl
        check_true(f"Вращение {rpm} об/мин: поправка в пределах 0,4...1,5",
                   0.4 * base <= v <= 1.5 * base, f"{v / base:.3f}")


def test_hole_cleaning():
    """Очистка ствола: режимы, форма кривой, геометрия подушки."""
    d = {"t600": 74, "t300": 52, "t200": 42, "t100": 31, "t6": 9, "t3": 7}
    rh = Rheology(1.23, fann=d)
    args = dict(d_out=0.2388, d_in=0.127, d_part=0.005, rho_s=2600.0,
                rop_mh=15.0, bit_d=0.2191, rpm=0.0)
    vs = {a: hole_cleaning(rh, 0.038, inc_deg=a, **args)["V_crit"]
          for a in (0, 20, 45, 60, 75, 90)}
    check_true("Требуемая скорость в вертикали ниже, чем в горизонтали",
               vs[0] < vs[90], f"{vs[0]:.2f} < {vs[90]:.2f}")
    check_true("В окне 40-60 град требуемая скорость превышает вертикаль",
               vs[45] > 1.8 * vs[0], f"{vs[45]:.2f} против {vs[0]:.2f}")
    check_true("Режим определяется по зенитному углу",
               hole_cleaning(rh, 0.038, inc_deg=10, **args)["regime"]
               == _t("hc_suspension")
               and hole_cleaning(rh, 0.038, inc_deg=80, **args)["regime"]
               == _t("hc_stationary"))

    # геометрия подушки
    D = 0.2159
    check("Подушка на всю высоту = площадь ствола",
          bed_area(D, D), math.pi * D ** 2 / 4.0, 1e-6)
    check("Подушка нулевой высоты = нулевая площадь", bed_area(0.0, D), 0.0)
    check("Подушка на половину ствола = половина площади",
          bed_area(D / 2, D), math.pi * D ** 2 / 8.0, 0.001)

    # равновесие: скорость над подушкой равна критической
    h, frac, A, V = equilibrium_bed(0.020, 0.2388, 0.127, 1.3)
    check_true("Подушка образуется при недостаточном расходе", frac > 0)
    check("Скорость над подушкой равна критической", V, 1.3, 0.01)

    big = hole_cleaning(rh, 0.015, inc_deg=85, **args)["bed_frac"]
    small = hole_cleaning(rh, 0.060, inc_deg=85, **args)["bed_frac"]
    check_true("Рост расхода уменьшает подушку", small < big,
               f"{small * 100:.1f}% < {big * 100:.1f}%")

    rot = hole_cleaning(rh, 0.038, inc_deg=85,
                        **{**args, "rpm": 120})["bed_frac"]
    still = hole_cleaning(rh, 0.038, inc_deg=85, **args)["bed_frac"]
    check_true("Вращение колонны уменьшает подушку", rot <= still,
               f"{rot * 100:.1f}% <= {still * 100:.1f}%")


def test_end_to_end():
    import os
    from hydraulics_core import InputData, Trajectory
    from hydraulics_solver import make_intervals, calc_interval

    from hydraulics_core import find_input_file, DATA_DIRS
    here = os.path.dirname(os.path.abspath(__file__))
    files = []
    p0 = find_input_file(CFG.EXCEL_FILE)
    if p0:
        files.append(p0)
    for sub in DATA_DIRS:
        d = os.path.normpath(os.path.join(here, sub))
        if os.path.isdir(d):
            files += [os.path.join(d, f) for f in sorted(os.listdir(d))
                      if f.lower().endswith(".xlsx")
                      and not f.startswith("~$")]
    data = None
    for path in files:
        if not os.path.exists(path):
            continue
        try:
            d = InputData(path)
            from hydraulics_solver import make_intervals as mi
            if mi(d):
                data = d
                break
        except Exception:
            continue
    if data is None:
        FAIL.append(f"{'Сквозной расчёт: нет файла с интервалами':<58s}")
        return
    traj = Trajectory(data.survey)
    ivs = make_intervals(data)
    if not ivs:
        FAIL.append(f"{'Сквозной расчёт: интервалы не сформированы':<58s}")
        return
    res = calc_interval(ivs[-1], data, traj)

    s = (res["dp_surface"] + res["dp_inside"] + res["dp_bit"] + res["dp_ann"])
    check("Баланс: сумма составляющих = давление на насосе",
          s, res["p_pump"], 1e-9)

    check("Баланс: сумма по участкам колонны = потери в колонне",
          sum(x.dp for x in res["inside"]), res["dp_inside"], 1e-9)
    check("Баланс: сумма по участкам затрубья = потери в затрубье",
          sum(x.dp for x in res["ann"]), res["dp_ann"], 1e-9)

    # непрерывность разбивки: участки без разрывов и нахлёстов
    gaps = [abs(b.md_top - a.md_bot) for a, b in
            zip(res["ann"], res["ann"][1:])]
    check_true("Разбивка затрубья без разрывов и нахлёстов",
               all(g < 1e-6 for g in gaps),
               f"макс. разрыв {max(gaps) if gaps else 0:.2e} м")

    total = res["ann"][-1].md_bot - res["ann"][0].md_top
    check("Разбивка перекрывает весь ствол", total, res["td"], 1e-6)

    # ЭЦП не может быть ниже статической плотности
    check_true("ЭЦП не ниже плотности раствора",
               res["ecd_bottom"] >= res["itv"]["rho"] - 1e-9,
               f"{res['ecd_bottom']:.4f} >= {res['itv']['rho']:.4f}")

    # При малом расходе потери на трение стремятся к нулю и ЭЦП должна
    # сойтись к статической плотности. Вклад шлама отключается: при
    # Q -> 0 концентрация шлама физически растёт, и это не ошибка.
    # Проверка ведётся на жидкости без предельного напряжения сдвига:
    # у раствора Гершеля-Балкли градиент при Q -> 0 стремится не к нулю,
    # а к порогу страгивания, и ЭЦП остаётся выше плотности. Это верно.
    keep_c = CFG.ACCOUNT_CUTTINGS_IN_ECD
    CFG.ACCOUNT_CUTTINGS_IN_ECD = False
    iv_pl = dict(ivs[-1])
    iv_pl["model"] = "power_law"
    try:
        tiny = calc_interval(iv_pl, data, traj, q_lps=0.02, quiet=True)
        check("ЭЦП при нулевом расходе = плотность раствора",
              tiny["ecd_bottom"], tiny["itv"]["rho"], 0.005)
    finally:
        CFG.ACCOUNT_CUTTINGS_IN_ECD = keep_c

    # рост расхода -> рост давления
    lo = calc_interval(ivs[-1], data, traj, q_lps=10, quiet=True)["p_pump"]
    hi = calc_interval(ivs[-1], data, traj, q_lps=25, quiet=True)["p_pump"]
    check_true("Давление на насосе растёт с расходом", hi > lo)


def test_trajectory():
    """Траектория: совпадение с замерами и согласованность MD, TVD, угла."""
    from hydraulics_core import Trajectory
    surv = [(0, 0, 0), (500, 0, 500), (1500, 60, 1350), (2000, 90, 1500)]
    t = Trajectory(surv, step=1.0)
    for md, inc, tvd in surv:
        check(f"Траектория: TVD на {md} м", t.tvd_at(md), tvd, 0.002)

    # проверка через интеграл: TVD = сумма dMD*cos(alpha)
    dz = 0.0
    for i in range(1, len(t.md)):
        a = math.radians(0.5 * (t.inc[i] + t.inc[i - 1]))
        dz += (t.md[i] - t.md[i - 1]) * math.cos(a)
    check("Траектория: TVD согласована с зенитным углом",
          dz, surv[-1][2] - surv[0][2], 0.005)

    check_true("Траектория: TVD монотонно растёт",
               all(b >= a - 1e-9 for a, b in zip(t.tvd, t.tvd[1:])))
    check_true("Траектория: MD >= TVD везде",
               all(m >= z - 1e-6 for m, z in zip(t.md, t.tvd)))


# ==========================================================================
#  ЗАПУСК
# ==========================================================================

TESTS = [
    ("Предельный переход к течению Пуазейля", test_poiseuille),
    ("Предельный переход к течению в щели", test_slot),
    ("Вырождение модели Бингама", test_bingham_limit),
    ("Согласованность моделей между собой", test_powerlaw_vs_bingham),
    ("Долото: сверка с промысловой формулой", test_bit_nozzles_field_units),
    ("Мощность: сверка с промысловой формулой",
     test_hydraulic_power_field_units),
    ("Скорость в затрубье: сверка с формулой",
     test_annular_velocity_field_units),
    ("HSI: согласованность единиц", test_hsi_units),
    ("Коэффициент трения", test_friction_factor),
    ("Смена режима течения", test_regime_transition),
    ("Монотонность потерь", test_monotonic),
    ("Масштабирование по долоту", test_bit_scaling),
    ("Скорость осаждения шлама", test_slip_velocity),
    ("Предельное напряжение сдвига", test_yield_stress),
    ("Эксцентриситет колонны", test_eccentricity),
    ("Вращение колонны", test_rotation),
    ("Очистка ствола", test_hole_cleaning),
    ("Траектория ствола", test_trajectory),
    ("Сквозной расчёт и балансы", test_end_to_end),
]


def main():
    print("=" * 96)
    print("  ВАЛИДАЦИЯ РАСЧЁТНОГО ЯДРА  NTS-HYDRA")
    print("=" * 96)
    for title, fn in TESTS:
        try:
            fn()
        except Exception:
            FAIL.append(f"{title:<58s} ИСКЛЮЧЕНИЕ")
            traceback.print_exc()

    for line in PASS:
        print("  [ok]   " + line)
    if FAIL:
        print()
        for line in FAIL:
            print("  [FAIL] " + line)

    print("=" * 96)
    print(f"  Пройдено: {len(PASS)}   Провалено: {len(FAIL)}")
    print("=" * 96)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
