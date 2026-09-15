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
 ЛОКАЛИЗАЦИЯ / LOCALISATION
==========================================================================
 Язык отчёта и сообщений задаётся параметром LANGUAGE в файле настроек:
     "ru" - русский, "en" - English, "fr" - francais

 Строка запрашивается функцией t("ключ"). Если перевода нет, возвращается
 русский вариант - расчёт от этого не страдает.

     The report language is set by LANGUAGE in the configuration file.
     Strings are retrieved with t("key"); missing translations fall back
     to Russian.

 ПЕРЕВОДЧИКАМ. Словарь STRINGS - это ключ и кортеж из трёх строк в
 порядке ru, en, fr. Чтобы добавить язык, впишите его код в LANGS и
 добавьте четвёртый элемент в каждый кортеж.
==========================================================================
"""

import hydraulics_config as CFG

LANGS = ("ru", "en", "fr")


def lang():
    code = str(getattr(CFG, "LANGUAGE", "ru")).lower()[:2]
    return code if code in LANGS else "ru"


def t(key, *args, **kw):
    """Строка на текущем языке. Лишние аргументы идут в format()."""
    row = STRINGS.get(key)
    if row is None:
        return key
    i = LANGS.index(lang())
    s = row[i] if i < len(row) and row[i] else row[0]
    if args or kw:
        try:
            return s.format(*args, **kw)
        except (IndexError, KeyError):
            return s
    return s


def decimal_comma():
    """В русском и французском дробная часть отделяется запятой."""
    return lang() in ("ru", "fr")


def num(value, nd=2):
    """Число в местном формате."""
    if value is None:
        return t("dash")
    s = f"{value:.{nd}f}"
    return s.replace(".", ",") if decimal_comma() else s


# ==========================================================================
#  СЛОВАРЬ                     ru                    en                  fr
# ==========================================================================

STRINGS = {
    # ------------------------------------------------------- общее ------
    "dash": ("-", "-", "-"),
    "yes": ("да", "yes", "oui"),
    "no": ("нет", "no", "non"),
    "page": ("стр.", "p.", "p."),
    "note": ("Примечание", "Note", "Remarque"),

    # ------------------------------------------------------ единицы -----
    "u_m": ("м", "m", "m"),
    "u_mm": ("мм", "mm", "mm"),
    "u_ms": ("м/с", "m/s", "m/s"),
    "u_mh": ("м/ч", "m/h", "m/h"),
    "u_lps": ("л/с", "L/s", "L/s"),
    "u_gcm3": ("г/см³", "g/cm³", "g/cm³"),
    "u_deg": ("град", "deg", "deg"),
    "u_pct": ("%", "%", "%"),
    "u_kw": ("кВт", "kW", "kW"),
    "u_kn": ("кН", "kN", "kN"),
    "u_in2": ("дюйм²", "in²", "po²"),
    "u_cp": ("сПз", "cP", "cP"),
    "u_spm": ("ход/мин", "spm", "c/min"),
    "u_rpm": ("об/мин", "rpm", "tr/min"),
    "u_kwcm2": ("кВт/см²", "kW/cm²", "kW/cm²"),
    "u_hpin2": ("л.с./дюйм²", "hp/in²", "ch/po²"),
    "u_lb100": ("фунт/100фт²", "lb/100ft²", "lb/100pi²"),

    # -------------------------------------------------- титульный лист --
    "report_title": (
        "ГИДРАВЛИЧЕСКИЙ РАСЧЁТ ПРОМЫВКИ СКВАЖИНЫ",
        "DRILLING HYDRAULICS CALCULATION",
        "CALCUL HYDRAULIQUE DE FORAGE"),
    "report_sub": (
        "поинтервальный / посекционный",
        "interval by interval",
        "intervalle par intervalle"),
    "brief_title": ("ГИДРАВЛИЧЕСКИЙ РАСЧЁТ", "DRILLING HYDRAULICS",
                    "HYDRAULIQUE DE FORAGE"),
    "brief_sub": ("краткий отчёт", "summary report", "rapport de synthese"),
    "manual_title": ("РУКОВОДСТВО ПОЛЬЗОВАТЕЛЯ", "USER MANUAL",
                     "MANUEL DE L'UTILISATEUR"),

    # ---------------------------------------------------- реквизиты -----
    "r_client": ("Заказчик", "Client", "Client"),
    "r_field": ("Месторождение", "Field", "Gisement"),
    "r_pad": ("Куст", "Pad", "Plateforme"),
    "r_well": ("Скважина", "Well", "Puits"),
    "r_welltype": ("Тип скважины", "Well type", "Type de puits"),
    "r_contractor": ("Буровой подрядчик", "Drilling contractor",
                     "Entreprise de forage"),
    "r_rig": ("Буровая установка", "Rig", "Appareil de forage"),
    "r_target": ("Проектный горизонт", "Target formation",
                 "Horizon objectif"),
    "r_author": ("Исполнитель", "Prepared by", "Etabli par"),
    "r_date": ("Дата расчёта", "Date", "Date"),

    "i_td": ("Забой (проектный), м MD", "Total depth, m MD",
             "Profondeur finale, m MD"),
    "i_nint": ("Число расчётных интервалов", "Number of intervals",
               "Nombre d'intervalles"),
    "i_model": ("Модель реологии", "Rheology model", "Modele rheologique"),
    "i_flow": ("Расход из диапазона", "Flow rate from range",
               "Debit dans la plage"),
    "i_pumps": ("Буровые насосы", "Mud pumps", "Pompes a boue"),
    "flow_max": ("максимальный", "maximum", "maximum"),
    "flow_min": ("минимальный", "minimum", "minimum"),
    "flow_mean": ("средний", "average", "moyen"),
    "pumps_of": ("{n} шт., втулка {d} мм", "{n} unit(s), liner {d} mm",
                 "{n} unite(s), chemise {d} mm"),

    # --------------------------------------------------- модели ---------
    "m_hb": ("Гершеля-Балкли", "Herschel-Bulkley", "Herschel-Bulkley"),
    "m_pl": ("степенная", "power law", "loi de puissance"),
    "m_bg": ("Бингама", "Bingham", "Bingham"),

    # ------------------------------------------- страница конструкции ---
    "p_construction": (
        "Конструкция скважины, профиль и разрез",
        "Well architecture, trajectory and geology",
        "Architecture du puits, trajectoire et geologie"),
    "p_construction_sub": (
        "схема обсадных колонн, открытого ствола и литологии",
        "casing scheme, open hole and lithology",
        "schema des tubages, trou ouvert et lithologie"),
    "c_scheme": ("Конструкция (схема)", "Well scheme", "Schema du puits"),
    "c_profile": ("Профиль (верт. проекция)", "Trajectory (vertical section)",
                  "Trajectoire (section verticale)"),
    "c_geology": ("Литолого-стратиграфический разрез",
                  "Lithological section", "Coupe lithologique"),
    "c_diameter": ("диаметр, мм", "diameter, mm", "diametre, mm"),
    "c_md": ("глубина по стволу, м MD", "measured depth, m MD",
             "profondeur mesuree, m MD"),
    "c_tvd": ("глубина по вертикали, м TVD", "true vertical depth, m TVD",
              "profondeur verticale, m TVD"),
    "c_disp": ("отход, м", "displacement, m", "deport, m"),
    "c_inc": ("зенитный угол, град", "inclination, deg",
              "inclinaison, deg"),
    "c_formation": ("свита", "formation", "formation"),
    "c_rho_rock": ("ρ породы, г/см³", "rock density, g/cm³",
                   "densite roche, g/cm³"),
    "c_hanger": ("подвеска {d} м", "hanger at {d} m",
                 "suspension a {d} m"),
    "c_openhole": ("Открытый ствол", "Open hole", "Trou ouvert"),

    # ------------------------------------------- исходные данные --------
    "p_inputs": ("Исходные данные", "Input data", "Donnees d'entree"),
    "p_inputs_sub": ("долотная программа, раствор, обсадные колонны",
                     "bit programme, mud, casing",
                     "programme d'outils, boue, tubages"),
    "t_bitprog": ("Долотная программа и параметры раствора",
                  "Bit programme and mud properties",
                  "Programme d'outils et proprietes de la boue"),
    "t_casing": ("Конструкция скважины", "Casing design",
                 "Architecture de tubage"),
    "t_pumps": ("Буровые насосы", "Mud pumps", "Pompes a boue"),
    "t_nozzles_block": ("Компоновка промывочных узлов и режим бурения",
                        "Circulation components and drilling parameters",
                        "Organes de circulation et parametres de forage"),

    "h_interval": ("Интервал", "Interval", "Intervalle"),
    "h_md": ("MD, м", "MD, m", "MD, m"),
    "h_bit_d": ("Ø долота,\nмм", "Bit dia.,\nmm", "Ø outil,\nmm"),
    "h_bit_type": ("Тип долота", "Bit type", "Type d'outil"),
    "h_rop": ("МСП,\nм/ч", "ROP,\nm/h", "VOP,\nm/h"),
    "h_drive": ("Привод", "Drive", "Entrainement"),
    "h_q": ("Q,\nл/с", "Q,\nL/s", "Q,\nL/s"),
    "h_mudtype": ("Тип раствора", "Mud type", "Type de boue"),
    "h_rho": ("ρ,\nг/см³", "ρ,\ng/cm³", "ρ,\ng/cm³"),
    "h_pv": ("PV,\nсПз", "PV,\ncP", "VP,\ncP"),
    "h_yp": ("ДНС,\nфунт/\n100фт²", "YP,\nlb/\n100ft²", "YP,\nlb/\n100pi²"),
    "h_model": ("Модель\nреологии", "Rheology\nmodel", "Modele\nrheologique"),
    "h_casing": ("Колонна", "Casing", "Tubage"),
    "h_od": ("Ø нар., мм", "OD, mm", "Ø ext., mm"),
    "h_wall": ("Стенка, мм", "Wall, mm", "Epaisseur, mm"),
    "h_id": ("Ø вн., мм", "ID, mm", "Ø int., mm"),
    "h_shoe": ("MD / TVD, м", "MD / TVD, m", "MD / TVD, m"),
    "h_nozzles": ("Насадки долота", "Bit nozzles", "Duses de l'outil"),
    "h_caving": ("Коэф.\nкавернозности", "Washout\nfactor",
                 "Facteur de\ncavage"),
    "h_motor": ("ВЗД", "Mud motor", "Moteur de fond"),
    "h_mwd": ("Телесистема", "MWD", "MWD"),
    "h_dp_motor": ("ΔP ВЗД,\n{u}", "Motor ΔP,\n{u}", "ΔP moteur,\n{u}"),
    "h_dp_mwd": ("ΔP MWD,\n{u}", "MWD ΔP,\n{u}", "ΔP MWD,\n{u}"),
    "h_rpm": ("Обороты,\nоб/мин", "Rotation,\nrpm", "Rotation,\ntr/min"),
    "h_param": ("Параметр насосной группы", "Pump parameter",
                "Parametre de pompe"),
    "h_value": ("Значение", "Value", "Valeur"),

    "pump_type": ("Тип насоса", "Pump type", "Type de pompe"),
    "pump_n": ("Рабочих насосов, шт.", "Pumps in operation",
               "Pompes en service"),
    "pump_liner": ("Диаметр втулки, мм", "Liner diameter, mm",
                   "Diametre de chemise, mm"),
    "pump_stroke": ("Длина хода, мм", "Stroke length, mm",
                    "Course, mm"),
    "pump_cyl": ("Цилиндров, шт.", "Cylinders", "Cylindres"),
    "pump_fill": ("Коэф. наполнения", "Volumetric efficiency",
                  "Rendement volumetrique"),
    "pump_spm": ("Макс. ходов, 1/мин", "Max strokes, spm",
                 "Courses max, c/min"),
    "pump_pmax": ("Макс. давление, {u}", "Max pressure, {u}",
                  "Pression max, {u}"),
    "pump_power": ("Мощность, кВт", "Power, kW", "Puissance, kW"),

    # ------------------------------------------- страница интервала -----
    "p_section": ("Секция «{k}»   {a}-{b} м", "Interval \"{k}\"   {a}-{b} m",
                  "Intervalle \"{k}\"   {a}-{b} m"),
    "p_section_sub": (
        "Ø долота {d} мм · Q = {q} л/с · ρ = {rho} г/см³ · "
        "PV = {pv} сПз · ДНС = {yp} фунт/100фт² · МСП = {rop} м/ч",
        "Bit {d} mm · Q = {q} L/s · ρ = {rho} g/cm³ · "
        "PV = {pv} cP · YP = {yp} lb/100ft² · ROP = {rop} m/h",
        "Outil {d} mm · Q = {q} L/s · ρ = {rho} g/cm³ · "
        "VP = {pv} cP · YP = {yp} lb/100pi² · VOP = {rop} m/h"),
    "g_bha": ("КНБК - {k}", "BHA - {k}", "Garniture de fond - {k}"),
    "g_bha_tmpl": ("\n(ориентировочная компоновка)", "\n(indicative BHA)",
                   "\n(garniture indicative)"),
    "g_bha_len": ("Σ КНБК = {L} м", "Σ BHA = {L} m", "Σ garniture = {L} m"),
    "g_bha_axis": ("расстояние от долота вверх, м",
                   "distance above bit, m", "distance au-dessus de l'outil, m"),
    "g_pressure": ("Эпюра давлений", "Pressure profile",
                   "Profil de pression"),
    "g_inside": ("внутри БК", "inside string", "interieur garniture"),
    "g_annulus": ("затрубье", "annulus", "annulaire"),
    "g_hydrostatic": ("гидростатика", "hydrostatic", "hydrostatique"),
    "g_pressure_x": ("давление, {u}", "pressure, {u}", "pression, {u}"),
    "g_velocity": ("Скорость в затрубье", "Annular velocity",
                   "Vitesse annulaire"),
    "g_required": ("требуемая", "required", "requise"),
    "g_ecd": ("ЭЦП и вынос шлама", "ECD and cuttings transport",
              "DEC et transport des deblais"),
    "g_ecd_x": ("ЭЦП, г/см³", "ECD, g/cm³", "DEC, g/cm³"),
    "g_conc": ("Cшлам, %", "cuttings, %", "deblais, %"),
    "g_balance": ("Баланс потерь давления", "Pressure loss breakdown",
                  "Repartition des pertes de charge"),
    "g_sweep": ("Влияние расхода", "Effect of flow rate",
                "Influence du debit"),
    "g_pump_p": ("P насоса", "pump pressure", "pression pompe"),
    "g_density": ("плотность, г/см³", "density, g/cm³", "densite, g/cm³"),

    "b_surface": ("Наземная обвязка", "Surface equipment",
                  "Equipement de surface"),
    "b_string": ("Бурильная колонна", "Drill string", "Garniture de forage"),
    "b_motor": ("ВЗД", "Mud motor", "Moteur de fond"),
    "b_mwd": ("Телесистема", "MWD", "MWD"),
    "b_bit": ("Насадки долота", "Bit nozzles", "Duses de l'outil"),
    "b_annulus": ("Затрубье", "Annulus", "Annulaire"),

    # ----------------------------------------- итоговые показатели ------
    "s_results": ("ИТОГОВЫЕ ПОКАЗАТЕЛИ", "KEY RESULTS",
                  "RESULTATS PRINCIPAUX"),
    "s_assess": ("ОЦЕНКА СООТВЕТСТВИЯ", "COMPLIANCE CHECK",
                 "VERIFICATION DES CRITERES"),
    "s_p_start": ("Давление, начало интервала", "Pressure, start of interval",
                  "Pression, debut d'intervalle"),
    "s_p_end": ("Давление, конец интервала", "Pressure, end of interval",
                "Pression, fin d'intervalle"),
    "s_load": ("Загрузка насоса", "Pump load", "Charge de la pompe"),
    "s_spm": ("Ходов насоса", "Pump strokes", "Courses de pompe"),
    "s_power": ("Гидравл. мощность", "Hydraulic power",
                "Puissance hydraulique"),
    "s_dp_bit": ("ΔP на долоте", "Bit ΔP", "ΔP a l'outil"),
    "s_vnoz": ("Скорость истечения", "Nozzle velocity",
               "Vitesse aux duses"),
    "s_tfa": ("TFA", "TFA", "TFA"),
    "s_hsi": ("HSI", "HSI", "HSI"),
    "s_same": ("то же", "same", "idem"),
    "s_impact": ("Сила удара струи", "Jet impact force",
                 "Force d'impact du jet"),
    "s_ecd": ("ЭЦП на забое", "ECD at bottom", "DEC au fond"),
    "s_ecd_rise": ("Прирост к ρ", "Increase over ρ", "Ecart avec ρ"),
    "s_rho_bh": ("ρ на забое (T, P)", "ρ at bottom (T, P)",
                 "ρ au fond (T, P)"),
    "s_temp": ("Температура забоя", "Bottomhole temperature",
               "Temperature de fond"),
    "s_inc_max": ("Зенитный угол (макс)", "Max inclination",
                  "Inclinaison max"),
    "s_rpm": ("Обороты колонны", "String rotation", "Rotation garniture"),
    "s_bed": ("Шламовая подушка", "Cuttings bed", "Lit de deblais"),
    "s_gel": ("Давление страгивания", "Break circulation pressure",
              "Pression de demarrage"),
    "s_rho_cut": ("ρ породы (шлам)", "Cuttings density",
                  "Densite des deblais"),
    "of_hole": ("% ствола", "% of hole", "% du trou"),

    # ------------------------------------------------- критерии ---------
    "k_vmin": ("Скорость в затрубье (мин)", "Annular velocity (min)",
               "Vitesse annulaire (min)"),
    "k_vmax": ("Скорость в затрубье (макс)*", "Annular velocity (max)*",
               "Vitesse annulaire (max)*"),
    "k_conc": ("Концентрация шлама (макс)", "Cuttings concentration (max)",
               "Concentration de deblais (max)"),
    "k_margin": ("Запас по скорости выноса", "Transport velocity margin",
                 "Marge de vitesse de transport"),
    "k_bed": ("Шламовая подушка (макс)", "Cuttings bed (max)",
              "Lit de deblais (max)"),
    "k_hsi": ("Уд. мощность долота HSI", "Bit hydraulic intensity HSI",
              "Puissance specifique HSI"),
    "k_ecd": ("ЭЦП на забое", "ECD at bottom", "DEC au fond"),
    "k_load": ("Загрузка насоса по давлению", "Pump pressure load",
               "Charge en pression de la pompe"),
    "k_spm": ("Число ходов насоса", "Pump strokes", "Courses de pompe"),
    "k_share": ("Доля перепада на долоте", "Bit pressure share",
                "Part de perte a l'outil"),
    "k_frac": ("Запас до давления ГРП", "Margin to fracture pressure",
               "Marge avant fracturation"),
    "k_pore": ("Репрессия на пласт", "Overbalance", "Surpression"),
    "k_at": ("на {a}-{b} м", "at {a}-{b} m", "a {a}-{b} m"),

    # ------------------------------------------------- таблицы ----------
    "p_tables": ("Поинтервальный расчёт - «{k}»",
                 "Detailed calculation - \"{k}\"",
                 "Calcul detaille - \"{k}\""),
    "p_tables_sub": (
        "потери давления по элементам бурильной колонны и участкам затрубья",
        "pressure losses by string component and annular section",
        "pertes de charge par element et par section annulaire"),
    "t_inside": ("Внутри бурильной колонны", "Inside the drill string",
                 "Interieur de la garniture"),
    "t_annulus": ("Затрубное пространство", "Annulus", "Espace annulaire"),
    "h_element": ("Элемент колонны", "String component",
                  "Element de garniture"),
    "h_len": ("L, м", "L, m", "L, m"),
    "h_v": ("V, м/с", "V, m/s", "V, m/s"),
    "h_re": ("Re", "Re", "Re"),
    "h_regime": ("Режим", "Regime", "Regime"),
    "h_grad": ("Град.,\n{u}/100 м", "Gradient,\n{u}/100 m",
               "Gradient,\n{u}/100 m"),
    "h_dp": ("ΔP, {u}", "ΔP, {u}", "ΔP, {u}"),
    "h_ann_sec": ("Участок затрубья", "Annular section", "Section annulaire"),
    "h_inc": ("зенит,\n°", "inc.,\n°", "incl.,\n°"),
    "h_od_hole": ("Ø нар.,\nмм", "OD hole,\nmm", "Ø trou,\nmm"),
    "h_od_pipe": ("Ø тр.,\nмм", "OD pipe,\nmm", "Ø tige,\nmm"),
    "h_vreq": ("V треб.,\nм/с", "V req.,\nm/s", "V req.,\nm/s"),
    "h_kecc": ("k экс.", "k ecc.", "k exc."),
    "h_krot": ("k вращ.", "k rot.", "k rot."),
    "h_bed": ("подушка,\n%", "bed,\n%", "lit,\n%"),
    "h_conc": ("Сшлам,\n%", "cuttings,\n%", "deblais,\n%"),
    "total_line": (
        "ИТОГО:   обвязка {a} + колонна {b} + долото {c} + затрубье {d}"
        "  =  {tot}",
        "TOTAL:   surface {a} + string {b} + bit {c} + annulus {d}"
        "  =  {tot}",
        "TOTAL:   surface {a} + garniture {b} + outil {c} + annulaire {d}"
        "  =  {tot}"),

    # ------------------------------------------------- режимы -----------
    "fl_laminar": ("ламинарный", "laminar", "laminaire"),
    "fl_turbulent": ("турбулентный", "turbulent", "turbulent"),
    "fl_transition": ("переходный", "transitional", "transitoire"),
    "hc_suspension": ("взвесь", "suspension", "suspension"),
    "hc_sliding": ("сползающая подушка", "sliding bed", "lit glissant"),
    "hc_stationary": ("неподвижная подушка", "stationary bed", "lit fixe"),

    # ------------------------------------------------- сводные ----------
    "p_summary": ("Сводные результаты по секциям", "Summary by interval",
                  "Synthese par intervalle"),
    "p_summary_sub": (
        "давление, ЭЦП, показатели работы долота и выноса шлама",
        "pressure, ECD, bit hydraulics and cuttings transport",
        "pression, DEC, hydraulique de l'outil et transport des deblais"),
    "g_struct": ("Структура потерь давления по интервалам",
                 "Pressure loss breakdown by interval",
                 "Repartition des pertes par intervalle"),
    "g_rho_ecd": ("Плотность раствора и ЭЦП", "Mud density and ECD",
                  "Densite de boue et DEC"),
    "g_pmax": ("макс. давление", "max pressure", "pression max"),
    "g_mud": ("ρ раствора", "mud density", "densite boue"),
    "g_ecd_bh": ("ЭЦП на забое", "ECD at bottom", "DEC au fond"),
    "h_pstart": ("P нач.,\n{u}", "P start,\n{u}", "P debut,\n{u}"),
    "h_pend": ("P кон.,\n{u}", "P end,\n{u}", "P fin,\n{u}"),
    "h_vann": ("V затр.,\nм/с", "V ann.,\nm/s", "V ann.,\nm/s"),
    "h_ecd": ("ЭЦП,\nг/см³", "ECD,\ng/cm³", "DEC,\ng/cm³"),
    "h_hsi": ("HSI,\nкВт/см²", "HSI,\nkW/cm²", "HSI,\nkW/cm²"),
    "h_spm": ("ходов/\nмин", "spm", "c/min"),
    "h_loadpct": ("загрузка", "load", "charge"),

    # ------------------------------------------- краткий отчёт ----------
    "br_results": ("Результаты по интервалам", "Results by interval",
                   "Resultats par intervalle"),
    "br_scheme": ("Конструкция", "Well scheme", "Schema du puits"),
    "br_window": ("ЭЦП в окне бурения", "ECD within the drilling window",
                  "DEC dans la fenetre de forage"),
    "br_pore": ("поровое", "pore", "pression de pore"),
    "br_frac": ("ГРП", "fracture", "fracturation"),
    "br_assess": ("Оценка соответствия критериям", "Compliance check",
                  "Verification des criteres"),
    "br_criteria": ("Принятые критерии", "Applied criteria",
                    "Criteres appliques"),
    "br_head": (
        "Забой {td} м MD · интервалов {n} · насосы {pump} · реология: {model}",
        "TD {td} m MD · {n} intervals · pumps {pump} · rheology: {model}",
        "Profondeur {td} m MD · {n} intervalles · pompes {pump} · "
        "rheologie: {model}"),
    "br_note": (
        "Критерии очистки ствола (скорость в затрубье и концентрация шлама) "
        "принимаются по каждому интервалу отдельно, если они заданы в "
        "исходных данных; в таблице приведены значения для первого "
        "интервала. Остальные критерии общие для всей скважины.\n\n"
        "Звёздочкой отмечена максимальная скорость в затрубье: она "
        "оценивается только по протяжённым участкам, короткие переводники и "
        "калибраторы в оценку не входят.",
        "Hole cleaning criteria (annular velocity and cuttings "
        "concentration) are taken per interval where specified in the input "
        "data; the table shows the values for the first interval. All other "
        "criteria apply to the whole well.\n\n"
        "The asterisk marks the maximum annular velocity: it is evaluated "
        "over long sections only, short subs and stabilisers are excluded.",
        "Les criteres de nettoyage du trou (vitesse annulaire et "
        "concentration de deblais) sont pris par intervalle lorsqu'ils sont "
        "definis; le tableau donne les valeurs du premier intervalle. Les "
        "autres criteres valent pour tout le puits.\n\n"
        "L'asterisque indique la vitesse annulaire maximale: elle n'est "
        "evaluee que sur les sections longues, les raccords courts et les "
        "stabilisateurs sont exclus."),
    "st_ok": ("норма", "pass", "conforme"),
    "st_warn": ("внимание", "check", "a verifier"),
    "st_bad": ("нарушение", "fail", "non conforme"),
    "st_ok_d": ("критерий выполнен", "criterion met", "critere respecte"),
    "st_warn_d": ("на границе", "borderline", "limite"),
    "st_bad_d": ("не выполнен", "not met", "non respecte"),
    "cr_vmin": ("Мин. скорость в затрубье, м/с",
                "Min annular velocity, m/s",
                "Vitesse annulaire min, m/s"),
    "cr_vmin_v": ("{a} в вертикали / {b} в наклоне",
                  "{a} vertical / {b} inclined",
                  "{a} vertical / {b} incline"),
    "cr_vmax": ("Макс. скорость в затрубье, м/с",
                "Max annular velocity, m/s",
                "Vitesse annulaire max, m/s"),
    "cr_conc": ("Предельная концентрация шлама, %",
                "Max cuttings concentration, %",
                "Concentration max de deblais, %"),
    "cr_bed": ("Предельная высота шламовой подушки, % ствола",
               "Max cuttings bed height, % of hole",
               "Hauteur max du lit de deblais, % du trou"),
    "cr_hsi": ("Мин. удельная мощность долота, кВт/см²",
               "Min bit hydraulic intensity, kW/cm²",
               "Puissance specifique min, kW/cm²"),
    "cr_ecd": ("Допустимый прирост ЭЦП, г/см³",
               "Allowable ECD increase, g/cm³",
               "Augmentation admissible de DEC, g/cm³"),
    "cr_load": ("Предельная загрузка насоса, %", "Max pump load, %",
                "Charge max de la pompe, %"),
    "h_criterion": ("Критерий", "Criterion", "Critere"),

    # ------------------------------------------------- консоль ----------
    "cli_title": ("Гидравлический расчёт промывки скважины",
                  "Drilling hydraulics calculation",
                  "Calcul hydraulique de forage"),
    "cli_license": ("Apache License 2.0. Поставляется БЕЗ КАКИХ-ЛИБО ГАРАНТИЙ.",
                    "Apache License 2.0. Provided WITHOUT ANY WARRANTY.",
                    "Licence Apache 2.0. Fourni SANS AUCUNE GARANTIE."),
    "cli_read": ("[1/5] Чтение исходных данных: {f}",
                 "[1/5] Reading input data: {f}",
                 "[1/5] Lecture des donnees: {f}"),
    "cli_traj": ("[2/5] Построение траектории MD → TVD",
                 "[2/5] Building MD → TVD trajectory",
                 "[2/5] Construction de la trajectoire MD → TVD"),
    "cli_int": ("[3/5] Формирование расчётных интервалов",
                "[3/5] Building calculation intervals",
                "[3/5] Constitution des intervalles"),
    "cli_calc": ("[4/5] Гидравлический расчёт", "[4/5] Hydraulics calculation",
                 "[4/5] Calcul hydraulique"),
    "cli_pdf": ("[5/5] Формирование PDF-отчёта", "[5/5] Building PDF report",
                "[5/5] Generation du rapport PDF"),
    "cli_done": ("ГОТОВО.  Отчёт: {f}", "DONE.  Report: {f}",
                 "TERMINE.  Rapport: {f}"),
    "cli_brief": ("Краткий отчёт: {f}", "Summary report: {f}",
                  "Rapport de synthese: {f}"),
    "cli_pages": ("Страниц: {n}", "Pages: {n}", "Pages: {n}"),
    "cli_notes": ("Замечаний к исходным данным: {n}",
                  "Input data remarks: {n}", "Remarques sur les donnees: {n}"),
    "cli_nofile": ("ОШИБКА: файл «{f}» не найден.",
                   "ERROR: file \"{f}\" not found.",
                   "ERREUR: fichier \"{f}\" introuvable."),
    "cli_fallback": ("файл из настроек не найден, использую: {f}",
                     "configured file not found, using: {f}",
                     "fichier configure introuvable, utilisation de: {f}"),
    "cli_sheets": ("листов: {s}; колонн: {c}; точек инклинометрии: {t}",
                   "sheets: {s}; casings: {c}; survey stations: {t}",
                   "feuilles: {s}; tubages: {c}; points de deviation: {t}"),
    "cli_nothing": ("Нет ни одного рассчитанного интервала. "
                    "Проверьте исходные данные.",
                    "No intervals calculated. Check the input data.",
                    "Aucun intervalle calcule. Verifiez les donnees."),
    "cli_req": ("реквизиты: {s}", "well: {s}", "puits: {s}"),
}
