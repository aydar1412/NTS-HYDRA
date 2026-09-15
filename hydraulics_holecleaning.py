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
 ОЧИСТКА СТВОЛА И ПЕРЕНОС ШЛАМА
==========================================================================
 Прежняя модель (осаждение частицы с поправкой на косинус угла) описывает
 только вертикальный ствол. В наклонном стволе механизм другой: шлам
 оседает на нижнюю стенку и образует подушку. Здесь реализованы три
 режима по зенитному углу.

   alpha < 30 град   - режим взвеси.
       Работает баланс скорости потока и скорости осаждения частицы.

   30 <= alpha < 55  - режим сползающей подушки. Самый тяжёлый.
       Поверхность подушки наклонена к горизонту на угол beta = 90 - alpha.
       Когда beta превышает угол естественного откоса шлама, подушка
       теряет устойчивость и сползает вниз по стволу. Промысловый опыт
       (худшая очистка при 40-60 град) объясняется именно этим.

   alpha >= 55       - режим неподвижной подушки.
       Подушка устойчива, разрушается только потоком. Критерий срыва
       частицы со свода подушки - критерий Шилдса с поправкой на уклон:

           tau_c = theta_c * (rho_s - rho_f) * g * d
           theta_c(beta) = theta_c0 * cos(beta) * (1 - tg(beta)/tg(phi))

       где phi - угол естественного откоса шлама.

 Замыкание по высоте подушки. Если скорость потока ниже критической,
 подушка нарастает, сечение сужается, скорость растёт. Равновесная
 высота подушки - та, при которой скорость становится равной критической.
 Это даёт не качественную оценку, а число: высоту подушки в процентах
 от диаметра ствола и связанный с ней рост ЭЦП.
==========================================================================
"""

import math

import numpy as np

import hydraulics_config as CFG
from hydraulics_rheology import Rheology, friction_factor

G = 9.81


# ==========================================================================
#  1. ОСАЖДЕНИЕ ОДИНОЧНОЙ ЧАСТИЦЫ
# ==========================================================================

def slip_velocity(rh: Rheology, d_part, rho_s, gamma_ref=None, V_ann=0.5,
                  dh=0.05):
    """
    Скорость свободного осаждения частицы, м/с. Итерация по коэффициенту
    лобового сопротивления; эффективная вязкость берётся при скорости
    сдвига, характерной для затрубья.
    """
    gamma = gamma_ref if gamma_ref else 12.0 * max(V_ann, 0.05) / max(dh, 1e-3)
    mu = min(max(rh.mu_app(gamma), 1e-3), 5.0)
    vs = 0.15
    for _ in range(80):
        Re_p = max(rh.rho * vs * d_part / mu, 1e-4)
        if Re_p < 1.0:
            Cd = 24.0 / Re_p
        elif Re_p < 1000.0:
            Cd = 24.0 / Re_p * (1.0 + 0.15 * Re_p ** 0.687)
        else:
            Cd = 0.44
        vs_new = math.sqrt(4.0 * G * d_part * (rho_s - rh.rho) /
                           (3.0 * Cd * rh.rho))
        if abs(vs_new - vs) < 1e-6:
            vs = vs_new
            break
        vs = 0.5 * (vs + vs_new)
    return vs, mu


# ==========================================================================
#  2. КРИТИЧЕСКАЯ СКОРОСТЬ СРЫВА ПОДУШКИ (КРИТЕРИЙ ШИЛДСА)
# ==========================================================================

def bed_shear_velocity(rh, tau_c, V_ref, dh):
    """Скорость потока, дающая на стенке касательное напряжение tau_c."""
    gamma = 12.0 * max(V_ref, 0.1) / max(dh, 1e-3)
    mu = max(rh.mu_app(gamma), 1e-4)
    Re = rh.rho * max(V_ref, 0.1) * dh / mu
    N = rh.local_index(gamma)
    f, _ = friction_factor(Re, N, "annulus")
    return math.sqrt(2.0 * tau_c / (max(f, 1e-4) * rh.rho))


def critical_velocity(rh: Rheology, d_part, rho_s, inc_deg, V_ref, dh,
                      v_slip, crit=None):
    """
    Минимальная скорость восходящего потока, при которой шламовая подушка
    не образуется. Возвращает (V_crit, режим, признак сползания, tau_c).

    Огибающая закреплена физикой на обоих концах:

      вертикаль (alpha <= 30)   V_susp = v_slip / (1 - C_доп)
          условие удержания частицы во взвеси при допустимой
          концентрации шлама;

      горизонт  (alpha = 90)    V_bed по критерию Шилдса
          tau_c = theta_c * (rho_s - rho_f) * g * d,  tau_c = f*rho*V^2/2.

    Между ними скорость нарастает по гладкой функции, к которой в окне
    30-55 градусов добавляется надбавка за сползание подушки. Уклон
    поверхности подушки там превышает угол естественного откоса, шлам
    скатывается вниз по стволу и накапливается снова - это известное
    окно наихудшей очистки. Максимум надбавки приходится на середину окна.

    Прямое применение поправки Шилдса на уклон в этом окне невозможно:
    при beta -> phi критическое напряжение стремится к нулю, и формула
    показывала бы улучшение очистки там, где она в действительности
    наихудшая.
    """
    phi = getattr(CFG, "ANGLE_OF_REPOSE", 35.0)
    a_low = getattr(CFG, "INC_SUSPENSION", 30.0)
    a_slide = 90.0 - phi                       # граница сползания
    cc = crit or CFG.CRIT
    c_max = cc["Cшлам_макс_%"] / 100.0

    # --- нижний якорь: удержание во взвеси -------------------------------
    V_susp = v_slip / max(1.0 - c_max, 0.05)

    # --- верхний якорь: срыв подушки в горизонтальном стволе -------------
    theta_c = getattr(CFG, "SHIELDS_THETA", 0.24)
    tau_c = theta_c * (rho_s - rh.rho) * G * d_part
    V_bed = bed_shear_velocity(rh, tau_c, V_ref, dh)

    # нижняя граница по нормативному требованию предприятия: физический
    # критерий взвеси в вязком растворе даёт очень малые скорости, но
    # РД задают минимум независимо от реологии
    V_susp = max(V_susp, cc.get("Vкц_мин_верт_мс", 0.5))
    V_bed = max(V_bed, cc.get("Vкц_мин_наклон_мс", 0.9))

    if inc_deg <= a_low:
        return V_susp, REGIMES["suspension"], False, 0.0

    # --- переход от взвеси к подушке -------------------------------------
    w = min(max((inc_deg - a_low) / (90.0 - a_low), 0.0), 1.0)
    shape = math.sin(0.5 * math.pi * w) ** 0.7
    V = V_susp + (V_bed - V_susp) * shape

    sliding = inc_deg < a_slide
    if sliding:
        P = getattr(CFG, "SLIDING_BED_PENALTY", 0.25)
        u = (inc_deg - a_low) / max(a_slide - a_low, 1e-9)
        V *= 1.0 + P * math.sin(math.pi * min(max(u, 0.0), 1.0))

    regime = REGIMES["sliding"] if sliding else REGIMES["stationary"]
    return V, regime, sliding, tau_c


def rotation_credit(rpm):
    """
    Снижение требуемой скорости потока за счёт вращения колонны.
    Вращение механически разрушает подушку и выносит шлам из застойной
    зоны. Оценка эмпирическая, коэффициент задаётся в конфигурации.
    """
    if not rpm or rpm <= 0:
        return 1.0
    k = getattr(CFG, "ROTATION_CLEANING_CREDIT", 0.30)
    ref = getattr(CFG, "ROTATION_CLEANING_RPM", 120.0)
    return 1.0 - k * min(rpm / ref, 1.0)


# ==========================================================================
#  3. ГЕОМЕТРИЯ ШЛАМОВОЙ ПОДУШКИ
# ==========================================================================

def bed_area(h_bed, d_out):
    """Площадь сегмента подушки высотой h_bed в стволе диаметром d_out."""
    R = d_out / 2.0
    h = min(max(h_bed, 0.0), 2.0 * R)
    if h <= 0:
        return 0.0
    if h >= 2.0 * R:
        return math.pi * R ** 2
    th = math.acos(1.0 - h / R)
    return R ** 2 * (th - math.sin(th) * math.cos(th))


def equilibrium_bed(Q, d_out, d_in, V_crit):
    """
    Равновесная высота подушки: сечение сужается, пока скорость потока
    не достигнет критической. Возвращает (высота м, доля от диаметра,
    остаточная площадь, скорость над подушкой).
    """
    A_ann = math.pi * (d_out ** 2 - d_in ** 2) / 4.0
    V0 = Q / A_ann
    if V0 >= V_crit or V_crit <= 0:
        return 0.0, 0.0, A_ann, V0

    lo, hi = 0.0, d_out - d_in       # подушка не выше низа трубы
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        A = max(A_ann - bed_area(mid, d_out), 1e-6)
        if Q / A < V_crit:
            lo = mid
        else:
            hi = mid
    h = 0.5 * (lo + hi)
    A = max(A_ann - bed_area(h, d_out), 1e-6)
    return h, h / d_out, A, Q / A


# ==========================================================================
#  4. ОСНОВНАЯ ФУНКЦИЯ
# ==========================================================================

from hydraulics_lang import t


class _Regimes(dict):
    """Названия режимов на текущем языке отчёта."""

    def __getitem__(self, k):
        return t({"suspension": "hc_suspension",
                  "sliding": "hc_sliding",
                  "stationary": "hc_stationary"}[k])


REGIMES = _Regimes()


def hole_cleaning(rh: Rheology, Q, d_out, d_in, inc_deg, d_part, rho_s,
                  rop_mh, bit_d, rpm=0.0, crit=None):
    """
    Полная оценка очистки участка затрубья.
    Все линейные размеры в метрах, Q в м3/с, rop в м/ч.
    """
    A_ann = math.pi * (d_out ** 2 - d_in ** 2) / 4.0
    dh = d_out - d_in
    V = Q / A_ann if A_ann > 0 else 0.0

    q_cut = rop_mh / 3600.0 * math.pi * bit_d ** 2 / 4.0      # м3/с шлама

    a_low = getattr(CFG, "INC_SUSPENSION", 30.0)
    a_high = 90.0 - getattr(CFG, "ANGLE_OF_REPOSE", 35.0)

    out = {
        "V": V, "A_ann": A_ann, "dh": dh, "inc": inc_deg, "rpm": rpm,
        "q_cut": q_cut, "bed_h": 0.0, "bed_frac": 0.0, "A_flow": A_ann,
        "V_flow": V, "V_crit": 0.0, "sliding": False, "tau_c": 0.0,
    }

    v_slip, mu_eff = slip_velocity(rh, d_part, rho_s, V_ann=V, dh=dh)
    out["v_slip"] = v_slip
    out["mu_eff"] = mu_eff

    # ---------------------------------------------------- режим взвеси --
    if inc_deg < a_low:
        out["regime"] = REGIMES["suspension"]
        cc = (crit or CFG.CRIT)
        out["V_crit"] = max(
            v_slip / max(1.0 - cc["Cшлам_макс_%"] / 100.0, 0.05),
            cc.get("Vкц_мин_верт_мс", 0.5))
        v_tr = V - v_slip * math.cos(math.radians(inc_deg))
        out["v_transport"] = v_tr
        if v_tr <= 0.02:
            conc = 1.0
        else:
            conc = min(q_cut / (A_ann * v_tr), 1.0)
        out["conc"] = conc
        out["V_req"] = v_slip / max(1.0 - conc, 0.05) if conc < 1 else V * 3
        out["transport_ratio"] = max(v_tr, 0.0) / V if V > 0 else 0.0
        return out

    # ------------------------------------------- режимы с подушкой -----
    V_crit, regime, sliding, tau_c = critical_velocity(
        rh, d_part, rho_s, inc_deg, V, dh, v_slip, crit)
    V_crit *= rotation_credit(rpm)
    out.update({"V_crit": V_crit, "tau_c": tau_c, "sliding": sliding,
                "regime": regime})

    h, frac, A_flow, V_flow = equilibrium_bed(Q, d_out, d_in, V_crit)
    out.update({"bed_h": h, "bed_frac": frac, "A_flow": A_flow,
                "V_flow": V_flow})

    v_tr = max(V_flow - v_slip * math.cos(math.radians(inc_deg)), 0.02)
    conc = min(q_cut / (A_flow * v_tr), 1.0)
    # шлам, лежащий в подушке, добавляется к объёмной концентрации
    conc_bed = (A_ann - A_flow) / A_ann * (1.0 - getattr(
        CFG, "BED_POROSITY", 0.36))
    out["conc"] = min(conc + conc_bed, 1.0)
    out["conc_flow"] = conc
    out["conc_bed"] = conc_bed
    out["V_req"] = V_crit
    out["transport_ratio"] = v_tr / V_flow if V_flow > 0 else 0.0
    return out


# ==========================================================================
#  5. ТРЕБУЕМЫЙ РАСХОД
# ==========================================================================

def required_flow(rh, d_out, d_in, inc_deg, d_part, rho_s, rop_mh, bit_d,
                  rpm=0.0, q_hi=0.120):
    """Минимальный расход, при котором подушка не образуется, м3/с."""
    lo, hi = 1e-4, q_hi
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        r = hole_cleaning(rh, mid, d_out, d_in, inc_deg, d_part, rho_s,
                          rop_mh, bit_d, rpm)
        if r["bed_frac"] > 1e-4 or r["conc"] > CFG.CRIT["Cшлам_макс_%"] / 100:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
