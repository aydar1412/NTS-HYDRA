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
 ВИЗУАЛИЗАЦИЯ: конструкция скважины, профиль, стратиграфия,
 схема КНБК, эпюры давлений, скоростей, ЭЦП, таблицы
==========================================================================
"""

import math
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle, Polygon, FancyBboxPatch
from matplotlib.lines import Line2D
import numpy as np

import hydraulics_config as CFG
from hydraulics_core import fmt, P, pfmt, pgrad, punit, pnd
from hydraulics_lang import t, lang

C = CFG.COLORS
def model_name(m):
    return {"herschel_bulkley": t("m_hb"), "power_law": t("m_pl"),
            "bingham": t("m_bg")}.get(m, m or t("dash"))


class _Models(dict):
    def get(self, k, default=None):
        return model_name(k) if k else (default or t("dash"))


MODEL_NAMES = _Models()
WELL_CAPTION = ""      # заполняется из main.py после чтения данных
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.edgecolor": "#A8A8AA",
    "axes.labelcolor": C["text"],
    "text.color": C["text"],
    "xtick.color": C["text"],
    "ytick.color": C["text"],
    "axes.grid": True,
    "grid.color": C["grid"],
    "grid.linewidth": 0.6,
    "figure.facecolor": "white",
})

A4 = (11.69, 8.27)      # альбомная A4, дюймы
A4P = (8.27, 11.69)     # книжная

_LOGO_CACHE = {}


def load_logo(name=None):
    """Логотип из файла рядом со скриптом. Если нет - None."""
    import os
    fn = name or CFG.APP_LOGO
    if fn in _LOGO_CACHE:
        return _LOGO_CACHE[fn]
    img = None
    here = os.path.dirname(os.path.abspath(__file__))
    roots = (here, os.path.join(here, ".."), os.getcwd())
    subdirs = ("", "assets", "logo", "img")
    for base in roots:
        for sub in subdirs:
            path = os.path.normpath(os.path.join(base, sub, fn))
            if os.path.exists(path):
                try:
                    img = plt.imread(path)
                except Exception:
                    img = None
                break
        if img is not None:
            break
    _LOGO_CACHE[fn] = img
    return img


def well_caption(data=None):
    """Строка реквизитов для колонтитула."""
    g = getattr(data, "general", {}) if data is not None else {}
    parts = []
    for k in ("месторождение", "куст", "скважина"):
        v = g.get(k)
        if v:
            parts.append(v if k == "месторождение" else f"{k} {v}")
    if not parts:
        return f"{CFG.FIELD_NAME}, {CFG.WELL_NAME}"
    return ", ".join(parts)


# ==========================================================================
#  ОБЩИЕ ЭЛЕМЕНТЫ
# ==========================================================================

def page(figsize=A4):
    fig = plt.figure(figsize=figsize)
    return fig


def header(fig, title, subtitle=""):
    fig.text(0.035, 0.962, title, fontsize=15, fontweight="bold",
             color=C["text"], va="top")
    if subtitle:
        fig.text(0.035, 0.925, subtitle, fontsize=9, color="#6C6C6E", va="top")
    fig.add_artist(Line2D([0.035, 0.965], [0.905, 0.905],
                          color=C["accent"], lw=1.4))
    # фирменная отбивка слева от заголовка (не пересекается с блоками ниже)
    fig.add_artist(Line2D([0.0225, 0.0225], [0.918, 0.978],
                          color=C["yellow"], lw=5.0, solid_capstyle="butt"))


def footer(fig, well, page_no, mark=True):
    fig.add_artist(Line2D([0.035, 0.965], [0.042, 0.042],
                          color=C["grid"], lw=0.8))
    fig.text(0.035, 0.020, well, fontsize=7, color="#8A8A8C")
    fig.text(0.5, 0.018,
             f"{CFG.APP_NAME}  {CFG.APP_VERSION}   ·   {CFG.APP_AUTHOR}",
             fontsize=7, color="#8A8A8C", ha="center")
    fig.text(0.965, 0.020, f'{t("page")} {page_no}', fontsize=7,
             color="#8A8A8C", ha="right")
    img = load_logo(getattr(CFG, "APP_MARK", "nts_hydra_mark.png")) \
        if mark else None
    if img is not None:
        ax = fig.add_axes([0.912, 0.925, 0.055, 0.062], zorder=5)
        ax.imshow(img)
        ax.axis("off")


def block_title(fig, x, y, text, color=None):
    """Подзаголовок блока с фирменной жёлтой отбивкой."""
    fig.add_artist(Line2D([x, x + 0.006], [y - 0.004, y + 0.014],
                          color=C["yellow"], lw=3.2, solid_capstyle="butt"))
    fig.text(x + 0.012, y, text, fontsize=9.3, fontweight="bold",
             color=color or C["text"])


def status_color(st):
    return {"ok": C["ok"], "warn": C["warn"], "bad": C["bad"]}.get(st, C["text"])


_W_CACHE = {}


def text_width_pt(txt, fontsize):
    """Фактическая ширина строки в пунктах для текущего шрифта."""
    if not txt:
        return 0.0
    key = (txt, round(fontsize, 2))
    w = _W_CACHE.get(key)
    if w is None:
        from matplotlib.textpath import TextPath
        from matplotlib.font_manager import FontProperties
        tp = TextPath((0, 0), txt, size=fontsize,
                      prop=FontProperties(family="DejaVu Sans"))
        w = tp.get_extents().width
        _W_CACHE[key] = w
    return w


def _fit_lines(text, width_frac, ax_w_in, fontsize):
    """
    Разбивает текст на строки, помещающиеся в ширину столбца.
    Ширина измеряется по фактическим метрикам шрифта, а не по числу
    символов: у кириллицы средняя ширина знака заметно больше латиницы.
    """
    text = str(text)
    limit = max(width_frac * ax_w_in * 72.0 - 7.0, 12.0)
    if text_width_pt(text, fontsize) <= limit:
        return [text]

    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if cur and text_width_pt(trial, fontsize) > limit:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [text]


def draw_table(ax, headers, rows, col_w=None, row_colors=None,
               fontsize=7.2, header_fs=7.4, align=None, bold_cols=(),
               wrap=True):
    """
    Таблица с переносом текста в ячейках. Высота строки подбирается под
    самую «высокую» ячейку строки, поэтому длинный текст не выходит за
    границы столбца.
    """
    ax.axis("off")
    ncol = len(headers)
    if col_w is None:
        col_w = [1.0 / ncol] * ncol
    col_w = [w / sum(col_w) for w in col_w]
    x = np.concatenate([[0], np.cumsum(col_w)])

    fig = ax.figure
    ax_w_in = ax.get_position().width * fig.get_size_inches()[0]

    def split(txt, j, fs):
        return _fit_lines(txt, col_w[j], ax_w_in, fs) if wrap else [str(txt)]

    hdr_lines = [max(len(str(h).split("\n")), 1) for h in headers]
    hdr_n = max(hdr_lines) if hdr_lines else 1

    body = []
    for row in rows:
        cells = [split(c, j, fontsize) for j, c in enumerate(row)]
        body.append((cells, max(len(c) for c in cells)))

    total_units = hdr_n * 1.25 + sum(n + 0.45 for _, n in body)
    unit = 1.0 / total_units
    y = 1.0

    # --------------------------------------------------------- шапка ---
    hh = hdr_n * 1.25 * unit
    ax.add_patch(Rectangle((0, y - hh), 1, hh, color=C["accent"],
                           transform=ax.transAxes, clip_on=False))
    ax.add_patch(Rectangle((0, y - hh), 1, hh * 0.10, color=C["yellow"],
                           transform=ax.transAxes, clip_on=False, zorder=3))
    for j, htxt in enumerate(headers):
        ax.text(x[j] + col_w[j] / 2, y - hh / 2, str(htxt), ha="center",
                va="center", fontsize=header_fs, color="white",
                fontweight="bold", transform=ax.transAxes,
                linespacing=1.15)
    y -= hh

    # --------------------------------------------------------- строки --
    for i, (cells, nlines) in enumerate(body):
        h = (nlines + 0.45) * unit
        y -= h
        if i % 2 == 0:
            ax.add_patch(Rectangle((0, y), 1, h, color=C["row"],
                                   transform=ax.transAxes, clip_on=False,
                                   zorder=0))
        for j, lines in enumerate(cells):
            col = C["text"]
            if row_colors and i < len(row_colors) and row_colors[i] \
                    and j == len(cells) - 1:
                col = row_colors[i]
            a = (align[j] if align
                 else ("left" if (j == 0 or len(lines) > 1) else "center"))
            xx = (x[j] + 0.006 if a == "left"
                  else x[j + 1] - 0.006 if a == "right"
                  else x[j] + col_w[j] / 2)
            ax.text(xx, y + h / 2, "\n".join(lines), ha=a, va="center",
                    fontsize=fontsize + (0.5 if j in bold_cols else 0),
                    color=col, transform=ax.transAxes, zorder=2,
                    linespacing=1.18,
                    fontweight="bold" if j in bold_cols else "normal")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)


# ==========================================================================
#  1. ТИТУЛЬНЫЙ ЛИСТ
# ==========================================================================

def page_title(pdf, data, intervals, warnings_list):
    fig = page(A4)
    g = getattr(data, "general", {}) or {}

    logo = load_logo()
    if logo is not None:
        h = logo.shape[0] / logo.shape[1]
        w = 0.19
        ax = fig.add_axes([0.5 - w / 2, 0.955 - w * h * 11.69 / 8.27,
                           w, w * h * 11.69 / 8.27])
        ax.imshow(logo)
        ax.axis("off")
    else:
        fig.text(0.5, 0.90, CFG.APP_NAME, ha="center", fontsize=26,
                 fontweight="bold", color=C["accent2"])
    fig.text(0.5, 0.735, f"{CFG.APP_VERSION}   ·   {CFG.APP_AUTHOR}",
             ha="center", fontsize=10, color="#8A8A8C")

    fig.text(0.5, 0.665, t("report_title"),
             ha="center", fontsize=19, fontweight="bold", color=C["text"])
    fig.text(0.5, 0.622, t("report_sub"),
             ha="center", fontsize=11, color=C["accent"])
    fig.add_artist(Line2D([0.22, 0.78], [0.598, 0.598], color=C["accent"],
                          lw=1.2))
    fig.add_artist(Line2D([0.435, 0.565], [0.598, 0.598], color=C["yellow"],
                          lw=4.0, solid_capstyle="butt"))

    req = [(t("r_client"), g.get("заказчик")),
           (t("r_field"), g.get("месторождение") or CFG.FIELD_NAME),
           (t("r_pad"), g.get("куст")),
           (t("r_well"), g.get("скважина") or CFG.WELL_NAME),
           (t("r_welltype"), g.get("тип скважины")),
           (t("r_contractor"), g.get("буровой подрядчик")),
           (t("r_rig"), g.get("буровая установка")),
           (t("r_target"), g.get("проектный горизонт"))]
    req = [(k, v) for k, v in req if v]
    y = 0.560
    for k, v in req:
        fig.text(0.485, y, k + ":", fontsize=9.5, color="#6C6C6E", ha="right")
        fig.text(0.505, y, v, fontsize=9.5, color=C["text"], fontweight="bold")
        y -= 0.027

    y -= 0.012
    fig.add_artist(Line2D([0.30, 0.70], [y + 0.014, y + 0.014],
                          color=C["grid"], lw=0.8))
    y -= 0.010

    pmp = dict(CFG.PUMPS)
    pmp.update((getattr(data, "extra", {}) or {}).get("pumps") or {})
    models = []
    for m in (getattr(data, "models_used", []) or []):
        nm = MODEL_NAMES.get(m, m)
        if nm not in models:
            models.append(nm)
    model_txt = ", ".join(models) if models else MODEL_NAMES.get(
        CFG.RHEOLOGY_MODEL, CFG.RHEOLOGY_MODEL)

    info = [
        (t("i_td"), f"{max(i['md_to'] for i in intervals):.0f}"),
        (t("i_nint"), f"{len(intervals)}"),
        (t("i_model"), model_txt),
        (t("i_flow"), t({"max": "flow_max", "min": "flow_min",
                         "mean": "flow_mean"}[CFG.FLOW_CHOICE])),
        (t("i_pumps"), pmp["тип"] + ", " + t(
            "pumps_of", n=f"{pmp['количество_рабочих']:.0f}",
            d=f"{pmp['диаметр_втулки_мм']:.0f}")),
        (t("r_author"), g.get("ответственный исполнитель") or CFG.AUTHOR),
        (t("r_date"), g.get("дата расчёта") or ""),
    ]
    info = [(k, v) for k, v in info if v]
    for k, v in info:
        fig.text(0.485, y, k + ":", fontsize=8.5, color="#6C6C6E", ha="right")
        fig.text(0.505, y, v, fontsize=8.5, color=C["text"])
        y -= 0.024

    y = min(y - 0.018, 0.245)
    if warnings_list and y < 0.155:
        fig.text(0.5, max(y, 0.075),
                 f"Замечаний к исходным данным: {len(warnings_list)} - "
                 f"полный перечень на последней странице отчёта",
                 ha="center", fontsize=8.5, fontweight="bold", color=C["bad"])
    elif warnings_list:
        fig.text(0.5, y, "ЗАМЕЧАНИЯ К ИСХОДНЫМ ДАННЫМ",
                 ha="center", fontsize=10, fontweight="bold", color=C["bad"])
        y -= 0.030
        shown = 0
        for w in warnings_list:
            lines = textwrap.wrap("• " + w, 118)
            if y - 0.018 * len(lines) < 0.075:
                break
            for ln in lines:
                fig.text(0.07, y, ln, fontsize=7.4, color="#6C6C6E")
                y -= 0.018
            y -= 0.004
            shown += 1
        rest = len(warnings_list) - shown
        if rest > 0:
            fig.text(0.07, y, f"…и ещё {rest} - полный перечень на последней "
                              f"странице отчёта", fontsize=7.4,
                     color=C["bad"], style="italic")
    # логотип компании в нижней части титульного листа
    comp = load_logo(getattr(CFG, "COMPANY_LOGO", ""))
    if comp is not None:
        ch = comp.shape[0] / comp.shape[1]
        cw = 0.135
        ax = fig.add_axes([0.5 - cw / 2, 0.062, cw, cw * ch * 11.69 / 8.27])
        ax.imshow(comp)
        ax.axis("off")
    elif getattr(CFG, "COMPANY_NAME", ""):
        fig.text(0.5, 0.085, CFG.COMPANY_NAME, ha="center", fontsize=11,
                 fontweight="bold", color=C["accent"])

    footer(fig, well_caption(data), 1, mark=False)
    pdf.savefig(fig)
    plt.close(fig)


# ==========================================================================
#  2. КОНСТРУКЦИЯ СКВАЖИНЫ + ПРОФИЛЬ + СТРАТИГРАФИЯ
# ==========================================================================

def page_construction(pdf, data, traj, intervals, page_no):
    fig = page(A4)
    header(fig, t("p_construction"), t("p_construction_sub"))

    ax1 = fig.add_axes([0.055, 0.095, 0.245, 0.712])
    ax2 = fig.add_axes([0.380, 0.095, 0.235, 0.712])
    ax3 = fig.add_axes([0.690, 0.095, 0.275, 0.712])

    td = max(i["md_to"] for i in intervals)
    _draw_well_schematic(ax1, data, intervals, td)
    _draw_profile(ax2, traj, data)
    _draw_strat(ax3, data, td)

    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


def casing_top(c, casings):
    """
    Глубина верха колонны. Обычная колонна - от устья.
    Хвостовик - от башмака предыдущей колонны минус перекрытие.
    """
    if "хвостовик" in c.name.lower() or "liner" in c.name.lower():
        prev = [x for x in casings if x.md_m < c.md_m]
        if prev:
            shoe = max(x.md_m for x in prev)
            return max(0.0, shoe - CFG.LINER_OVERLAP_M)
    return 0.0


def _draw_well_schematic(ax, data, intervals, td):
    ax.set_title(t("c_scheme"), fontsize=10, fontweight="bold", pad=10)
    maxd = max(c.od_mm for c in data.casings) * 1.45

    # 1) открытый ствол по секциям (с учётом кавернозности)
    for itv in intervals:
        key, sec = itv["key"], itv["section"]
        cav = CFG.CAVING_FACTOR.get(key, CFG.CAVING_FACTOR.get(sec, 1.1))
        d = itv["bit_mm"] * cav
        ax.add_patch(Rectangle((-d / 2, itv["md_from"]), d,
                               itv["md_to"] - itv["md_from"],
                               facecolor="#F7E9C4", edgecolor="#C8901A",
                               lw=0.6, zorder=1))

    # 2) колонны: цемент -> стенки -> раствор внутри
    for c in sorted(data.casings, key=lambda x: -x.od_mm):
        top = casing_top(c, data.casings)
        ax.add_patch(Rectangle((-c.od_mm / 2, top), c.od_mm, c.md_m - top,
                               facecolor="#D4D2CB", edgecolor="none", zorder=2))
        for sgn in (-1, 1):
            ax.add_patch(Rectangle((sgn * c.id_mm / 2, top),
                                   sgn * (c.od_mm - c.id_mm) / 2, c.md_m - top,
                                   facecolor="#3A3A3A", edgecolor="none",
                                   zorder=3))
        ax.add_patch(Rectangle((-c.id_mm / 2, top), c.id_mm, c.md_m - top,
                               facecolor=C["mud"], alpha=1.0,
                               edgecolor="none", zorder=2.5))
        ax.plot([-c.od_mm / 2, c.od_mm / 2], [c.md_m, c.md_m],
                color="#3A3A3A", lw=1.8, zorder=4)
        if top > 0:
            ax.plot([-c.od_mm / 2, c.od_mm / 2], [top, top],
                    color="#3A3A3A", lw=1.2, ls=":", zorder=4)

    # 3) необсаженный интервал
    for oh in (getattr(data, "extra", {}) or {}).get("openhole") or []:
        prev = [c.md_m for c in data.casings if c.md_m < oh["md_to"]]
        top = max(prev) if prev else 0.0
        d = oh["d_mm"]
        ax.add_patch(Rectangle((-d / 2, top), d, oh["md_to"] - top,
                               facecolor="none", edgecolor=C["accent2"],
                               lw=1.4, ls=(0, (4, 2)), zorder=4))
        ax.annotate(f"{oh['name']} Ø{d:.1f} мм\n"
                    f"{top:.0f}-{oh['md_to']:.0f} м MD",
                    xy=(d / 2, 0.5 * (top + oh["md_to"])),
                    xytext=(maxd * 0.55, oh["md_to"] + td * 0.045),
                    fontsize=6.2, va="center", ha="left",
                    color=C["accent2"],
                    arrowprops=dict(arrowstyle="-", lw=0.6,
                                    color=C["accent2"]), zorder=5)

    # 4) выноски
    for c in data.casings:
        top = casing_top(c, data.casings)
        extra = "\n" + t("c_hanger", d=f"{top:.0f}") if top > 0 else ""
        ax.annotate(f"{c.name}\nØ{c.od_mm:.0f}×{c.wall_mm:.1f} (вн. {c.id_mm:.1f})\n"
                    f"{c.md_m:.0f} м MD / {c.tvd_m:.0f} м TVD{extra}",
                    xy=(c.od_mm / 2, c.md_m),
                    xytext=(maxd * 0.55, c.md_m),
                    fontsize=6.2, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", lw=0.6,
                                    color="#A8A8AA"), zorder=5)

    ax.set_xlim(-maxd * 0.72, maxd * 1.85)
    ax.set_ylim(td * 1.03, -td * 0.03)
    ax.set_xlabel(t("c_diameter"), fontsize=7.5)
    ax.set_ylabel(t("c_md"), fontsize=8)
    ax.grid(axis="y", alpha=0.5)
    ax.set_xticks([-300, -150, 0, 150, 300])
    ax.set_xticklabels(["300", "150", "0", "150", "300"], fontsize=6.5)
    ax.tick_params(labelsize=6.5)


def _draw_profile(ax, traj, data):
    ax.set_title(t("c_profile"), fontsize=10, fontweight="bold", pad=10)
    hd = traj.hd
    ax.plot(hd, traj.tvd, color=C["accent"], lw=2.4, zorder=3)
    ax.fill_betweenx(traj.tvd, 0, hd, color=C["accent"], alpha=0.07)

    for c in data.casings:
        i = int(np.argmin(np.abs(traj.md - c.md_m)))
        ax.plot(hd[i], traj.tvd[i], "o", ms=6, color=C["accent2"], zorder=4)
        ax.annotate(f"Ø{c.od_mm:.0f}   {c.md_m:.0f} м",
                    (hd[i], traj.tvd[i]), xytext=(7, -9),
                    textcoords="offset points", fontsize=6.3)

    ax2 = ax.twiny()
    ax2.plot(traj.inc, traj.tvd, color=C["accent2"], lw=1.0, ls="--", alpha=0.8)
    ax2.set_xlabel(t("c_inc"), color=C["accent2"], fontsize=7.5)
    ax2.tick_params(axis="x", colors=C["accent2"], labelsize=6.5)
    ax2.grid(False)

    ax.set_xlabel(t("c_disp"))
    ax.set_ylabel(t("c_tvd"))
    ax.invert_yaxis()


def _draw_strat(ax, data, td):
    ax.set_title(t("c_geology"), fontsize=10, fontweight="bold", pad=8)
    if not data.strat:
        ax.text(0.5, 0.5, "нет данных", ha="center", transform=ax.transAxes)
        ax.axis("off")
        return
    palette = ["#E4DCC8", "#D2D0CA", "#EFE2BC", "#C8C6C0", "#E8DCB4",
               "#BEBCB6", "#F0E6C8", "#D8D4C6", "#E0D2A8", "#CACAC4",
               "#EDE4CE", "#C4C2BA", "#E6DAB8"]
    rho_max = max(s["ро"] for s in data.strat)
    for i, s in enumerate(data.strat):
        h = s["до"] - s["от"]
        ax.add_patch(Rectangle((0, s["от"]), 1.0, h,
                               facecolor=palette[i % len(palette)],
                               edgecolor="white", lw=0.6))
        ax.barh(s["от"] + h / 2, s["ро"] / rho_max * 0.9, height=h * 0.55,
                left=1.10, color="#EFD79A", edgecolor=C["accent2"], lw=0.5)
        if h > td * 0.011:
            ax.text(0.03, s["от"] + h / 2, s["название"],
                    fontsize=6.0 if h > td * 0.022 else 4.8, va="center")
            ax.text(2.06, s["от"] + h / 2, f"{s['ро']:.2f}", fontsize=5.8,
                    va="center", ha="right", color=C["text"])
    ax.set_xlim(0, 2.1)
    ax.set_ylim(td * 1.03, -td * 0.03)
    ax.set_xticks([0.5, 1.55])
    ax.set_xticklabels([t("c_formation"), t("c_rho_rock")], fontsize=7)
    ax.set_ylabel(t("c_md"))
    ax.grid(axis="y", alpha=0.4)


# ==========================================================================
#  3. ИСХОДНЫЕ ДАННЫЕ (ТАБЛИЦЫ)
# ==========================================================================

def page_inputs(pdf, data, intervals, page_no):
    fig = page(A4)
    header(fig, t("p_inputs"), t("p_inputs_sub"))

    ax = fig.add_axes([0.04, 0.595, 0.92, 0.265])
    mud_src = (getattr(data, "extra", {}) or {}).get("mud", {})
    rows = []
    for i in intervals:
        mud = mud_src.get(i["key"], {})
        rows.append([i["key"], f"{i['md_from']:.0f}-{i['md_to']:.0f}",
                     f"{i['bit_mm']:.1f}", i.get("bit_type", "-") or "-",
                     f"{i['rop']:.0f}", i["drive"],
                     f"{i['q_lps']:.0f}",
                     (mud.get("тип") or "-")[:26],
                     f"{i['rho']:.2f}", f"{i['pv']:.0f}", f"{i['yp']:.0f}",
                     MODEL_NAMES.get(i.get("model"), "-")])
    draw_table(ax,
               [t("h_interval"), t("h_md"), t("h_bit_d"), t("h_bit_type"),
                t("h_rop"), t("h_drive"), t("h_q"), t("h_mudtype"),
                t("h_rho"), t("h_pv"), t("h_yp"), t("h_model")],
               rows,
               col_w=[0.108, 0.085, 0.062, 0.115, 0.048, 0.095, 0.045,
                      0.165, 0.055, 0.048, 0.058, 0.116],
               fontsize=6.6, header_fs=6.6)
    block_title(fig, 0.04, 0.876, t("t_bitprog"))

    ax2 = fig.add_axes([0.04, 0.315, 0.44, 0.20])
    rows2 = [[c.name, f"{c.od_mm:.1f}", f"{c.wall_mm:.1f}", f"{c.id_mm:.1f}",
              f"{c.md_m:.0f} / {c.tvd_m:.0f}"] for c in data.casings]
    for oh in (getattr(data, "extra", {}) or {}).get("openhole") or []:
        rows2.append([oh["name"], f"{oh['d_mm']:.1f}", "-", "-",
                      f"{oh['md_to']:.0f} / {oh['tvd_to']:.0f}"])
    draw_table(ax2, [t("h_casing"), t("h_od"), t("h_wall"), t("h_id"),
                     t("h_shoe")], rows2,
               col_w=[0.30, 0.16, 0.17, 0.16, 0.21])
    block_title(fig, 0.04, 0.535, t("t_casing"))

    ax3 = fig.add_axes([0.545, 0.315, 0.415, 0.20])
    p = dict(CFG.PUMPS)
    p.update((getattr(data, "extra", {}) or {}).get("pumps") or {})
    rows3 = [
        [t("pump_type"), p["тип"]],
        [t("pump_n"), f"{p['количество_рабочих']:.0f}"],
        [t("pump_liner"), f"{p['диаметр_втулки_мм']:.0f}"],
        [t("pump_stroke"), f"{p['длина_хода_мм']:.0f}"],
        [t("pump_cyl"), f"{p.get('цилиндров', 3):.0f}"],
        [t("pump_fill"), f"{p['коэффициент_наполнения']:.2f}"],
        [t("pump_spm"), f"{p['макс_ходов_в_мин']:.0f}"],
        [t("pump_pmax", u=punit()), pfmt(p["макс_давление_МПа"] * 1e6)],
        [t("pump_power"), f"{p['мощность_на_насос_кВт']:.0f}"],
    ]
    draw_table(ax3, [t("h_param"), t("h_value")], rows3,
               col_w=[0.62, 0.38])
    block_title(fig, 0.545, 0.535, t("t_pumps"))

    ax4 = fig.add_axes([0.04, 0.055, 0.92, 0.20])
    from hydraulics_extra import resolve
    ex = getattr(data, "extra", {}) or {}
    res_rpm = getattr(CFG, "ROTATION_RPM", {})
    rows4 = []
    for i in intervals:
        key, sec = i["key"], i["section"]
        nz, s1 = resolve(ex, "nozzles", key, sec, CFG.NOZZLES, [])
        cv, _ = resolve(ex, "caving", key, sec, CFG.CAVING_FACTOR, 1.1)
        mt, s2 = resolve(ex, "motor", key, sec, CFG.MOTOR)
        mw, s3 = resolve(ex, "mwd", key, sec, CFG.MWD)
        if isinstance(nz, dict):
            nztxt = f"TFA {nz.get('tfa_in2', 0):.3f} дюйм²"
        elif nz and len(set(nz)) == 1:
            nztxt = f"{len(nz)} × {nz[0]:.0f}/32\""
        elif nz:
            from collections import Counter
            nztxt = " + ".join(f"{k}×{d:.0f}/32\""
                               for d, k in sorted(Counter(nz).items()))
        else:
            nztxt = "-"
        rpm = ((ex.get("rpm", {}) or {}).get(key)
               or res_rpm.get(key, res_rpm.get(sec, 0)) or 0)
        rows4.append([
            key, nztxt, f"{cv:.2f}",
            mt["имя"] if mt else "-",
            pfmt((mt["dp_xx_МПа"] + mt["dp_load_МПа"]) * 1e6) if mt else "-",
            mw["имя"] if mw else "-",
            pfmt(mw["dp_МПа"] * 1e6) if mw else "-",
            f"{rpm:.0f}" if rpm else "-",
        ])
    draw_table(ax4, [t("h_interval"), t("h_nozzles"), t("h_caving"),
                     t("h_motor"), t("h_dp_motor", u=punit()), t("h_mwd"),
                     t("h_dp_mwd", u=punit()), t("h_rpm")],
               rows4, col_w=[0.16, 0.24, 0.11, 0.12, 0.10, 0.11, 0.09, 0.07])
    block_title(fig, 0.04, 0.272, t("t_nozzles_block"))

    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


# ==========================================================================
#  4. СХЕМА КНБК
# ==========================================================================

ELEMENT_STYLE = {
    "долот":       ("#3A3A3A", "долото"),
    "взд":         ("#C8901A", "ВЗД"),
    "калибратор":  ("#F8C818", "калибратор"),
    "стабилизатор": ("#F8C818", "стабилизатор"),
    "mwd":         ("#8C7A3C", "MWD"),
    "lwd":         ("#8C7A3C", "LWD"),
    "нубт":        ("#A08C46", "НУБТ"),
    "убт":         ("#58585A", "УБТ"),
    "тбт":         ("#7A7A7C", "ТБТ"),
    "сбт":         ("#9C9C9E", "СБТ"),
    "яс":          ("#6E6A50", "ясс"),
    "амортизатор": ("#7E7660", "амортизатор"),
    "клапан":      ("#46464A", "клапан"),
    "переводник":  ("#BEBCB8", "переводник"),
}


def element_style(name):
    n = name.lower()
    for k, v in ELEMENT_STYLE.items():
        if k in n:
            return v[0]
    return "#BEBCB8"


def _spread_labels(centers, total, min_gap):
    """
    Раздвигает подписи по вертикали так, чтобы они не накладывались,
    сохраняя порядок (простой одномерный алгоритм «расталкивания»).
    """
    ys = list(centers)
    n = len(ys)
    for _ in range(200):
        moved = False
        for i in range(n - 1):
            gap = ys[i + 1] - ys[i]
            if gap < min_gap:
                sh = (min_gap - gap) / 2.0
                ys[i] -= sh
                ys[i + 1] += sh
                moved = True
        ys[0] = max(ys[0], 0.0)
        ys[-1] = min(ys[-1], total)
        if not moved:
            break
    return ys


def draw_bha(ax, res):
    """Схематичная компоновка низа бурильной колонны (в масштабе по длине)."""
    bha = res["bha"]
    total = sum(b.length_m for b in bha)
    ax.set_title(t("g_bha", k=res["key"])
                 + (t("g_bha_tmpl") if res["is_template"] else ""),
                 fontsize=9.0, fontweight="bold", pad=8,
                 color=C["bad"] if res["is_template"] else C["text"])

    dmax = max(b.od_mm for b in bha)
    # координата: 0 - долото (внизу), вверх - к устью
    tops, y = [], 0.0
    for b in bha:
        L = max(b.length_m or 0.0, total * 0.004)
        tops.append((b, y, L))
        y += L
    scale = total / y if y > 0 else 1.0

    centers, labels = [], []
    for b, y0, L in tops:
        y0s, Ls = y0 * scale, L * scale
        col = element_style(b.name)
        if "долот" in b.name.lower():
            _draw_bit(ax, y0s, Ls, b.od_mm, col)
        else:
            ax.add_patch(Rectangle((-b.od_mm / 2, y0s), b.od_mm, Ls,
                                   facecolor=col, edgecolor="white", lw=0.4))
            if b.id_mm:
                ax.add_patch(Rectangle((-b.id_mm / 2, y0s), b.id_mm, Ls,
                                       facecolor="white", alpha=0.6,
                                       edgecolor="none"))
        centers.append(y0s + Ls / 2)
        labels.append(f"{b.name} · L={b.length_m:.2f} м · "
                      f"Ø{b.od_mm:.1f}" + (f"/{b.id_mm:.1f}" if b.id_mm else "/-"))

    gap = total / max(len(labels) + 1, 1) * 0.92
    ys = _spread_labels(centers, total, gap)
    xlab = dmax * 0.80
    for (b, y0, L), yc, yl, txt in zip(tops, centers, ys, labels):
        ax.annotate(txt, xy=(b.od_mm / 2, yc), xytext=(xlab, yl),
                    fontsize=5.6, va="center", ha="left",
                    arrowprops=dict(arrowstyle="-", lw=0.45, color="#C9C7C2",
                                    shrinkA=0, shrinkB=0))

    ax.set_xlim(-dmax * 0.95, dmax * 3.3)
    ax.set_ylim(-total * 0.03, total * 1.05)
    ax.set_xlabel("Ø, " + t("u_mm"), fontsize=7)
    ax.set_ylabel(t("g_bha_axis"), fontsize=7.5)
    ax.grid(axis="y", alpha=0.4)
    ax.tick_params(labelsize=6.3)
    ax.text(0.02, 0.985, t("g_bha_len", L=f"{total:.2f}"), fontsize=7,
            fontweight="bold", color=C["accent"], va="top",
            transform=ax.transAxes,
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=C["grid"],
                      lw=0.5))


def _draw_bit(ax, y, L, d, col):
    """Долото рисуется остриём вниз."""
    pts = [(-d / 2, y + L), (d / 2, y + L), (d / 2 * 0.72, y),
           (-d / 2 * 0.72, y)]
    ax.add_patch(Polygon(pts, closed=True, facecolor=col, edgecolor="white",
                         lw=0.6))
    for k in (-0.26, 0, 0.26):
        ax.plot([d * k], [y + L * 0.3], marker="v", ms=2.6, color="white")


# ==========================================================================
#  5. СТРАНИЦА СЕКЦИИ
# ==========================================================================

def page_section(pdf, res, assessment, sweep, traj, page_no):
    fig = page(A4)
    itv = res["itv"]
    header(fig,
           t("p_section", k=res["key"], a=f"{itv['md_from']:.0f}",
             b=f"{itv['md_to']:.0f}"),
           t("p_section_sub", d=f"{itv['bit_mm']:.1f}",
             q=f"{res['q_lps']:.1f}", rho=f"{itv['rho']:.2f}",
             pv=f"{itv['pv']:.0f}", yp=f"{itv['yp']:.0f}",
             rop=f"{itv['rop']:.0f}"))

    # --- КНБК ---
    ax_bha = fig.add_axes([0.040, 0.082, 0.205, 0.745])
    draw_bha(ax_bha, res)

    # --- эпюра давлений ---
    ax_p = fig.add_axes([0.320, 0.475, 0.175, 0.345])
    _plot_pressure(ax_p, res)

    # --- скорости в затрубье ---
    ax_v = fig.add_axes([0.560, 0.475, 0.155, 0.345])
    _plot_velocity(ax_v, res)

    # --- ЭЦП ---
    ax_e = fig.add_axes([0.775, 0.475, 0.155, 0.320])
    _plot_ecd(ax_e, res)

    # --- баланс потерь ---
    ax_b = fig.add_axes([0.345, 0.085, 0.150, 0.275])
    _plot_balance(ax_b, res)

    # --- зависимость от расхода ---
    ax_q = fig.add_axes([0.565, 0.085, 0.150, 0.275])
    _plot_sweep(ax_q, res, sweep)

    # --- итоговые показатели ---
    ax_s = fig.add_axes([0.775, 0.070, 0.200, 0.325])
    _panel_summary(ax_s, res, assessment)

    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


def _plot_pressure(ax, res):
    ax.set_title(t("g_pressure"), fontsize=9, fontweight="bold")
    ax.plot(P(np.array(res["in_p"])), res["in_md"], color=C["accent"],
            lw=1.8, label=t("g_inside"))
    ax.plot(P(np.array(res["prof_p"])), res["prof_md"], color=C["accent2"],
            lw=1.8, label=t("g_annulus"))
    fl = res["fluid"]
    md = np.array(res["prof_md"])
    if len(md):
        hyd = P(np.array([fl.rho * CFG.G * t for t in res["prof_tvd"]]))
        ax.plot(hyd, md, color="#A8A8AA", lw=1.0, ls="--",
                label=t("g_hydrostatic"))
    ax.set_xlabel(t("g_pressure_x", u=punit()), fontsize=7.5)
    ax.set_ylabel(t("c_md"), fontsize=7.5)
    ax.invert_yaxis()
    ax.legend(fontsize=6, loc="lower left", framealpha=0.9)
    ax.tick_params(labelsize=6.5)


def _plot_velocity(ax, res):
    ax.set_title(t("g_velocity"), fontsize=9, fontweight="bold")
    for s in res["ann"]:
        need = getattr(s, "v_crit", 0.0)
        col = (C["bad"] if s.V < need
               else C["warn"] if s.V > CFG.CRIT["Vкц_макс_мс"]
               else C["ok"])
        ax.plot([s.V, s.V], [s.md_top, s.md_bot], color=col, lw=3.2,
                solid_capstyle="butt")
    xs, ys = [], []
    for s in res["ann"]:
        xs += [s.V, s.V]
        ys += [s.md_top, s.md_bot]
    ax.plot(xs, ys, color="#6C6C6E", lw=0.7, alpha=0.8, zorder=1)
    # требуемая скорость выноса меняется по стволу вместе с углом
    xr, yr = [], []
    for s in res["ann"]:
        vc = getattr(s, "v_crit", 0.0)
        xr += [vc, vc]
        yr += [s.md_top, s.md_bot]
    if any(xr):
        ax.plot(xr, yr, color=C["bad"], lw=1.3, ls="--",
                label=t("g_required"))
        ax.legend(fontsize=5.6, loc="lower right", framealpha=0.9)
    ax.axvline(CFG.CRIT["Vкц_макс_мс"], color=C["warn"], ls=":", lw=1.0)
    ax.set_xlabel(t("h_v"), fontsize=7.5)
    ax.set_ylabel(t("c_md"), fontsize=7.5)
    ax.invert_yaxis()
    ax.tick_params(labelsize=6.5)
    long_v = [s.V for s in res["ann"] if (s.md_bot - s.md_top) >= 5.0]
    vlim = max(long_v, default=max((s.V for s in res["ann"]), default=1.0))
    ax.set_xlim(0, max(2.0, vlim * 1.35))


def _plot_ecd(ax, res):
    ax.set_title(t("g_ecd"), fontsize=9, fontweight="bold", pad=16)
    md = res["prof_md"][1:]
    ecd = res["prof_ecd"][1:]
    ax.plot(ecd, md, color=C["accent"], lw=1.8)
    rho = res["itv"]["rho"]
    lim = rho + CFG.CRIT["ЭЦП_запас_гсм3"]
    ax.axvline(rho, color="#A8A8AA", ls="--", lw=1.0)

    extra = []
    w = res.get("window")
    if w:
        # окно бурения: от порового давления до давления ГРП
        po = [v for v in w["pore"] if v is not None]
        fr = [v for v in w["frac"] if v is not None]
        if po and fr and len(po) == len(w["md"]) and len(fr) == len(w["md"]):
            ax.fill_betweenx(w["md"], w["pore"], w["frac"],
                             color=C["ok"], alpha=0.10, zorder=0)
            ax.plot(w["pore"], w["md"], color=C["ok"], lw=1.1, ls="-.")
            ax.plot(w["frac"], w["md"], color=C["bad"], lw=1.1, ls="-.")
            extra = po + fr
        if w.get("loss") and any(v is not None for v in w["loss"]):
            ax.plot(w["loss"], w["md"], color=C["warn"], lw=0.9, ls=":")
            extra += [v for v in w["loss"] if v is not None]
    else:
        ax.axvline(lim, color=C["bad"], ls="--", lw=1.0)
        extra = [lim]

    lo = min([rho] + list(ecd) + extra) - 0.02
    hi = max(list(ecd) + extra + [rho]) + 0.02
    ax.set_xlim(lo, hi)
    ax.set_xlabel(t("g_ecd_x"), fontsize=7.5)
    ax.set_ylabel(t("c_md"), fontsize=7.5)
    ax.set_ylim(res["td"] * 1.02, -res["td"] * 0.02)
    ax.tick_params(labelsize=6.3)

    ax2 = ax.twiny()
    conc = [getattr(s, "conc", 0) * 100 for s in res["ann"]]
    mds = [s.md_bot for s in res["ann"]]
    ax2.plot(conc, mds, color=C["accent2"], lw=1.2, alpha=0.85)
    ax2.set_xlabel(t("g_conc"), color=C["accent2"], fontsize=6.8,
                   labelpad=1)
    ax2.tick_params(axis="x", colors=C["accent2"], labelsize=5.8)
    ax2.set_xlim(0, max(max(conc, default=1) * 1.25, 1.0))
    ax2.grid(False)
    ax2.set_ylim(ax.get_ylim())


def _plot_balance(ax, res):
    ax.set_title(t("g_balance"), fontsize=9, fontweight="bold")
    items = [
        (t("b_surface"), res["dp_surface"]),
        (t("b_string"),
         res["dp_inside"] - res["dp_motor"] - res["dp_mwd"]),
        (t("b_motor"), res["dp_motor"]),
        (t("b_mwd"), res["dp_mwd"]),
        (t("b_bit"), res["dp_bit"]),
        (t("b_annulus"), res["dp_ann"]),
    ]
    palette = {t("b_surface"): C["grey_lt"], t("b_string"): C["accent"],
               t("b_motor"): C["accent2"], t("b_mwd"): "#8C7A3C",
               t("b_bit"): C["bit"], t("b_annulus"): C["yellow"]}
    items = [(n, v) for n, v in items if v > 1e3]
    names = [i[0] for i in items]
    vals = [P(i[1]) for i in items]
    cols = [palette[n] for n in names]
    y = np.arange(len(items))
    ax.barh(y, vals, color=cols, height=0.62)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6.8)
    ax.invert_yaxis()
    tot = P(res["p_pump"])
    for i, v in enumerate(vals):
        ax.text(v + tot * 0.015, i,
                f"{v:.{pnd()}f} {punit()} ({v / tot * 100:.0f} %)",
                va="center", fontsize=6.3)
    ax.set_xlim(0, max(vals) * 1.55)
    ax.set_xlabel(t("h_dp", u=punit()), fontsize=7.5)
    ax.tick_params(labelsize=6.5)
    ax.grid(axis="x", alpha=0.5)


def _plot_sweep(ax, res, sw):
    ax.set_title(t("g_sweep"), fontsize=9, fontweight="bold")
    if not sw["q"]:
        ax.axis("off")
        return
    ax.plot(sw["q"], P(np.array(sw["p"])), color=C["accent"], lw=1.8,
            label=t("g_pump_p"))
    ax.axhline(P(res.get("pump", CFG.PUMPS)["макс_давление_МПа"] * 1e6),
               color=C["bad"], ls="--", lw=1.0)
    ax.axvline(res["q_lps"], color="#A8A8AA", ls=":", lw=1.2)
    ax.set_xlabel(t("h_q").replace("\n", " "), fontsize=7.5)
    ax.set_ylabel(f"P, {punit()}", fontsize=7.5, color=C["accent"])
    ax.tick_params(labelsize=6.5)

    ax2 = ax.twinx()
    ax2.plot(sw["q"], sw["ecd"], color=C["accent2"], lw=1.5)
    ax2.set_ylabel(t("g_ecd_x"), fontsize=7.5, color=C["accent2"])
    ax2.tick_params(axis="y", colors=C["accent2"], labelsize=6.5)
    ax2.grid(False)
    ax.legend(fontsize=6, loc="upper left")


def _panel_summary(ax, res, assessment):
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    b = res["bit"]
    lines = [
        (t("s_p_start"),
         pfmt(res["p_start"], unit=True) if res.get("p_start")
         else t("dash")),
        (t("s_p_end"), pfmt(res["p_pump"], unit=True)),
        (t("s_load"), f"{res['load_pct']:.0f} %"),
        (t("s_spm"), f"{res['spm']:.0f} " + t("u_spm")),
        (t("s_power"), f"{res['power_kW']:.0f} " + t("u_kw")),
        ("-", ""),
        (t("s_dp_bit"), pfmt(res["dp_bit"], unit=True)),
        (t("s_vnoz"), f"{b['v_noz']:.0f} " + t("u_ms")),
        (t("s_tfa"), f"{b['tfa_in2']:.3f} " + t("u_in2")),
        (t("s_hsi"), f"{b['hsi_kW_cm2']:.3f} " + t("u_kwcm2")),
        (t("s_same"), f"{b['hsi_hp_in2']:.2f} " + t("u_hpin2")),
        (t("s_impact"), f"{b['impact_N'] / 1000:.2f} " + t("u_kn")),
        ("-", ""),
        (t("s_ecd"), f"{res['ecd_bottom']:.3f} " + t("u_gcm3")),
        (t("s_ecd_rise"), f"+{res['ecd_bottom'] - res['itv']['rho']:.3f}"),
        (t("s_rho_bh"), f"{res.get('rho_bottom', 0):.3f} " + t("u_gcm3")),
        (t("s_temp"), f"{res.get('T_bottom', 0):.0f} °C"),
        ("–", ""),
        (t("s_inc_max"), f"{res.get('inc_max', 0):.0f}°"),
        (t("s_rpm"), f"{res.get('rpm', 0):.0f} " + t("u_rpm")),
        (t("s_bed"), f"{res.get('bed_max', 0) * 100:.1f} " + t("of_hole")),
        (t("s_gel"), pfmt(res.get("gel", (0, 0, 0))[2], unit=True)),
        (t("s_rho_cut"), f"{res['rho_cut']:.2f} " + t("u_gcm3")),
    ]
    n_ass = len(assessment)
    step = 0.0265
    y = 1.0
    ax.text(0, y, t("s_results"), fontsize=7.6, fontweight="bold",
            color=C["text"])
    ax.plot([0, 0.30], [y - 0.012, y - 0.012], color=C["yellow"], lw=2.4,
            clip_on=False, solid_capstyle="butt")
    y -= 0.044
    for k, v in lines:
        if k == "-":
            ax.plot([0, 1], [y + 0.014, y + 0.014], color=C["grid"], lw=0.7,
                    clip_on=False)
            y -= 0.020
            continue
        ax.text(0, y, k, fontsize=6.0, color="#6C6C6E")
        ax.text(1, y, v, fontsize=6.0, ha="right", fontweight="bold")
        y -= step

    y -= 0.018
    ax.text(0, y, t("s_assess"), fontsize=7.6, fontweight="bold",
            color=C["text"])
    ax.plot([0, 0.30], [y - 0.012, y - 0.012], color=C["yellow"], lw=2.4,
            clip_on=False, solid_capstyle="butt")
    y -= 0.042
    for name, val, crit, st in assessment:
        ax.add_patch(plt.Circle((0.016, y + 0.007), 0.013,
                                color=status_color(st), clip_on=False))
        ax.text(0.048, y, name, fontsize=5.5, color=C["text"])
        ax.text(1.0, y, val, fontsize=5.5, ha="right",
                color=status_color(st), fontweight="bold")
        y -= 0.0275
    ax.set_aspect("auto")


# ==========================================================================
#  6. ТАБЛИЦЫ ПОИНТЕРВАЛЬНОГО РАСЧЁТА
# ==========================================================================

def page_section_tables(pdf, res, page_no):
    fig = page(A4)
    header(fig, t("p_tables", k=res["key"]), t("p_tables_sub"))

    rows_in = []
    for s in res["inside"]:
        rows_in.append([s.name[:28], f"{s.md_top:.1f}-{s.md_bot:.1f}",
                        f"{s.md_bot - s.md_top:.2f}",
                        f"{s.d_in:.1f}" if s.d_in else "-",
                        f"{s.V:.2f}" if s.V else "-",
                        f"{s.Re:.0f}" if s.Re else "-", s.mode,
                        f"{pgrad(s.grad):.1f}" if s.grad else "-",
                        pfmt(s.dp, fine=True)])
    n1 = len(rows_in)
    h1 = min(0.40, 0.028 * (n1 + 2))
    ax1 = fig.add_axes([0.035, 0.863 - h1, 0.93, h1])
    draw_table(ax1, [t("h_element"), t("h_md"), t("h_len"), t("h_id"),
                     t("h_v"), t("h_re"), t("h_regime"),
                     t("h_grad", u=punit()), t("h_dp", u=punit())],
               rows_in,
               col_w=[0.24, 0.14, 0.07, 0.08, 0.07, 0.09, 0.11, 0.09, 0.11],
               fontsize=6.4, header_fs=6.6)
    block_title(fig, 0.035, 0.876, t("t_inside"))

    rows_a = []
    for s in res["ann"]:
        rows_a.append([s.name[:20], f"{s.md_top:.0f}-{s.md_bot:.0f}",
                       f"{getattr(s, 'inc', 0):.0f}",
                       f"{s.d_out:.1f}", f"{s.d_in:.1f}",
                       f"{s.V:.2f}", f"{getattr(s, 'v_crit', 0):.2f}",
                       f"{s.Re:.0f}", s.mode,
                       f"{getattr(s, 'k_ecc', 1):.2f}",
                       f"{getattr(s, 'k_rot', 1):.2f}",
                       f"{getattr(s, 'bed_frac', 0) * 100:.0f}",
                       f"{getattr(s, 'conc', 0) * 100:.2f}",
                       f"{pgrad(s.grad):.2f}", pfmt(s.dp, fine=True)])
    top2 = 0.863 - h1 - 0.075
    n2 = len(rows_a)
    h2 = min(top2 - 0.06, 0.028 * (n2 + 2))
    ax2 = fig.add_axes([0.035, top2 - h2, 0.93, h2])
    draw_table(ax2, [t("h_ann_sec"), t("h_md"), t("h_inc"),
                     t("h_od_hole"), t("h_od_pipe"), t("h_v"), t("h_vreq"),
                     t("h_re"), t("h_regime"), t("h_kecc"), t("h_krot"),
                     t("h_bed"), t("h_conc"), t("h_grad", u=punit()),
                     t("h_dp", u=punit())],
               rows_a,
               col_w=[0.135, 0.095, 0.045, 0.058, 0.055, 0.048, 0.058,
                      0.062, 0.088, 0.048, 0.050, 0.058, 0.050, 0.070,
                      0.082],
               fontsize=5.9, header_fs=5.8)
    block_title(fig, 0.035, top2 + 0.013, t("t_annulus"))

    tot = t("total_line", a=pfmt(res["dp_surface"]),
            b=pfmt(res["dp_inside"]), c=pfmt(res["dp_bit"]),
            d=pfmt(res["dp_ann"]), tot=pfmt(res["p_pump"], unit=True))
    fig.text(0.5, 0.045, tot, fontsize=10, fontweight="bold",
             ha="center", color=C["accent"])
    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


# ==========================================================================
#  7. СВОДНАЯ СТРАНИЦА
# ==========================================================================

def page_summary(pdf, results, page_no):
    fig = page(A4)
    header(fig, t("p_summary"), t("p_summary_sub"))

    rows, colors = [], []
    for r in results:
        v = [s.V for s in r["ann"]]
        conc = max((getattr(s, "conc", 0) for s in r["ann"]), default=0) * 100
        st = ("bad" if r["load_pct"] > CFG.CRIT["Загрузка_насоса_%"]
              or conc > CFG.CRIT["Cшлам_макс_%"] else "ok")
        rows.append([
            r["key"], f"{r['md_from']:.0f}-{r['td']:.0f}",
            f"{r['q_lps']:.0f}",
            pfmt(r["p_start"]) if r.get("p_start") else "-",
            pfmt(r["p_pump"]),
            pfmt(r["dp_surface"]), pfmt(r["dp_inside"]),
            pfmt(r["dp_bit"]), pfmt(r["dp_ann"]),
            f"{min(v):.2f}-{max(v):.2f}" if v else "-",
            f"{conc:.1f}", f"{r['ecd_bottom']:.3f}",
            f"{r['bit']['hsi_kW_cm2']:.3f}", f"{r['spm']:.0f}",
            f"{r['load_pct']:.0f} %",
        ])
        colors.append(status_color(st))
    ax = fig.add_axes([0.03, 0.60, 0.94, 0.26])
    draw_table(ax, [t("h_interval"), t("h_md"), t("h_q"),
                    t("h_pstart", u=punit()), t("h_pend", u=punit()),
                    t("b_surface"), t("b_string"), t("b_bit"),
                    t("b_annulus"), t("h_vann"), t("h_bed"), t("h_conc"),
                    t("h_ecd"), t("h_hsi"), t("h_spm"), t("h_loadpct")],
               rows,
               col_w=[0.103, 0.083, 0.045, 0.058, 0.058, 0.055, 0.055,
                      0.052, 0.055, 0.077, 0.053, 0.048, 0.054, 0.061,
                      0.048, 0.058],
               row_colors=colors, fontsize=6.3, header_fs=6.2,
               bold_cols=(3, 4))

    ax2 = fig.add_axes([0.06, 0.09, 0.40, 0.41])
    keys = [r["key"] for r in results]
    x = np.arange(len(results))
    parts = {
        t("b_surface"): [P(r["dp_surface"]) for r in results],
        t("b_string"): [P(r["dp_inside"]) for r in results],
        t("b_bit"): [P(r["dp_bit"]) for r in results],
        t("b_annulus"): [P(r["dp_ann"]) for r in results],
    }
    bottom = np.zeros(len(results))
    cols = [C["grey_lt"], C["accent"], C["bit"], C["yellow"]]
    for (nm, vals), col in zip(parts.items(), cols):
        ax2.bar(x, vals, bottom=bottom, label=nm, color=col, width=0.6)
        bottom += np.array(vals)
    ax2.axhline(P(results[0].get("pump", CFG.PUMPS)["макс_давление_МПа"] * 1e6),
                color=C["bad"], ls="--", lw=1.2, label=t("g_pmax"))
    ax2.set_xticks(x)
    ax2.set_xticklabels(keys, fontsize=6.8, rotation=18, ha="right")
    ax2.set_ylabel(t("h_dp", u=punit()))
    ax2.set_title(t("g_struct"), fontsize=9.5, fontweight="bold")
    ax2.legend(fontsize=6.5, ncol=2)

    ax3 = fig.add_axes([0.56, 0.09, 0.40, 0.41])
    ecd = [r["ecd_bottom"] for r in results]
    rho = [r["itv"]["rho"] for r in results]
    ax3.bar(x - 0.18, rho, width=0.34, color=C["grey_lt"],
            label=t("g_mud"))
    ax3.bar(x + 0.18, ecd, width=0.34, color=C["yellow"],
            edgecolor=C["accent2"], lw=0.6, label=t("g_ecd_bh"))
    for i, (a, b) in enumerate(zip(rho, ecd)):
        ax3.text(i + 0.18, b + 0.01, f"+{b - a:.3f}", ha="center", fontsize=6)
    ax3.set_xticks(x)
    ax3.set_xticklabels(keys, fontsize=6.8, rotation=18, ha="right")
    ax3.set_ylabel(t("g_density"))
    ax3.set_ylim(min(rho) * 0.9, max(ecd) * 1.08)
    ax3.set_title(t("g_rho_ecd"), fontsize=9.5, fontweight="bold")
    ax3.legend(fontsize=6.5)

    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


# ==========================================================================
#  8. СТРАНИЦА ЗАМЕЧАНИЙ
# ==========================================================================

def page_notes(pdf, warnings_list, page_no):
    fig = page(A4)
    header(fig, "Замечания к исходным данным и рекомендации",
           "что необходимо уточнить для повышения достоверности расчёта")
    y = 0.86
    fig.text(0.05, y, "1. Замечания, выявленные при расчёте", fontsize=10,
             fontweight="bold", color=C["accent"])
    y -= 0.032
    for w in warnings_list:
        for ln in textwrap.wrap("•  " + w, 140):
            fig.text(0.06, y, ln, fontsize=7.6, color=C["text"])
            y -= 0.0195
        y -= 0.005
        if y < 0.42:
            break

    y = min(y, 0.42) - 0.02
    fig.text(0.05, y, "2. Данные, которые желательно добавить в файл",
             fontsize=10, fontweight="bold", color=C["accent"])
    y -= 0.032
    need = [
        "Насадки долот по каждой секции: количество и диаметр (в 1/32\"), "
        "либо TFA - без этого перепад на долоте и HSI носят условный характер.",
        "Паспортные характеристики ВЗД: типоразмер, рабочий расход, перепад "
        "давления на холостом ходу и под нагрузкой, момент, обороты.",
        "Перепад давления на телесистеме (MWD/LWD) при рабочем расходе.",
        "Параметры буровых насосов: тип, диаметр втулок, длина хода, "
        "коэффициент наполнения, максимальное давление обвязки, мощность.",
        "Схема наземной обвязки: длины и внутренние диаметры стояка, "
        "бурового рукава, вертлюга и ведущей трубы.",
        "Полный инклинометрический файл (MD / зенит / азимут через 10-30 м) - "
        "текущие 5 точек не позволяют корректно пересчитывать MD→TVD.",
        "Полная реология по каждой секции: показания вискозиметра Фанна "
        "(600/300/200/100/6/3 об/мин) и СНС 10 с / 10 мин. Для направления "
        "реология не задана вовсе.",
        "Коэффициент кавернозности по интервалам (по данным каверномера "
        "аналогичных скважин) - прямо влияет на скорость в затрубье и ЭЦП.",
        "Градиенты порового давления и давления гидроразрыва по разрезу - "
        "без них нельзя оценить, вписывается ли ЭЦП в «окно бурения». "
        "Особенно важно для интервалов солей (452-545, 672-840, 1226-1474 м) "
        "и траппов (879-1118 м).",
        "КНБК для эксплуатационной колонны и хвостовика - сейчас взяты "
        "ориентировочные шаблоны.",
        "Компоновка бурильной колонны выше КНБК (типоразмер и длины СБТ, ТБТ) "
        "для каждой секции.",
        "Температурный режим по стволу - влияет на реологию и плотность "
        "раствора на забое.",
        "Размер и плотность частиц шлама, требования по очистке ствола "
        "(для участков с зенитным углом 75-80° это критично).",
    ]
    for t in need:
        for ln in textwrap.wrap("•  " + t, 140):
            fig.text(0.06, y, ln, fontsize=7.6, color=C["text"])
            y -= 0.0195
        y -= 0.005

    footer(fig, WELL_CAPTION, page_no)
    pdf.savefig(fig)
    plt.close(fig)


# ==========================================================================
#  9. КРАТКИЙ ОТЧЁТ
# ==========================================================================

def brief_report(path, data, intervals, results, traj):
    """
    Краткий отчёт на одной-двух страницах: реквизиты, ключевые результаты
    по интервалам, схема конструкции, структура потерь и ЭЦП.
    """
    global WELL_CAPTION
    with PdfPages(path) as pdf:
        _brief_main(pdf, data, intervals, results, traj)
        _brief_checks(pdf, data, results)
        d = pdf.infodict()
        d["Title"] = f"Гидравлический расчёт (кратко) - {WELL_CAPTION}"
        d["Creator"] = f"{CFG.APP_NAME} {CFG.APP_VERSION} ({CFG.APP_AUTHOR})"
    return path


def _brief_head(fig, data):
    g = getattr(data, "general", {}) or {}
    logo = load_logo(CFG.APP_LOGO)
    if logo is not None:
        h = logo.shape[0] / logo.shape[1]
        w = 0.082
        ax = fig.add_axes([0.035, 0.918, w, w * h * 11.69 / 8.27])
        ax.imshow(logo)
        ax.axis("off")
    fig.text(0.128, 0.962, t("brief_title"),
             fontsize=13.0, fontweight="bold", va="center")
    fig.text(0.128, 0.937, t("brief_sub"), fontsize=9, color=C["accent"],
             va="center")

    req = [(t("r_client"), g.get("заказчик")),
           (t("r_field"), g.get("месторождение")),
           (t("r_pad"), g.get("куст")), (t("r_well"), g.get("скважина")),
           (t("r_welltype"), g.get("тип скважины")),
           (t("r_target"), g.get("проектный горизонт")),
           (t("r_author"), g.get("ответственный исполнитель")),
           (t("r_date"), g.get("дата расчёта"))]
    req = [(k, v) for k, v in req if v]
    for i, (k, v) in enumerate(req[:8]):
        col, row = divmod(i, 4)
        x = 0.585 + col * 0.215
        y = 0.968 - row * 0.0185
        fig.text(x, y, k + ":", fontsize=7.0, color="#6C6C6E", ha="right")
        fig.text(x + 0.008, y, str(v)[:26], fontsize=7.0,
                 fontweight="bold")
    fig.add_artist(Line2D([0.035, 0.965], [0.898, 0.898],
                          color=C["accent"], lw=1.4))
    fig.add_artist(Line2D([0.035, 0.150], [0.898, 0.898],
                          color=C["yellow"], lw=4.0, solid_capstyle="butt"))


def _brief_main(pdf, data, intervals, results, traj):
    fig = page(A4)
    _brief_head(fig, data)

    pmp = dict(CFG.PUMPS)
    pmp.update((getattr(data, "extra", {}) or {}).get("pumps") or {})
    td = max(i["md_to"] for i in intervals)
    models = []
    for r in results:
        nm = MODEL_NAMES.get(r.get("model"), r.get("model"))
        if nm and nm not in models:
            models.append(nm)
    pump_txt = (pmp["тип"] + ", "
                + t("pumps_of", n=f"{pmp['количество_рабочих']:.0f}",
                    d=f"{pmp['диаметр_втулки_мм']:.0f}") + ", "
                + pfmt(pmp["макс_давление_МПа"] * 1e6, unit=True))
    line = t("br_head", td=f"{td:.0f}", n=len(results), pump=pump_txt,
             model=", ".join(models))
    y0 = 0.878
    for ln in textwrap.wrap(line, 150):
        fig.text(0.035, y0, ln, fontsize=7.4, color="#6C6C6E")
        y0 -= 0.017

    # ------------------------------------------------ сводная таблица ---
    rows, colors = [], []
    for r in results:
        v = [s.V for s in r["ann"]]
        conc = max((getattr(s, "conc", 0) for s in r["ann"]), default=0) * 100
        cr = r.get("crit") or CFG.CRIT
        bad = (r["load_pct"] > cr["Загрузка_насоса_%"]
               or conc > cr["Cшлам_макс_%"]
               or r.get("bed_max", 0) * 100 > cr.get("Подушка_макс_доля",
                                                     0.1) * 100)
        rows.append([
            r["key"], f"{r['md_from']:.0f}-{r['td']:.0f}",
            f"{r['itv']['bit_mm']:.1f}", f"{r['q_lps']:.0f}",
            pfmt(r["p_start"]) if r.get("p_start") else "-",
            pfmt(r["p_pump"]), f"{r['load_pct']:.0f}",
            f"{r['spm']:.0f}", pfmt(r["dp_bit"]),
            f"{r['bit']['hsi_kW_cm2']:.3f}",
            f"{min(v):.2f}-{max(v):.2f}" if v else "-",
            f"{r.get('bed_max', 0) * 100:.0f}", f"{conc:.1f}",
            f"{r['itv']['rho']:.2f}", f"{r['ecd_bottom']:.3f}",
        ])
        colors.append(C["bad"] if bad else C["ok"])
    ax = fig.add_axes([0.035, 0.575, 0.93, 0.262])
    draw_table(ax, [t("h_interval"), t("h_md"), t("h_bit_d"), t("h_q"),
                    t("h_pstart", u=punit()), t("h_pend", u=punit()),
                    t("h_loadpct"), t("h_spm"),
                    t("h_dp", u=punit()), t("h_hsi"), t("h_vann"),
                    t("h_bed"), t("h_conc"), t("h_rho"), t("h_ecd")],
               rows, col_w=[0.108, 0.086, 0.050, 0.042, 0.066, 0.066,
                            0.046, 0.052, 0.058, 0.058, 0.080, 0.057,
                            0.049, 0.046, 0.050],
               row_colors=colors, fontsize=6.9, header_fs=6.6,
               bold_cols=(4, 5))
    block_title(fig, 0.035, 0.845, t("br_results"))

    # ---------------------------------------------------- схема ствола --
    ax1 = fig.add_axes([0.055, 0.090, 0.185, 0.415])
    _draw_well_schematic(ax1, data, intervals, td)
    ax1.set_title(t("br_scheme"), fontsize=9.5, fontweight="bold", pad=8)

    # ------------------------------------------- структура потерь -------
    ax2 = fig.add_axes([0.315, 0.085, 0.30, 0.420])
    keys = [r["key"] for r in results]
    x = np.arange(len(results))
    parts = {"обвязка": [P(r["dp_surface"]) for r in results],
             "колонна": [P(r["dp_inside"]) for r in results],
             "долото": [P(r["dp_bit"]) for r in results],
             "затрубье": [P(r["dp_ann"]) for r in results]}
    bottom = np.zeros(len(results))
    for (nm, vals), col in zip(parts.items(),
                               [C["grey_lt"], C["accent"], C["bit"],
                                C["yellow"]]):
        ax2.bar(x, vals, bottom=bottom, label=nm, color=col, width=0.6)
        bottom += np.array(vals)
    ax2.axhline(P(pmp["макс_давление_МПа"] * 1e6), color=C["bad"], ls="--",
                lw=1.2, label=t("g_pmax"))
    ax2.set_xticks(x)
    ax2.set_xticklabels(keys, fontsize=6.8, rotation=18, ha="right")
    ax2.set_ylabel(t("h_dp", u=punit()), fontsize=8)
    ax2.set_title(t("g_balance"), fontsize=9.5, fontweight="bold")
    ax2.legend(fontsize=6.4, ncol=2)
    ax2.tick_params(labelsize=7)

    # ------------------------------------------- ЭЦП и окно бурения -----
    ax3 = fig.add_axes([0.680, 0.085, 0.285, 0.420])
    rho = [r["itv"]["rho"] for r in results]
    ecd = [r["ecd_bottom"] for r in results]
    ax3.bar(x - 0.19, rho, width=0.36, color=C["grey_lt"],
            label=t("g_mud"))
    ax3.bar(x + 0.19, ecd, width=0.36, color=C["yellow"],
            edgecolor=C["accent2"], lw=0.6, label=t("g_ecd_bh"))

    # Диапазон осей задаётся плотностями раствора: границы окна бурения
    # на истощённых или высоконапорных пластах уходят далеко и сплющили бы
    # столбцы. Границы вне поля подписываются у края.
    lo = min(rho) * 0.90
    hi = max(ecd) * 1.10
    rng = hi - lo
    shown_p = shown_f = False
    for i, r in enumerate(results):
        w = r.get("window")
        if not w:
            continue
        for key, col, nm, shown in (("pore", C["ok"], t("br_pore"), "p"),
                                    ("frac", C["bad"], t("br_frac"), "f")):
            vals = [v for v in w[key] if v is not None]
            if not vals:
                continue
            val = vals[-1]
            lbl = None
            if (nm == t("br_pore") and not shown_p) or (
                    nm == t("br_frac") and not shown_f):
                lbl = nm
            if nm == t("br_pore"):
                shown_p = True
            else:
                shown_f = True
            if lo <= val <= hi:
                ax3.plot([i - 0.45, i + 0.45], [val] * 2, color=col,
                         lw=1.8, label=lbl)
            else:
                edge = hi - rng * 0.02 if val > hi else lo + rng * 0.02
                ax3.plot([i - 0.45, i + 0.45], [edge] * 2, color=col,
                         lw=1.4, ls=":", label=lbl)
                ax3.annotate(f"{val:.2f}", xy=(i, edge), fontsize=5.6,
                             color=col, ha="center",
                             va="bottom" if val > hi else "top",
                             xytext=(0, 3 if val > hi else -3),
                             textcoords="offset points")
    for i, (a, b) in enumerate(zip(rho, ecd)):
        ax3.text(i + 0.19, b + rng * 0.015, f"+{b - a:.3f}",
                 ha="center", fontsize=6.0)

    ax3.set_xticks(x)
    ax3.set_xticklabels(keys, fontsize=6.8, rotation=18, ha="right")
    ax3.set_ylabel(t("g_density"), fontsize=8)
    ax3.set_ylim(lo, hi + rng * 0.10)
    ax3.set_title(t("br_window"), fontsize=9.5, fontweight="bold")
    ax3.legend(fontsize=6.2, ncol=2, loc="upper left")
    ax3.tick_params(labelsize=7)

    footer(fig, WELL_CAPTION, 1, mark=False)
    pdf.savefig(fig)
    plt.close(fig)


def _brief_checks(pdf, data, results):
    fig = page(A4)
    _brief_head(fig, data)
    block_title(fig, 0.035, 0.860, t("br_assess"))

    from hydraulics_solver import assess
    names, matrix, vals = [], [], []
    for r in results:
        a = assess(r)
        if not names:
            names = [t[0] for t in a]
        matrix.append([t[3] for t in a])
        vals.append([t[1] for t in a])

    keys = [r["key"] for r in results]
    ncol = len(keys)

    # матрица «критерий - интервал» занимает верхние две трети листа,
    # нижняя треть отведена под перечень принятых критериев
    top, bottom = 0.845, 0.360
    ax = fig.add_axes([0.035, bottom, 0.93, top - bottom])
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    wl = 0.28
    wc = (1.0 - wl) / max(ncol, 1)
    rh = 1.0 / (len(names) + 1.3)

    ax.add_patch(Rectangle((0, 1 - rh), 1, rh, color=C["accent"],
                           transform=ax.transAxes))
    ax.add_patch(Rectangle((0, 1 - rh), 1, rh * 0.10, color=C["yellow"],
                           transform=ax.transAxes, zorder=3))
    ax.text(0.008, 1 - rh / 2, t("h_criterion"), fontsize=7.4,
            color="white",
            fontweight="bold", va="center", transform=ax.transAxes)
    for j2, k in enumerate(keys):
        ax.text(wl + wc * (j2 + 0.5), 1 - rh / 2, k, fontsize=6.8,
                color="white", fontweight="bold", ha="center", va="center",
                transform=ax.transAxes)

    for i2, nm in enumerate(names):
        yy = 1 - rh * (i2 + 2)
        if i2 % 2 == 0:
            ax.add_patch(Rectangle((0, yy), 1, rh, color=C["row"],
                                   transform=ax.transAxes, zorder=0))
        ax.text(0.008, yy + rh / 2, nm, fontsize=7.0, va="center",
                transform=ax.transAxes)
        for j2 in range(ncol):
            st = matrix[j2][i2]
            ax.text(wl + wc * (j2 + 0.5), yy + rh / 2, vals[j2][i2],
                    fontsize=6.6, ha="center", va="center",
                    color=status_color(st), fontweight="bold",
                    transform=ax.transAxes, zorder=2)

    # условные обозначения - одной строкой
    y = bottom - 0.035
    x = 0.040
    for col, name, d in [(C["ok"], t("st_ok"), t("st_ok_d")),
                         (C["warn"], t("st_warn"), t("st_warn_d")),
                         (C["bad"], t("st_bad"), t("st_bad_d"))]:
        fig.text(x, y, "\u25cf", fontsize=9.5, color=col)
        fig.text(x + 0.016, y, name, fontsize=8.2, fontweight="bold",
                 color=col)
        fig.text(x + 0.016 + 0.075, y, f"- {d}", fontsize=8.2,
                 color="#3A3A3C")
        x += 0.265

    y -= 0.042
    block_title(fig, 0.035, y, t("br_criteria"))
    cr = results[0].get("crit") or CFG.CRIT
    rows = [
        [t("cr_vmin"), t("cr_vmin_v", a=f"{cr['Vкц_мин_верт_мс']:.2f}",
                         b=f"{cr['Vкц_мин_наклон_мс']:.2f}")],
        [t("cr_vmax"), f"{cr['Vкц_макс_мс']:.2f}"],
        [t("cr_conc"), f"{cr['Cшлам_макс_%']:.1f}"],
        [t("cr_bed"), f"{cr.get('Подушка_макс_доля', 0.1) * 100:.0f}"],
        [t("cr_hsi"), f"{cr['HSI_мин_кВт_см2']:.3f}"],
        [t("cr_ecd"), f"{cr['ЭЦП_запас_гсм3']:.2f}"],
        [t("cr_load"), f"{cr['Загрузка_насоса_%']:.0f}"],
    ]
    ax2 = fig.add_axes([0.035, 0.075, 0.53, y - 0.020 - 0.075])
    draw_table(ax2, [t("h_criterion"), t("h_value")], rows,
               col_w=[0.60, 0.40], fontsize=7.4, header_fs=7.4)

    note = t("br_note")
    yy = y - 0.030
    for block in note.split("\n\n"):
        for ln in textwrap.wrap(block, 58):
            fig.text(0.600, yy, ln, fontsize=7.4, color="#5C5C5E")
            yy -= 0.018
        yy -= 0.008

    footer(fig, WELL_CAPTION, 2, mark=False)
    pdf.savefig(fig)
    plt.close(fig)
