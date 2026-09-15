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
  ГИДРАВЛИЧЕСКИЙ РАСЧЁТ БУРЕНИЯ СКВАЖИНЫ  -  ГЛАВНЫЙ ФАЙЛ
==========================================================================
  ЗАПУСК В THONNY:
    1. Положите в одну папку 4 файла:
         main.py, hydraulics_config.py, hydraulics_core.py,
         hydraulics_solver.py, hydraulics_plots.py
       и Excel-файл с исходными данными.
    2. Установите библиотеки (Thonny → Инструменты → Управление пакетами):
         numpy, pandas, matplotlib, openpyxl
    3. Откройте main.py и нажмите F5.
    4. Рядом появится PDF-отчёт.
==========================================================================
"""

import os
import sys
import traceback

try:
    from matplotlib.backends.backend_pdf import PdfPages
except ImportError:
    print("Не установлен matplotlib. Thonny → Инструменты → Управление пакетами → matplotlib")
    sys.exit(1)

import hydraulics_config as CFG
import hydraulics_core as CORE
import hydraulics_plots as PLOT
from hydraulics_core import InputData, Trajectory, pfmt, punit
from hydraulics_lang import t
from hydraulics_solver import make_intervals, calc_interval, sweep_flow, assess


BAR = "=" * 74


def main():
    print(BAR)
    print(f"  {CFG.APP_NAME}  {CFG.APP_VERSION}   ·   {CFG.APP_AUTHOR}")
    print("  " + t("cli_title"))
    print("  " + t("cli_license"))
    print(BAR)

    path = CORE.find_input_file(CFG.EXCEL_FILE, prefer_template=False)
    if path is None:
        print("\n  " + t("cli_nofile", f=CFG.EXCEL_FILE))
        print("  Положите его рядом с main.py либо в папку templates,")
        print("  либо укажите полный путь в EXCEL_FILE "
              "(файл hydraulics_config.py).")
        return
    if os.path.basename(path) != os.path.basename(CFG.EXCEL_FILE):
        print("      " + t("cli_fallback", f=os.path.basename(path)))

    print("\n" + t("cli_read", f=os.path.basename(path)))
    data = InputData(path)
    print("      " + t("cli_sheets", s=len(data.sheetnames),
                        c=len(data.casings), t=len(data.survey)))

    PLOT.WELL_CAPTION = PLOT.well_caption(data)
    if data.general:
        print("      " + t("cli_req", s=PLOT.WELL_CAPTION))

    print(t("cli_traj"))
    traj = Trajectory(data.survey, step=1.0)

    print(t("cli_int"))
    intervals = make_intervals(data)
    for i in intervals:
        print(f"      {i['key']:<16} {i['md_from']:>7.0f} - "
              f"{i['md_to']:<7.0f} {t('u_m')}   "
              f"Ø{i['bit_mm']:>6.1f} {t('u_mm')}   "
              f"Q = {i['q_lps']:>4.0f} {t('u_lps')}   "
              f"ρ = {i['rho']:.2f} {t('u_gcm3')}")

    print(t("cli_calc"))
    results, sweeps = [], []
    for itv in intervals:
        res = calc_interval(itv, data, traj)
        if res is None:
            continue
        # тот же интервал в начале бурения: колонна короче, потери меньше
        md0 = max(itv["md_from"], 1.0)
        try:
            start = calc_interval(itv, data, traj, td_override=md0,
                                  quiet=True)
            res["p_start"] = start["p_pump"]
            res["ecd_start"] = start["ecd_bottom"]
            res["spm_start"] = start["spm"]
            res["load_start"] = start["load_pct"]
        except Exception:
            res["p_start"] = None
        results.append(res)
        sweeps.append(sweep_flow(itv, data, traj))
        print(f"      {itv['key']:<16} "
              f"{t('s_p_end').split(',')[0]} = "
              f"{pfmt(res.get('p_start') or res['p_pump']):>6}"
              f" -> {pfmt(res['p_pump']):>6} {punit()}   "
              f"{t('s_dp_bit')} = {pfmt(res['dp_bit']):>6} {punit()}   "
              f"{t('s_ecd')} = {res['ecd_bottom']:.3f} {t('u_gcm3')}   "
              f"{t('s_load')} {res['load_pct']:.0f} %")

    if not results:
        print("\n  " + t("cli_nothing"))
        return

    print(t("cli_pdf"))
    out = CFG.PDF_OUT
    if not os.path.isabs(out):
        out = os.path.join(os.path.dirname(os.path.abspath(path)), out)

    with PdfPages(out) as pdf:
        n = 1
        show_notes = getattr(CFG, "SHOW_NOTES_PAGE", False)
        PLOT.page_title(pdf, data, intervals,
                        CORE.WARNINGS if show_notes else [])
        n += 1
        PLOT.page_construction(pdf, data, traj, intervals, n)
        n += 1
        PLOT.page_inputs(pdf, data, intervals, n)
        for res, sw in zip(results, sweeps):
            n += 1
            PLOT.page_section(pdf, res, assess(res), sw, traj, n)
            n += 1
            PLOT.page_section_tables(pdf, res, n)
        n += 1
        PLOT.page_summary(pdf, results, n)

        if getattr(CFG, "SHOW_NOTES_PAGE", False):
            n += 1
            PLOT.page_notes(pdf, CORE.WARNINGS, n)

        d = pdf.infodict()
        d["Title"] = (f"Гидравлический расчёт промывки скважины - "
                      f"{PLOT.WELL_CAPTION}")
        d["Author"] = data.general.get("ответственный исполнитель", CFG.AUTHOR)
        d["Subject"] = PLOT.WELL_CAPTION
        d["Creator"] = f"{CFG.APP_NAME} {CFG.APP_VERSION} ({CFG.APP_AUTHOR})"


    brief = None
    if getattr(CFG, "BRIEF_REPORT", True):
        brief = os.path.join(os.path.dirname(out),
                             getattr(CFG, "PDF_BRIEF",
                                     "Гидравлический_расчёт_кратко.pdf"))
        PLOT.brief_report(brief, data, intervals, results, traj)

    print(BAR)
    print("  " + t("cli_done", f=out))
    if brief:
        print("  " + t("cli_brief", f=brief))
    print("  " + t("cli_pages", n=n))
    if CORE.WARNINGS:
        print("\n  " + t("cli_notes", n=len(CORE.WARNINGS)) + ":")
        for w in CORE.WARNINGS:
            print(f"    • {w}")
    print(BAR)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("\n--- ОШИБКА ВЫПОЛНЕНИЯ ---")
        traceback.print_exc()
