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
 ЯДРО РАСЧЁТА: чтение данных, траектория, геометрия, гидравлика
==========================================================================
 Единицы внутри модуля - СИ (м, м3/с, Па, кг/м3, Па·с).
 На вход/выход - привычные промысловые (мм, л/с, МПа, г/см3).
==========================================================================
"""

import math
import re
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import hydraulics_config as CFG

warnings.filterwarnings("ignore")

# ==========================================================================
#  0. МЕЛКИЕ УТИЛИТЫ
# ==========================================================================

WARNINGS = []          # сюда собираются все замечания к исходным данным

# папки, в которых ищется файл исходных данных
DATA_DIRS = ("", "data", "templates", "examples", "..")


def find_input_file(preferred=None, prefer_template=False):
    """
    Путь к файлу исходных данных. Сначала проверяется указанное имя,
    затем подходящие файлы в стандартных папках рядом со скриптом.
    """
    import os
    if preferred and os.path.exists(preferred):
        return preferred
    here = os.path.dirname(os.path.abspath(__file__))
    if preferred:
        alt = os.path.join(here, os.path.basename(preferred))
        if os.path.exists(alt):
            return alt
    found = []
    for sub in DATA_DIRS:
        d = os.path.normpath(os.path.join(here, sub))
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if (f.lower().endswith((".xlsx", ".xlsm"))
                    and not f.startswith("~$")):
                found.append(os.path.join(d, f))
    if not found:
        return None
    found.sort(key=lambda f: (("шаблон" in os.path.basename(f).lower())
                              != prefer_template, f))
    return found[0]


def warn(msg):
    if msg not in WARNINGS:
        WARNINGS.append(msg)


NO_DATA_TOKENS = {
    "", "-", "\u2013", "\u2014", "н/д", "нд", "н.д.", "н/д.", "нет данных",
    "нет", "не задано", "не известно", "неизвестно", "?", "n/a", "na",
    "none", "nan", "-\u2013", "\u2013\u2013",
    "no data", "unknown", "tbd", "t.b.d.", "not available",
    "pas de donnees", "inconnu", "non disponible", "nd",
}


def is_no_data(x):
    """True, если ячейка пустая или содержит пометку «нет данных»."""
    if x is None:
        return True
    if isinstance(x, float) and math.isnan(x):
        return True
    if isinstance(x, (int, float)):
        return False
    return _is_no_data(str(x))


def _is_no_data(s):
    t = str(s).strip().lower().replace("\xa0", " ")
    t = " ".join(t.split())
    return t in NO_DATA_TOKENS


def to_float(x, default=None):
    """Аккуратное приведение ячейки Excel к числу."""
    if x is None:
        return default
    if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x)):
        return float(x)
    s = str(x).strip().replace(",", ".").replace("\xa0", " ")
    if _is_no_data(s):
        return default
    if _is_no_data(s):
        return default
    m = re.findall(r"-?\d+\.?\d*", s)
    return float(m[0]) if m else default


def parse_range(x, mode="max"):
    """
    '50-55' -> 55 (max) / 50 (min) / 52.5 (mean).
    Одиночное число возвращается как есть.
    """
    if x is None:
        return None
    if isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x)):
        return float(x)
    if _is_no_data(x):
        return None
    s = str(x).replace(",", ".").replace("\u2013", "-").replace("\u2014", "-")
    nums = [float(v) for v in re.findall(r"\d+\.?\d*", s)]
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    if mode == "min":
        return min(nums)
    if mode == "mean":
        return sum(nums) / len(nums)
    return max(nums)


# ---------------------------- ЕДИНИЦЫ ДАВЛЕНИЯ ----------------------------
# коэффициент перевода из Па и число знаков после запятой
PRESSURE_UNITS = {
    "МПа":     (1.0e6,     2, 3),
    "атм":     (98066.5,   1, 3),
    "кгс/см2": (98066.5,   1, 3),
    "бар":     (1.0e5,     1, 3),
    "psi":     (6894.757,  0, 2),
}


PRESSURE_NAMES = {
    "МПа": ("МПа", "MPa", "MPa"),
    "атм": ("атм", "atm", "atm"),
    "кгс/см2": ("кгс/см²", "kgf/cm²", "kgf/cm²"),
    "бар": ("бар", "bar", "bar"),
    "psi": ("psi", "psi", "psi"),
}


def punit_key():
    """Внутренний код единицы давления."""
    u = getattr(CFG, "PRESSURE_UNIT", "МПа")
    return u if u in PRESSURE_UNITS else "МПа"


def punit():
    """Название единицы давления на языке отчёта."""
    from hydraulics_lang import LANGS, lang
    names = PRESSURE_NAMES[punit_key()]
    i = LANGS.index(lang())
    return names[i] if i < len(names) else names[0]


def P(pa):
    """Перевод давления из Па в текущую единицу отчёта."""
    if pa is None:
        return None
    return pa / PRESSURE_UNITS[punit_key()][0]


def pnd(fine=False):
    """Число знаков после запятой для давления."""
    _, nd, nd_fine = PRESSURE_UNITS[punit_key()]
    return nd_fine if fine else nd


def pfmt(pa, fine=False, unit=False):
    """Форматирование давления: значение (и, при желании, единица)."""
    v = P(pa)
    if v is None:
        return "-"
    txt = f"{v:.{pnd(fine)}f}"
    return f"{txt} {punit()}" if unit else txt


def pgrad(pa_per_m):
    """Градиент давления в единицах отчёта на 100 м."""
    return P(pa_per_m) * 100.0


def fmt(v, nd=2, dash="-"):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return dash
    return f"{v:,.{nd}f}".replace(",", " ")


# ==========================================================================
#  1. ЧТЕНИЕ ИСХОДНЫХ ДАННЫХ
# ==========================================================================

@dataclass
class Casing:
    name: str
    od_mm: float
    md_m: float
    tvd_m: float
    wall_mm: float
    top_m: float = None      # глубина подвески (для хвостовика)

    @property
    def id_mm(self):
        return self.od_mm - 2.0 * self.wall_mm


@dataclass
class BhaItem:
    name: str
    length_m: float
    od_mm: float
    id_mm: float or None
    kind: str = "pipe"      # pipe | bit | motor | mwd


@dataclass
class Interval:
    """Один расчётный интервал долотной программы."""
    key: str                # 'Кондуктор 1'
    section: str            # 'Кондуктор'  (как в листе «Параметры раствора»)
    md_from: float
    md_to: float
    rop: float              # МСП, м/ч
    drive: str
    q_lps: float            # рабочий расход, л/с
    q_raw: str
    bit_mm: float
    rho: float              # г/см3
    pv: float               # сПз
    yp: float               # фунт/100фут2


class InputData:
    def __init__(self, path):
        self.path = path
        xl = pd.ExcelFile(path)
        self.sheetnames = xl.sheet_names

        # -------- сначала пробуем шаблон NTS-HYDRA --------
        import hydraulics_input as HI
        if HI.is_template(self.sheetnames):
            self.format = "template"
            self._init_from_template(HI.read_template(path, self.sheetnames))
            return

        # -------- иначе читаем исходный (устаревший) формат --------
        self.format = "legacy"
        self.sheets = {n: xl.parse(n) for n in xl.sheet_names}
        self.casings = self._read_casings()
        self.survey = self._read_survey()
        self.bitprog = self._read_bitprogram()
        self.mud = self._read_mud()
        self.strat = self._read_strat()
        self.bha_sheets = {n: v for n, v in
                           ((n, self._read_bha(n)) for n in self.sheetnames
                            if n.strip().upper().startswith("КНБК")) if v}

        # уточнённые данные из листов-шаблонов (все необязательны)
        try:
            import hydraulics_extra
            self.extra = hydraulics_extra.read_all(self)
        except Exception as e:
            self.extra = {}
            warn(f"Не удалось прочитать дополнительные листы: {e}")

        self.general = (self.extra or {}).get("general", {}) or {}

        if self.extra.get("survey") and len(self.extra["survey"]) > len(self.survey):
            self.survey = list(self.extra["survey"])
            self.survey_full = True
        else:
            self.survey_full = False

        self._check_completeness()

    # ---------------------------------------------------- конструкция ----
    def _read_casings(self):
        df = self.sheets["Конструкция скважины"]
        out = []
        for _, r in df.iterrows():
            name = str(r.iloc[0]).strip()
            if name in ("", "nan"):
                continue
            od = to_float(r.iloc[1])
            depth = str(r.iloc[2])
            nums = [float(v) for v in re.findall(r"\d+\.?\d*", depth.replace(",", "."))]
            md = nums[0] if nums else None
            tvd = nums[1] if len(nums) > 1 else md
            wall = to_float(r.iloc[3], 0.0)
            if od and md:
                out.append(Casing(name, od, md, tvd, wall))
        out.sort(key=lambda c: c.md_m)
        return out

    # -------------------------------------------------------- профиль ----
    def _read_survey(self):
        df = self.sheets["Профиль скважины"]
        rows = []
        for _, r in df.iterrows():
            md = to_float(r.iloc[0])
            inc = to_float(r.iloc[1], 0.0)
            tvd = to_float(r.iloc[2])
            if md is None:
                continue
            rows.append((md, inc, tvd))
        rows.sort(key=lambda t: t[0])
        return rows

    # ------------------------------------------------ долотная программа -
    def _read_bitprogram(self):
        df = self.sheets["Долотная программа"]
        out = []
        for _, r in df.iterrows():
            sec = str(r.iloc[0]).strip()
            if sec in ("", "nan"):
                continue
            out.append({
                "секция": sec,
                "от": to_float(r.iloc[1]),
                "до": to_float(r.iloc[2]),
                "мсп": to_float(r.iloc[3], 10.0),
                "привод": str(r.iloc[4]).strip(),
                "расход_raw": str(r.iloc[5]).strip(),
            })
        return out

    # ------------------------------------------------- буровой раствор ---
    def _read_mud(self):
        df = self.sheets["Параметры бурового раствора"]
        cols = [str(c).strip() for c in df.columns]
        data = {}
        for j, c in enumerate(cols[1:], start=1):
            col = {}
            for _, r in df.iterrows():
                key = str(r.iloc[0]).strip()
                col[key] = r.iloc[j]
            data[c] = col
        return data

    # --------------------------------------------------- стратиграфия ---
    def _read_strat(self):
        key = [n for n in self.sheetnames if n.startswith("Стратиграфия")]
        if not key:
            return []
        df = self.sheets[key[0]]
        out = []
        for _, r in df.iterrows():
            nm = str(r.iloc[0]).strip()
            if nm in ("", "nan"):
                continue
            rho_txt = str(r.iloc[4])
            nums = [float(v) for v in re.findall(r"\d+\.?\d*", rho_txt.replace(",", "."))]
            rho = sum(nums) / len(nums) if nums else CFG.DEFAULT_CUTTINGS_DENSITY
            out.append({
                "название": nm,
                "от": to_float(r.iloc[1], 0.0),
                "до": to_float(r.iloc[2], 0.0),
                "литология": str(r.iloc[3]),
                "ро": rho,
            })
        return out

    # ---------------------------------------------------------- КНБК ----
    def _read_bha(self, sheet):
        """
        Читает лист КНБК. Работает и с «простым» листом (шапка в 1-й строке),
        и с листом шаблона (заголовок, пояснение, шапка в 4-й строке).
        """
        raw = pd.read_excel(self.path, sheet_name=sheet, header=None
                            ).values.tolist()
        start = 1
        for i, vals in enumerate(raw):
            first = "" if not vals else str(vals[0]).strip().lower()
            if first.startswith("наименование"):
                start = i + 1
                break

        items = []
        for vals in raw[start:]:
            nm = "" if not vals else str(vals[0]).strip()
            if nm.upper().startswith("ПРИМЕР"):
                break
            if nm in ("", "nan", "None"):
                continue
            L = to_float(vals[1] if len(vals) > 1 else None, 0.0)
            od = to_float(vals[2] if len(vals) > 2 else None)
            idd = to_float(vals[3] if len(vals) > 3 else None)
            if od is None:
                if L:      # строка заполнена частично - это ошибка
                    warn(f"Лист «{sheet}», элемент «{nm}»: не указан "
                         f"наружный диаметр - строка пропущена.")
                continue   # пустая строка-подсказка шаблона
            note = str(vals[4]) if len(vals) > 4 else ""
            items.append(BhaItem(nm, L or 0.0, od, idd,
                                 classify_element(nm, note, not items)))
        return items

    # ---------------------------------------------- контроль полноты ----
    def _check_completeness(self):
        for c in self.casings:
            if not c.wall_mm:
                warn(f"Не задана толщина стенки колонны «{c.name}» - "
                     f"внутренний диаметр принят условно.")
        if len(self.survey) < 6 and not getattr(self, "survey_full", False):
            warn("Профиль скважины задан всего "
                 f"{len(self.survey)} точками. Для корректного пересчёта MD→TVD "
                 "и расчёта потерь в наклонном стволе нужен полный инклинометрический "
                 "файл (MD / зенит / азимут через 10-30 м).")
        ex = getattr(self, "extra", {}) or {}

        # ячейки, помеченные «н/д»
        gaps = ex.get("_gaps") or []
        if gaps:
            by_sheet = {}
            for sheet, key, what in gaps:
                by_sheet.setdefault((sheet, what), []).append(key)
            for (sheet, what), keys in by_sheet.items():
                warn(f"Лист «{sheet}»: не заданы {what} для интервалов "
                     f"{', '.join(keys)} (пусто или «н/д»). Приняты "
                     f"значения из hydraulics_config.py.")
        if not ex.get("rheology"):
            for sec, col in self.mud.items():
                if to_float(col.get("Пластическая вязкость, сПз")) is None:
                    warn(f"Нет реологии для секции «{sec}» - принята по "
                         f"умолчанию PV={CFG.DEFAULT_RHEOLOGY['pv_cP']} сПз, "
                         f"YP={CFG.DEFAULT_RHEOLOGY['yp_lb100ft2']} "
                         f"фунт/100фут².")
        if not ex.get("nozzles"):
            warn("Нет данных по насадкам долот (лист «Насадки долот») - "
                 "значения взяты из блока NOZZLES в hydraulics_config.py.")
        if not ex.get("motor"):
            warn("Нет паспортных перепадов давления на ВЗД (лист «ВЗД») - "
                 "значения взяты из блока MOTOR в hydraulics_config.py.")
        if not ex.get("mwd"):
            warn("Нет перепада давления на телесистеме (лист «Телесистема») - "
                 "значения взяты из блока MWD в hydraulics_config.py.")
        if not ex.get("pumps"):
            warn("Нет параметров буровых насосов (лист «Буровые насосы») - "
                 "заданы в блоке PUMPS в hydraulics_config.py.")
        if not ex.get("surface"):
            warn("Нет схемы наземной обвязки (лист «Наземная обвязка») - "
                 "принята эквивалентная длина из hydraulics_config.py.")
        if not ex.get("pressure"):
            warn("Нет градиентов порового давления и давления гидроразрыва "
                 "(лист «Градиенты давлений») - соответствие ЭЦП «окну "
                 "бурения» не проверяется.")


def _init_from_template(self, ex):
    """Заполнение полей из шаблона NTS-HYDRA."""
    self.sheets = {}
    self.extra = ex
    self.general = ex.get("general", {}) or {}

    self.casings = [Casing(c["name"], c["od_mm"], c["md_m"], c["tvd_m"],
                           c["wall_mm"], c.get("top_m"))
                    for c in ex["casings"]]
    if not self.casings:
        warn("Не заполнен лист «02 Конструкция» - без него расчёт невозможен.")
    if not ex["intervals"]:
        warn("Не заполнен лист «05 Интервалы бурения» - "
             "без него расчёт невозможен.")
    self.survey = list(ex["survey"])
    self.survey_full = len(self.survey) >= 6
    self.strat = list(ex["strat"])

    # реология и кавернозность - под ключи, которые ждёт решатель
    ex["rheology"] = ex.get("mud", {})
    ex["caving"] = {i["key"]: i["caving"] for i in ex["intervals"]
                    if i.get("caving")}
    ex["rpm"] = {i["key"]: i["rpm"] for i in ex["intervals"]
                 if i.get("rpm") is not None}

    # КНБК: словарь «интервал -> элементы»
    self.bha_sheets = {}
    for key, items in (ex.get("bha") or {}).items():
        self.bha_sheets[key] = [
            BhaItem(it["name"], it["length_m"], it["od_mm"], it["id_mm"],
                    classify_element(it["name"], it.get("note", ""), i == 0))
            for i, it in enumerate(items)]

    self.bitprog = []
    for i in ex["intervals"]:
        self.bitprog.append({
            "секция": i["key"], "от": i["md_from"], "до": i["md_to"],
            "мсп": i["rop"], "привод": i["drive"],
            "расход_raw": i["q_raw"], "bit_mm": i["bit_mm"],
        })
    self.mud = {}
    self._check_template(ex)


def _check_template(self, ex):
    """Замечания к шаблону: чего не хватает."""
    by = {}
    for sheet, key, what in ex.get("_gaps", []):
        by.setdefault((sheet, what), []).append(key)
    for (sheet, what), keys in by.items():
        warn(f"Лист «{sheet}»: не заданы {what} для интервалов "
             f"{', '.join(keys)} (пусто или «н/д»). Приняты значения "
             f"из hydraulics_config.py.")
    if len(self.survey) < 6:
        warn(f"Инклинометрия задана {len(self.survey)} точками. "
             f"Для корректного пересчёта MD→TVD нужен полный замер "
             f"с шагом 10-30 м (лист «03 Инклинометрия»).")
    if not ex.get("pressure_md"):
        warn("Не заданы поровое давление и давление ГРП "
             "(лист «04 Разрез и давления») - соответствие ЭЦП «окну "
             "бурения» не проверяется.")
    if not ex.get("surface"):
        warn("Не заполнена наземная обвязка (лист «13 Наземная обвязка») - "
             "принята эквивалентная длина из hydraulics_config.py.")
    if not ex.get("pumps"):
        warn("Не заполнены параметры насосов (лист «12 Буровые насосы») - "
             "приняты из hydraulics_config.py.")
    for i in ex["intervals"]:
        if i["key"] not in (ex.get("bha") or {}):
            warn(f"Для интервала «{i['key']}» не задана КНБК "
                 f"(лист «10 КНБК») - использован ориентировочный шаблон.")


InputData._init_from_template = _init_from_template
InputData._check_template = _check_template


def classify_element(name, note="", first=False):
    """
    Тип элемента КНБК. Учитывается и наименование, и примечание:
    долото часто записывают как «295.3 PDC» без слова «долото».
    Первый элемент компоновки считается долотом по определению.
    """
    n = (str(name) + " " + str(note)).lower()
    if first:
        return "bit"
    if ("долот" in n or "бит" in n or "pdc" in n or "шарошеч" in n
            or "бурильная головка" in n or "бур. головка" in n):
        return "bit"
    if ("взд" in n or "двигател" in n or "дру" in n or "pdm" in n
            or "дшотр" in n or "винтовой заб" in n):
        return "motor"
    if ("калибратор" in n or "стабилизатор" in n or "центратор" in n
            or n.startswith("кс-") or " кс-" in n or n.startswith("жц")
            or " жц" in n):
        return "stab"
    if "mwd" in n or "lwd" in n or "телесистем" in n:
        return "mwd"
    return "pipe"


# ==========================================================================
#  2. ТРАЕКТОРИЯ: MD -> TVD и MD -> зенитный угол
# ==========================================================================

def _pchip(x, y, xq):
    """
    Монотонная кубическая интерполяция (Fritsch-Carlson).
    Своя реализация, чтобы не тянуть scipy.
    Возвращает (значения, производные) в точках xq.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    n = len(x)
    h = np.diff(x)
    d = np.diff(y) / h

    m = np.zeros(n)
    m[0] = d[0]
    m[-1] = d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1 = 2 * h[i] + h[i - 1]
            w2 = h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    for i in range(n - 1):
        if abs(d[i]) < 1e-12:
            m[i] = m[i + 1] = 0.0
        else:
            a, b = m[i] / d[i], m[i + 1] / d[i]
            s = a * a + b * b
            if s > 9.0:
                t = 3.0 / math.sqrt(s)
                m[i] = t * a * d[i]
                m[i + 1] = t * b * d[i]

    xq = np.asarray(xq, float)
    idx = np.clip(np.searchsorted(x, xq) - 1, 0, n - 2)
    hh = h[idx]
    t = (xq - x[idx]) / hh
    t2, t3 = t * t, t * t * t
    h00 = 2 * t3 - 3 * t2 + 1
    h10 = t3 - 2 * t2 + t
    h01 = -2 * t3 + 3 * t2
    h11 = t3 - t2
    val = (h00 * y[idx] + h10 * hh * m[idx] +
           h01 * y[idx + 1] + h11 * hh * m[idx + 1])
    d00 = (6 * t2 - 6 * t) / hh
    d10 = 3 * t2 - 4 * t + 1
    d01 = (-6 * t2 + 6 * t) / hh
    d11 = 3 * t2 - 2 * t
    der = (d00 * y[idx] + d10 * m[idx] +
           d01 * y[idx + 1] + d11 * m[idx + 1])
    return val, der


def _hold_build_profile(L, a0, a1, dtvd):
    """
    Восстанавливает зенитный угол на участке между двумя замерами так,
    чтобы ОДНОВРЕМЕННО выполнялись: длина по стволу L, углы на концах
    (a0, a1) и приращение по вертикали dtvd.

    Принята типовая схема: сначала участок стабилизации длиной Lh
    (угол a0), затем участок равномерного набора/падения до a1.
    Возвращает (Lh, a1_факт, признак_коррекции).
    """
    a0 = math.radians(a0)
    a1 = math.radians(a1)
    if abs(a1 - a0) < 1e-6:
        return L, math.degrees(a0), False

    F = (math.sin(a1) - math.sin(a0)) / (a1 - a0)   # средний cos на наборе
    den = math.cos(a0) - F
    if abs(den) > 1e-9:
        Lh = (dtvd - L * F) / den
        if -1e-6 <= Lh <= L + 1e-6:
            return min(max(Lh, 0.0), L), math.degrees(a1), False

    # решение не найдено -> подбираем конечный угол под фактический TVD
    def tvd_of(af):
        if abs(af - a0) < 1e-9:
            return L * math.cos(a0)
        return L * (math.sin(af) - math.sin(a0)) / (af - a0)

    lo, hi = 0.0, math.radians(120.0)
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if tvd_of(mid) > dtvd:
            lo = mid
        else:
            hi = mid
    return 0.0, math.degrees(0.5 * (lo + hi)), True


class Trajectory:
    """
    Траектория ствола, восстановленная по редким замерам.

    На каждом участке между замерами подбирается схема
    «стабилизация + равномерный набор», обеспечивающая точное совпадение
    и глубины по вертикали, и зенитных углов на концах участка.
    Горизонтальное смещение получается интегрированием sin(alpha).
    """

    def __init__(self, survey, step=1.0):
        self.stations = survey
        st_md = np.array([s[0] for s in survey], float)
        st_inc = np.array([s[1] for s in survey], float)
        has_tvd = all(s[2] is not None for s in survey)
        if has_tvd:
            st_tvd = np.array([s[2] for s in survey], float)
        else:
            # TVD не задана - восстанавливаем по зенитным углам
            st_tvd = np.zeros(len(st_md))
            for k in range(1, len(st_md)):
                a = math.radians(0.5 * (st_inc[k] + st_inc[k - 1]))
                st_tvd[k] = st_tvd[k - 1] + (st_md[k] - st_md[k - 1]) * math.cos(a)
        self.tvd_given = has_tvd

        grid = np.arange(st_md[0], st_md[-1], step)
        self.md = np.unique(np.round(
            np.concatenate([grid, st_md, [st_md[-1]]]), 4))

        inc = np.zeros_like(self.md)
        self.segments = []
        for k in range(1, len(st_md)):
            L = st_md[k] - st_md[k - 1]
            dtvd = st_tvd[k] - st_tvd[k - 1]
            if not has_tvd or L <= 35.0:
                Lh, a1f, corrected = 0.0, st_inc[k], False
            else:
                Lh, a1f, corrected = _hold_build_profile(L, st_inc[k - 1],
                                                         st_inc[k], dtvd)
            if corrected:
                warn(f"Интервал {st_md[k-1]:.0f}-{st_md[k]:.0f} м: замеренный "
                     f"зенитный угол ({st_inc[k]:.1f}°) и отметка TVD "
                     f"({st_tvd[k]:.1f} м) противоречат друг другу. "
                     f"Для расчёта принят угол {a1f:.1f}°. "
                     f"Проверьте исходные данные.")
            dls = (abs(a1f - st_inc[k - 1]) / max(L - Lh, 1e-6) * 30.0
                   if L - Lh > 1e-6 else 0.0)
            self.segments.append(dict(md0=st_md[k - 1], md1=st_md[k],
                                      hold=Lh, a0=st_inc[k - 1], a1=a1f,
                                      dls=dls))
            sel = (self.md >= st_md[k - 1] - 1e-9) & (self.md <= st_md[k] + 1e-9)
            x = self.md[sel] - st_md[k - 1]
            lb = max(L - Lh, 1e-9)
            inc[sel] = np.where(x <= Lh, st_inc[k - 1],
                                st_inc[k - 1] + (a1f - st_inc[k - 1]) *
                                np.clip((x - Lh) / lb, 0, 1))

        self.inc = inc
        tvd = np.zeros_like(self.md)
        hd = np.zeros_like(self.md)
        tvd[0] = st_tvd[0]
        for i in range(1, len(self.md)):
            dmd = self.md[i] - self.md[i - 1]
            a = math.radians(0.5 * (self.inc[i] + self.inc[i - 1]))
            tvd[i] = tvd[i - 1] + dmd * math.cos(a)
            hd[i] = hd[i - 1] + dmd * math.sin(a)
        self.tvd = tvd
        self.hd = hd
        self.md_max = st_md[-1]

        for md_s, tvd_s in (zip(st_md, st_tvd) if has_tvd else []):
            if abs(self.tvd_at(md_s) - tvd_s) > 1.5:
                warn(f"Расчётная TVD на {md_s:.0f} м MD отличается от заданной "
                     f"на {abs(self.tvd_at(md_s) - tvd_s):.1f} м.")

    def tvd_at(self, md):
        md = min(max(md, self.md[0]), self.md[-1])
        return float(np.interp(md, self.md, self.tvd))

    def inc_at(self, md):
        md = min(max(md, self.md[0]), self.md[-1])
        return float(np.interp(md, self.md, self.inc))

    def hd_at(self, md):
        md = min(max(md, self.md[0]), self.md[-1])
        return float(np.interp(md, self.md, self.hd))


# ==========================================================================
#  3. РЕОЛОГИЯ
# ==========================================================================

from hydraulics_rheology import (                      # noqa: E402
    Rheology, DIAL_TO_PA, SHEAR, pipe_flow, annulus_flow,
    friction_factor as _ff, eccentricity_at, eccentricity_factor,
    gel_break_pressure,
)


class Fluid(Rheology):
    """
    Буровой раствор. Тонкая обёртка над Rheology: сохраняет прежние имена
    полей, чтобы не переписывать вызывающий код.
    """

    def __init__(self, rho_gcm3, pv_cP=None, yp_lb100=None, name="",
                 fann=None, model=None):
        super().__init__(rho_gcm3, fann=fann, pv_cP=pv_cP,
                         yp_lb100=yp_lb100, model=model, name=name)
        self.fann_measured = self.measured

    def pl(self, geometry):
        """Совместимость: (n, K) текущей модели."""
        return self.n, self.K


# ==========================================================================
#  4. ПОТЕРИ ДАВЛЕНИЯ НА ЭЛЕМЕНТАРНОМ УЧАСТКЕ
# ==========================================================================

def _friction_factor(Re, n, geometry="pipe"):
    """Совместимость со старым интерфейсом."""
    return _ff(Re, n, geometry)


def pipe_pressure_gradient(Q, d_in, fluid):
    r = pipe_flow(Q, d_in, fluid)
    return r.dpdl, r.V, r.Re, r.mode


def annulus_pressure_gradient(Q, d_out, d_in, fluid, ecc=0.0, rpm=0.0):
    r = annulus_flow(Q, d_out, d_in, fluid, ecc, rpm)
    return r.dpdl, r.V, r.Re, r.mode


def bingham_pipe_gradient(Q, d_in, fluid):
    """Проверочный расчёт по модели Бингама (аналитическое решение)."""
    A = math.pi * d_in ** 2 / 4.0
    V = Q / A
    mu, tau0 = fluid.mu_p, fluid.tau_y_bingham
    Re = fluid.rho * V * d_in / max(mu, 1e-9)
    if Re < 2100.0:
        return (32.0 * mu * V / d_in ** 2 + 16.0 * tau0 / (3.0 * d_in),
                V, Re, "ламинарный")
    f = 0.079 / (Re ** 0.25)
    return 2.0 * f * fluid.rho * V * V / d_in, V, Re, "турбулентный"


def bingham_annulus_gradient(Q, d_out, d_in, fluid):
    A = math.pi * (d_out ** 2 - d_in ** 2) / 4.0
    V = Q / A
    dh = d_out - d_in
    mu, tau0 = fluid.mu_p, fluid.tau_y_bingham
    Re = fluid.rho * V * dh / max(mu, 1e-9)
    if Re < 2100.0:
        return (48.0 * mu * V / dh ** 2 + 6.0 * tau0 / dh,
                V, Re, "ламинарный")
    f = 0.079 / (Re ** 0.25)
    return 2.0 * f * fluid.rho * V * V / dh, V, Re, "турбулентный"


def grad_pipe(Q, d_in, fluid):
    return pipe_pressure_gradient(Q, d_in, fluid)


def grad_ann(Q, d_out, d_in, fluid, ecc=0.0, rpm=0.0):
    return annulus_pressure_gradient(Q, d_out, d_in, fluid, ecc, rpm)


# ==========================================================================
#  5. ДОЛОТО
# ==========================================================================

def nozzle_area(nozzles_32nd):
    """Суммарная площадь насадок, м2. Вход - список в 1/32 дюйма."""
    A = 0.0
    for d32 in nozzles_32nd:
        d_m = d32 / 32.0 * 0.0254
        A += math.pi * d_m ** 2 / 4.0
    return A


def bit_hydraulics(Q, nozzles_32nd, rho, bit_d_m):
    """Возвращает словарь показателей работы долота."""
    An = nozzle_area(nozzles_32nd)
    if An <= 0:
        return None
    dp = rho * Q ** 2 / (2.0 * CFG.CD_NOZZLE ** 2 * An ** 2)      # Па
    v_noz = Q / An                                               # м/с
    power = dp * Q                                               # Вт
    A_bit = math.pi * bit_d_m ** 2 / 4.0                         # м2
    hsi = power / (A_bit * 1e4)                                  # Вт/см2
    impact = CFG.CD_NOZZLE * Q * math.sqrt(2.0 * rho * dp)       # Н
    tfa_in2 = An / 0.0254 ** 2
    return {
        "dp_Pa": dp, "v_noz": v_noz, "power_W": power,
        "hsi_kW_cm2": hsi / 1000.0,
        "hsi_hp_in2": hsi / 1000.0 / 0.11559,
        "impact_N": impact,
        "tfa_in2": tfa_in2, "A_noz_mm2": An * 1e6,
    }


# ==========================================================================
#  6. ВЫНОС ШЛАМА
# ==========================================================================

def slip_velocity(d_part_m, rho_s, rho_f, fluid, V_ann, dh):
    """
    Скорость осаждения частицы шлама (итерационно, через Cd).
    Эффективная вязкость берётся из степенной модели для затрубья.
    """
    n, K = fluid.pl("annulus")
    gamma = 12.0 * max(V_ann, 0.05) / max(dh, 1e-3)
    mu_eff = K * (((2.0 * n + 1.0) / (3.0 * n)) ** n) * (gamma ** (n - 1.0))
    mu_eff = min(max(mu_eff, 1e-3), 5.0)

    vs = 0.15
    for _ in range(60):
        Re_p = rho_f * vs * d_part_m / mu_eff
        Re_p = max(Re_p, 1e-4)
        if Re_p < 1.0:
            Cd = 24.0 / Re_p
        elif Re_p < 1000.0:
            Cd = 24.0 / Re_p * (1.0 + 0.15 * Re_p ** 0.687)
        else:
            Cd = 0.44
        vs_new = math.sqrt(4.0 * CFG.G * d_part_m * (rho_s - rho_f) /
                           (3.0 * Cd * rho_f))
        if abs(vs_new - vs) < 1e-5:
            vs = vs_new
            break
        vs = 0.5 * vs + 0.5 * vs_new
    return vs, mu_eff


def cuttings_concentration(rop_mh, bit_d_m, A_ann, V_ann, V_slip, inc_deg):
    """Объёмная концентрация шлама в затрубье, доли ед."""
    q_cut = rop_mh / 3600.0 * math.pi * bit_d_m ** 2 / 4.0     # м3/с
    v_trans = V_ann - V_slip * math.cos(math.radians(inc_deg))
    if v_trans <= 0.02:
        return 1.0, v_trans
    c = q_cut / (A_ann * v_trans)
    return min(c, 1.0), v_trans
