# -*- coding: utf-8 -*-
"""
==========================================================================
 СВЕРКА РАСЧЁТА С ФАКТИЧЕСКИМИ ПРОГРАММАМИ БУРЕНИЯ
==========================================================================
 Эталон - гидравлические расчёты из программы бурения скважины 22288,
 куст 117, Тагульское месторождение (10 расчётных случаев, четыре
 диаметра ствола, глубины от 772 до 4240 м).

 Сверяются величины, которые программа вычисляет из геометрии и реологии
 и которые в эталоне приведены явно:

   1. параметры модели Гершеля-Балкли по показаниям вискозиметра;
   2. гидравлика долота: перепад, скорость истечения, мощность, HSI,
      сила удара струи;
   3. потери на трение в бурильных трубах - поэлементно;
   4. суммарные потери в затрубье;
   5. эквивалентная плотность циркуляции.

 Величины, зависящие от неизвестных нам данных (обвязка буровой,
 перепады на телесистеме и РУС), в сверку не входят.
==========================================================================
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

import hydraulics_config as CFG
CFG.LANGUAGE = "ru"
CFG.RHEOLOGY_MODEL = "herschel_bulkley"

from hydraulics_rheology import (                       # noqa: E402
    Rheology, pipe_flow, annulus_flow, DIAL_TO_PA, SHEAR,
    eccentricity_at,
)
from hydraulics_core import bit_hydraulics              # noqa: E402

ATM = 98066.5          # Па в одной технической атмосфере
LPM = 1.0 / 60000.0    # л/мин -> м3/с
MM = 1e-3

CASES = json.load(open(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reference_cases.json"),
    encoding="utf-8"))

REPORT = []


def cmp(case, name, got, ref, tol, unit="", note=""):
    if ref is None or got is None:
        return
    err = abs(got - ref) / abs(ref) * 100 if ref else 0.0
    REPORT.append({"case": case, "name": name, "got": got, "ref": ref,
                   "err": err, "ok": err <= tol, "tol": tol,
                   "unit": unit, "note": note})


def fluid_of(c):
    fann = {"t600": c["f600"], "t300": c["f300"], "t200": c["f200"],
            "t100": c["f100"], "t6": c["f6"], "t3": c["f3"]}
    return Rheology(c["rho"], fann=fann, model="herschel_bulkley")


# ==========================================================================
#  1. РЕОЛОГИЯ
# ==========================================================================

def check_rheology(c):
    rh = fluid_of(c)
    tag = f"{c['bit_mm']:.0f}мм/{c['MD']:.0f}м"
    cmp(tag, "Гершель-Балкли: n", rh.n, c["n"], 6)
    # предельное напряжение сдвига эталон даёт в фунт/100фут2
    ys_ref = c["YS"] * DIAL_TO_PA
    cmp(tag, "Гершель-Балкли: tau0, Па", rh.tau0, ys_ref, 25, "Па")
    # коэффициент консистенции эталон даёт в eq.cP = K[Па*с^n]*1000
    cmp(tag, "Гершель-Балкли: K, Па*с^n", rh.K, c["K"] / 1000.0, 20,
        "Па*с^n")
    return rh


# ==========================================================================
#  2. ДОЛОТО
# ==========================================================================

def check_bit(c, rh):
    tag = f"{c['bit_mm']:.0f}мм/{c['MD']:.0f}м"
    Q = (c["q_bit"] or c["Q_lpm"]) * LPM
    bh = bit_hydraulics(Q, c["nozzles"], rh.rho, c["bit_mm"] * MM)
    if bh is None:
        return
    cmp(tag, "Долото: перепад, атм", bh["dp_Pa"] / ATM, c["dp_bit"], 5, "атм")
    cmp(tag, "Долото: скорость истечения, м/с", bh["v_noz"], c["v_noz"], 5,
        "м/с")
    cmp(tag, "Долото: гидравл. мощность, кВт", bh["power_W"] / 1000.0,
        c["hhp"], 6, "кВт")
    cmp(tag, "Долото: HSI, л.с./дюйм2", bh["hsi_hp_in2"], c["hsi"], 10,
        "л.с./дюйм2")
    cmp(tag, "Долото: сила удара струи, Н", bh["impact_N"], c["impact"], 8,
        "Н")
    if c["tfa_mm2"]:
        cmp(tag, "Долото: площадь насадок, мм2", bh["A_noz_mm2"],
            c["tfa_mm2"], 3, "мм2")


# ==========================================================================
#  3. ТРЕНИЕ В БУРИЛЬНЫХ ТРУБАХ (ПОЭЛЕМЕНТНО)
# ==========================================================================

PIPE_WORDS = ("бур. трубы", "полуубт", "убт", "переводник", "тбт")


def check_pipe_friction(c, rh):
    tag = f"{c['bit_mm']:.0f}мм/{c['MD']:.0f}м"
    Q = c["Q_lpm"] * LPM
    for e in c["bha"]:
        nm = e["name"].lower()
        if not any(w in nm for w in PIPE_WORDS):
            continue
        if not e["len"] or e["len"] < 20 or not e["id"] or e["dp"] is None:
            continue
        if e["dp"] < 1.0:
            continue
        g = pipe_flow(Q, e["id"] * MM, rh).dpdl
        k = 1.0
        if "бур. трубы" in nm and e["od"] and e["od"] > 100:
            # замковые соединения: NC50, проходной Ø 82,6 мм,
            # длина замка 0,55 м на свече 9,45 м
            g_tj = pipe_flow(Q, 0.0826, rh).dpdl
            k = (8.9 * g + 0.55 * g_tj) / (9.45 * g)
        got = g * k * e["len"] / ATM
        cmp(tag, f"Трение внутри: {e['name']} L={e['len']:.0f} м "
                 f"Ø{e['id']:.1f}", got, e["dp"], 25, "атм")


# ==========================================================================
#  4. ЗАТРУБЬЕ И ЭЦП
# ==========================================================================

def annulus_profile(c, rh, use_ecc=True, use_rot=True):
    """Потери в затрубье по участкам: геометрия из эталонных таблиц."""
    Q = (c["q_bit"] or c["Q_lpm"]) * LPM
    inc = c["INC"] or 0.0
    rpm = (c["RPM"] or 0.0) if use_rot else 0.0
    ecc = eccentricity_at(inc) if use_ecc else 0.0

    # внешняя граница по глубине: из таблицы конструкции
    con = [x for x in c["construction"] if x["cum"]]
    con.sort(key=lambda x: x["cum"])

    def hole_at(md):
        for x in con:
            if md <= x["cum"] + 1e-6:
                return (x["id"] or c["bit_mm"]) * MM
        return c["bit_mm"] * MM

    # колонна снизу вверх
    parts, md = [], c["MD"]
    for e in c["bha"]:
        L = e["len"] or 0.0
        if L <= 0:
            continue
        parts.append((max(md - L, 0.0), md, e["od"] * MM, e["name"]))
        md -= L
        if md <= 0:
            break

    nodes = sorted({0.0, c["MD"]} | {x["cum"] for x in con if x["cum"] < c["MD"]}
                   | {p[0] for p in parts} | {p[1] for p in parts})
    nodes = [n for n in nodes if 0 <= n <= c["MD"]]

    total = 0.0
    for a, b in zip(nodes, nodes[1:]):
        if b - a < 1e-6:
            continue
        mid = 0.5 * (a + b)
        p = next((p for p in parts if p[0] - 1e-6 <= mid <= p[1] + 1e-6), None)
        if p is None:
            continue
        do, di = hole_at(mid), p[2]
        if do <= di:
            continue
        total += annulus_flow(Q, do, di, rh, ecc, rpm).dpdl * (b - a)
    return total


def check_annulus(c, rh):
    tag = f"{c['bit_mm']:.0f}мм/{c['MD']:.0f}м"
    for label, ecc, rot in (("концентрично, без вращения", False, False),
                            ("с эксцентриситетом и вращением", True, True)):
        got = annulus_profile(c, rh, ecc, rot) / ATM
        cmp(tag, f"Затрубье: потери, атм [{label}]", got, c["p_ann"], 40,
            "атм")

    # ЭЦП на забое: гидростатика + потери в затрубье
    dp = annulus_profile(c, rh, True, True)
    tvd = c["TVD"] or c["MD"]
    ecd = (rh.rho * 9.81 * tvd + dp) / (9.81 * tvd) / 1000.0
    cmp(tag, "ЭЦП на забое, г/см3", ecd, c["ecd"], 3, "г/см3")


# ==========================================================================
#  ЗАПУСК
# ==========================================================================

def main():
    for c in CASES:
        rh = check_rheology(c)
        check_bit(c, rh)
        check_pipe_friction(c, rh)
        check_annulus(c, rh)

    groups = {}
    for r in REPORT:
        key = r["name"].split(":")[0] if ":" in r["name"] else r["name"]
        if key.startswith("Трение внутри"):
            key = "Трение внутри бурильной колонны"
        groups.setdefault(key, []).append(r)

    print("=" * 100)
    print("  СВЕРКА С ПРОГРАММОЙ БУРЕНИЯ: скв. 22288, куст 117, "
          "Тагульское месторождение")
    print(f"  {len(CASES)} расчётных случаев, {len(REPORT)} сравнений")
    print("=" * 100)
    for g, rows in groups.items():
        ok = sum(1 for r in rows if r["ok"])
        errs = [r["err"] for r in rows]
        print(f"\n  {g}")
        print(f"     совпало {ok} из {len(rows)};  "
              f"расхождение: медиана {sorted(errs)[len(errs) // 2]:.1f} %, "
              f"максимум {max(errs):.1f} %")
        for r in rows:
            mark = "ok  " if r["ok"] else "ВНИМ"
            print(f"     [{mark}] {r['case']:<14} {r['name'][:52]:<52} "
                  f"расчёт {r['got']:>10.3f}  эталон {r['ref']:>10.3f}  "
                  f"{r['err']:>5.1f} %")
    tot_ok = sum(1 for r in REPORT if r["ok"])
    print("\n" + "=" * 100)
    print(f"  ИТОГО: совпало {tot_ok} из {len(REPORT)}")
    print("=" * 100)


if __name__ == "__main__":
    main()
