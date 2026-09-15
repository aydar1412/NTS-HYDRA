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
 ЧТЕНИЕ ДОПОЛНИТЕЛЬНЫХ ЛИСТОВ (шаблон с уточнёнными данными)
==========================================================================
 Все листы НЕОБЯЗАТЕЛЬНЫ. Если лист есть и заполнен - его данные имеют
 приоритет над значениями из hydraulics_config.py. Если листа нет или
 строка пустая - работает значение из конфигурации.
==========================================================================
"""

import re

import hydraulics_config as CFG

SHEETS = {
    "general":   "Общие сведения",
    "nozzles":   "Насадки долот",
    "motor":     "ВЗД",
    "mwd":       "Телесистема",
    "pumps":     "Буровые насосы",
    "surface":   "Наземная обвязка",
    "survey":    "Инклинометрия",
    "rheology":  "Реология",
    "caving":    "Кавернозность",
    "pressure":  "Градиенты давлений",
    "drillpipe": "Бурильная колонна",
    "temp":      "Температура",
    "cuttings":  "Шлам и очистка ствола",
}


def _rows(data, sheet, hdr_first=None):
    """
    Строки данных листа шаблона. Лист читается «как есть» (без шапки),
    затем ищется строка заголовка, после неё идут данные.
    Строка «ПРИМЕР ЗАПОЛНЕНИЯ» и всё ниже игнорируются.
    """
    import pandas as pd

    if sheet not in data.sheetnames:
        return []
    try:
        df = pd.read_excel(data.path, sheet_name=sheet, header=None)
    except Exception:
        return []

    raw = df.values.tolist()
    start = None
    for i, vals in enumerate(raw):
        first = "" if not vals else str(vals[0]).strip()
        if hdr_first and first.lower().startswith(hdr_first.lower()):
            start = i + 1
            break
    if start is None:
        start = 4                      # шапка на 4-й строке шаблона

    out = []
    for vals in raw[start:]:
        first = "" if not vals else str(vals[0]).strip()
        if first.upper().startswith("ПРИМЕР"):
            break
        if first in ("", "nan", "None"):
            continue
        out.append(vals)
    return out


NO_MOTOR = {"нет", "не применяется", "без взд", "роторное бурение",
            "не используется"}


def read_all(data):
    """Возвращает словарь уточнённых данных."""
    from hydraulics_core import to_float, warn, is_no_data

    ex = {}
    gaps = []          # где стоит «н/д»

    # -------------------------------------------------- общие сведения ----
    gen = {}
    for v in _rows(data, SHEETS["general"], "Показатель"):
        label = str(v[0]).strip()
        val = v[1] if len(v) > 1 else None
        if is_no_data(val):
            continue
        gen[label.rstrip(":").strip().lower()] = str(val).strip()
    ex["general"] = gen

    # ------------------------------------------------------- насадки ------
    nz = {}
    for v in _rows(data, SHEETS["nozzles"], "Интервал"):
        key = str(v[0]).strip()
        d = [to_float(x) for x in v[3:11]]
        d = [x for x in d if x and x > 0]
        if d:
            nz[key] = d
        else:
            tfa = to_float(v[11]) if len(v) > 11 else None
            if tfa and tfa > 0:
                nz[key] = {"tfa_in2": tfa}
            else:
                gaps.append(("Насадки долот", key, "диаметры насадок / TFA"))
    ex["nozzles"] = nz

    # ----------------------------------------------------------- ВЗД ------
    mt = {}
    for v in _rows(data, SHEETS["motor"], "Интервал"):
        key = str(v[0]).strip()
        name = str(v[1]).strip()
        if name.lower() in ("нет", "не применяется", "-", "-"):
            mt[key] = None          # явно указано: двигателя нет
            continue
        if name.lower() in ("", "nan", "none"):
            continue                # строка не заполнена - берём из конфига
        qmax = to_float(v[5]) or to_float(v[4])
        dxx = to_float(v[6])
        dld = to_float(v[7])
        if qmax is None or dxx is None:
            gaps.append(("ВЗД", key, "расход или перепад давления"))
        if qmax and dxx is not None:
            mt[key] = {"имя": name, "q_ref_лс": qmax,
                       "dp_xx_МПа": dxx, "dp_load_МПа": dld or 0.0,
                       "od_mm": to_float(v[2]), "id_mm": to_float(v[3])}
    ex["motor"] = mt

    # --------------------------------------------------- телесистема ------
    mw = {}
    for v in _rows(data, SHEETS["mwd"], "Интервал"):
        key = str(v[0]).strip()
        name = str(v[1]).strip()
        if name.lower() in ("нет", "не применяется", "-", "-"):
            mw[key] = None
            continue
        if name.lower() in ("", "nan", "none"):
            continue
        q = to_float(v[4])
        dp = to_float(v[5])
        if q and dp is not None:
            mw[key] = {"имя": name, "q_ref_лс": q, "dp_МПа": dp}
        else:
            gaps.append(("Телесистема", key, "расход или перепад давления"))
    ex["mwd"] = mw

    # -------------------------------------------------------- насосы ------
    pumps = {}
    mapping = {
        "тип насоса": "тип",
        "количество насосов в работе": "количество_рабочих",
        "число цилиндров": "цилиндров",
        "диаметр втулки": "диаметр_втулки_мм",
        "длина хода поршня": "длина_хода_мм",
        "коэффициент наполнения": "коэффициент_наполнения",
        "максимальное число ходов": "макс_ходов_в_мин",
        "максимальное давление насоса": "макс_давление_МПа",
        "максимальное давление обвязки": "макс_давление_обвязки_МПа",
        "мощность одного насоса": "мощность_на_насос_кВт",
        "кпд насоса": "КПД_насоса",
    }
    for v in _rows(data, SHEETS["pumps"], "Параметр"):
        label = str(v[0]).strip().lower()
        val = v[1] if len(v) > 1 else None
        for pat, field in mapping.items():
            if label.startswith(pat):
                if field == "тип":
                    if not is_no_data(val):
                        pumps[field] = str(val).strip()
                else:
                    fv = to_float(val)
                    if fv is not None:
                        pumps[field] = fv
                break
    if "макс_давление_обвязки_МПа" in pumps:
        pumps["макс_давление_МПа"] = min(
            pumps.get("макс_давление_МПа", 1e9),
            pumps["макс_давление_обвязки_МПа"])
    ex["pumps"] = pumps

    # ---------------------------------------------- наземная обвязка ------
    surf = []
    for v in _rows(data, SHEETS["surface"], "Элемент"):
        L = to_float(v[1])
        d = to_float(v[2])
        if L and d:
            surf.append((str(v[0]).strip(), L, d))
    ex["surface"] = surf

    # -------------------------------------------------- инклинометрия -----
    sv = []
    for v in _rows(data, SHEETS["survey"], "MD"):
        md = to_float(v[0])
        inc = to_float(v[1])
        if md is None or inc is None:
            continue
        sv.append((md, inc, to_float(v[3])))
    sv.sort(key=lambda t: t[0])
    ex["survey"] = sv

    # ------------------------------------------------------ реология ------
    rh = {}
    for v in _rows(data, SHEETS["rheology"], "Интервал"):
        key = str(v[0]).strip()
        f = {"rho": to_float(v[1]), "t600": to_float(v[2]),
             "t300": to_float(v[3]), "t200": to_float(v[4]),
             "t100": to_float(v[5]), "t6": to_float(v[6]),
             "t3": to_float(v[7])}
        if f["t600"] and f["t300"]:
            rh[key] = f
    ex["rheology"] = rh

    # ------------------------------------------------- кавернозность ------
    cav = {}
    for v in _rows(data, SHEETS["caving"], "Интервал"):
        k = to_float(v[3])
        if k and k > 0:
            cav[str(v[0]).strip()] = k
    ex["caving"] = cav

    # ------------------------------------------- градиенты давлений -------
    pr = []
    for v in _rows(data, SHEETS["pressure"], "Глубина"):
        tvd = to_float(v[0])
        if tvd is None:
            continue
        pr.append({"tvd": tvd, "pore": to_float(v[1]),
                   "frac": to_float(v[2]), "loss": to_float(v[3]),
                   "strat": str(v[4]) if len(v) > 4 else ""})
    pr.sort(key=lambda d: d["tvd"])
    ex["pressure"] = pr

    # -------------------------------------------- бурильная колонна -------
    dp = {}
    for v in _rows(data, SHEETS["drillpipe"], "Интервал"):
        key = str(v[0]).strip()
        od = to_float(v[3])
        idd = to_float(v[4])
        if od and idd:
            dp[key] = {"имя": str(v[1]).strip() or "СБТ",
                       "od_mm": od, "id_mm": idd,
                       "tj_od_mm": to_float(v[5]), "tj_id_mm": to_float(v[6])}
    ex["drillpipe"] = dp

    # ---------------------------------------------------------- шлам ------
    ct = {}
    for v in _rows(data, SHEETS["cuttings"], "Интервал"):
        key = str(v[0]).strip()
        row = {"d_mm": to_float(v[1]), "rho": to_float(v[2]),
               "c_max": to_float(v[3]), "v_min": to_float(v[4])}
        if any(x is not None for x in row.values()):
            ct[key] = row
    ex["cuttings"] = ct

    # --------------------------------------------------- температура ------
    tp = []
    for v in _rows(data, SHEETS["temp"], "Глубина"):
        tvd = to_float(v[0])
        t = to_float(v[1])
        if tvd is not None and t is not None:
            tp.append((tvd, t))
    ex["temperature"] = sorted(tp)
    ex["_gaps"] = gaps

    # ------------------------------------------------ что подхватилось ----
    found = [SHEETS[k] for k, v in
             [("nozzles", nz), ("motor", mt), ("mwd", mw), ("pumps", pumps),
              ("surface", surf), ("survey", sv), ("rheology", rh),
              ("caving", cav), ("pressure", pr), ("drillpipe", dp),
              ("cuttings", ct), ("temp", tp)] if v]
    ex["_found"] = found
    return ex


def resolve(ex, group, key, section, cfg_dict, default=None):
    """
    Значение параметра: сначала из Excel (по ключу интервала, затем по
    секции), затем из конфигурации, затем значение по умолчанию.
    """
    src = ex.get(group, {}) if ex else {}
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
