# -*- coding: utf-8 -*-
"""Разбор гидравлических расчётов из программы бурения (PDF) в JSON."""

import json
import re
import sys

import pymupdf

SRC = "Программа_бурения.pdf"   # положите рядом файл программы
PAGES = [39, 40, 58, 59, 77, 78, 96, 97, 119, 120]


def f(v):
    if v is None:
        return None
    v = str(v).replace("\xa0", " ").replace(" ", "").replace(",", ".")
    m = re.findall(r"-?\d+\.?\d*", v)
    return float(m[0]) if m else None


def field(txt, key, after=1):
    L = [x.strip() for x in txt.split("\n")]
    for i, l in enumerate(L):
        if l == key and i + after < len(L):
            return L[i + after]
    return None


def rows_by_y(page, y_from):
    w = page.get_text("words")
    rows = {}
    for x0, y0, x1, y1, word, *_ in w:
        if y0 < y_from - 1:
            continue
        rows.setdefault(round(y0, 0), []).append((x0, word))
    return [(y, sorted(rows[y])) for y in sorted(rows)]


def parse_tables(page):
    """КНБК и конструкция с одной страницы расчёта."""
    w = page.get_text("words")
    ys = [x[1] for x in w if x[4].startswith("Элемент")]
    if not ys:
        return [], []
    y0 = min(ys)
    ye = min([x[1] for x in w if x[4].startswith("Насадки")] or [1e9])

    bha, con = [], []
    for y, line in rows_by_y(page, y0 + 12):
        if y >= ye - 1:
            break
        left = [(x, t) for x, t in line if x < 360]
        right = [(x, t) for x, t in line if x >= 360]

        def split(cells, ncol):
            name, nums = [], []
            for x, t in cells:
                if re.fullmatch(r"-?[\d ,.]+", t) and any(c.isdigit() for c in t):
                    nums.append((x, t))
                else:
                    name.append(t)
            # имя может содержать цифры (16 3/4" Casing) - тогда числа
            # определяются по положению столбцов
            return " ".join(name), nums

        if left:
            nm, nums = split(left, 5)
            if nm and len(nums) >= 4:
                bha.append({"name": nm, "len": f(nums[0][1]),
                            "id": f(nums[1][1]), "od": f(nums[2][1]),
                            "cum": f(nums[3][1]),
                            "dp": f(nums[4][1]) if len(nums) > 4 else None})
        if right:
            nums = [(x, t) for x, t in right
                    if re.fullmatch(r"[\d,.]+", t) and x > 430]
            nm = " ".join(t for x, t in right if (x, t) not in nums)
            if nm and len(nums) >= 2:
                con.append({"name": nm, "len": f(nums[0][1]),
                            "id": f(nums[1][1]) if len(nums) > 2 else None,
                            "cum": f(nums[-1][1])})
    return bha, con


def parse_page(doc, pg):
    p = doc[pg]
    t = p.get_text()
    c = {"page": pg}
    keys = [("Расход:", "Q_lpm"), ("Долото по стволу", "MD"),
            ("Долото по верт", "TVD"), ("Башмак ОК", "shoe"),
            ("Плотность", "rho"), ("ПВ", "PV"), ("ДНС", "YP"),
            ("H-B n:", "n"), ("H-B YS:", "YS"), ("К консист", "K"),
            ("Fann 3:", "f3"), ("Fann 6:", "f6"), ("Fann 100:", "f100"),
            ("Fann 200:", "f200"), ("Fann 300:", "f300"),
            ("Fann 600:", "f600"), ("Размер мм", "bit_mm"),
            ("Скорость бурения", "ROP"), ("Частота вращения", "RPM"),
            ("Зенитный угол", "INC"), ("Диаметр:", "d_cut"),
            ("Плотность породы:", "rho_rock"),
            ("Наземное оборудование", "p_surf"), ("Внутри труб*", "p_dp"),
            ("КНБК", "p_bha"), ("ВЗД:", "p_motor"),
            ("Предохр. пер-ник", "p_sub"), ("Долото", "p_bit"),
            ("Возвр поток", "p_ann"),
            ("Разность в затр. и в тр.", "p_diff"), ("Всего", "p_total"),
            ("** ЭЦП на долоте:", "ecd"), ("ЭЦП на башмаке:", "ecd_shoe"),
            ("Скорость через насадки: м/сек", "v_noz"),
            ("Перепад на насадках ATM", "dp_bit"),
            ("Гидр-я мощность кВТ", "hhp"), ("HSI: HPSI", "hsi"),
            ("Сила г/м эф: Н", "impact"), ("Затруб.расход", "q_ann"),
            ("Критич.расход", "q_crit"), ("Расход на долоте: л/мин", "q_bit"),
            ("Пл. пром. отв. дюйм2", "tfa_mm2")]
    for k, name in keys:
        c[name] = f(field(t, k))
    m = re.search(r"Насадки 1/32 дюйма\n(.*?)\nОптимизация", t, re.S)
    nz = []
    if m:
        for a, b in re.findall(r"(\d+)\s*x\s*(\d+)", m.group(1)):
            nz += [int(b)] * int(a)
    c["nozzles"] = nz
    c["bha"], c["construction"] = parse_tables(p)
    return c


def main():
    doc = pymupdf.open(SRC)
    cases = [parse_page(doc, p) for p in PAGES]
    json.dump(cases, open("reference_cases.json", "w"),
              ensure_ascii=False, indent=1)
    for c in cases:
        print(f"стр.{c['page']:>4}  Ø{c['bit_mm']:>6.1f}  MD={c['MD']:>7.0f}  "
              f"Q={c['Q_lpm']:>6.0f} л/мин  ρ={c['rho']}  "
              f"КНБК {len(c['bha'])} эл.  конструкция {len(c['construction'])}"
              f"  P={c['p_total']:>4.0f} атм  ЭЦП={c['ecd']}")


if __name__ == "__main__":
    main()
