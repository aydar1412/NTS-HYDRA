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
 РЕОЛОГИЯ И ТЕЧЕНИЕ В КОЛОННЕ И ЗАТРУБЬЕ
==========================================================================
 Поддерживаются три модели:
   herschel_bulkley  tau = tau0 + K*gamma^n     (основная, API RP 13D)
   power_law         tau = K*gamma^n            (tau0 = 0)
   bingham           tau = tau0 + mu_p*gamma    (n = 1)

 Все три считаются ОДНИМ решателем: ламинарный режим - численным
 решением профиля скорости относительно напряжения на стенке,
 турбулентный - через обобщённое число Рейнольдса Метцнера-Рида.

 Учитываются:
   - эксцентриситет колонны в стволе (Haciislamoglu & Langlinais, 1990;
     Haciislamoglu & Cartalos, 1994);
   - вращение колонны (снижение эффективной вязкости за счёт
     дополнительного сдвига и вихри Тейлора).

 ВАЖНО о константах прибора. Вискозиметр Fann 35 (R1-B1, пружина F1):
     скорость сдвига  gamma = 1,7023 * об/мин
     напряжение       tau[Па] = 0,511266 * показание шкалы
 Именно при этих константах выполняется промысловое тождество
     PV[сПз] = theta600 - theta300
 с точностью 0,1 %. Если взять часто встречающийся множитель 0,4788,
 пластическая вязкость завышается на 6,7 %.
==========================================================================
"""

import math

import numpy as np

import hydraulics_config as CFG
from hydraulics_lang import t

# --- константы вискозиметра Fann 35 -------------------------------------
DIAL_TO_PA = 0.511266          # показание шкалы -> Па
RPM_TO_SHEAR = 1.7023          # об/мин -> 1/с

SHEAR = {600: 600 * RPM_TO_SHEAR, 300: 300 * RPM_TO_SHEAR,
         200: 200 * RPM_TO_SHEAR, 100: 100 * RPM_TO_SHEAR,
         6: 6 * RPM_TO_SHEAR, 3: 3 * RPM_TO_SHEAR}


# ==========================================================================
#  1. РЕОЛОГИЧЕСКАЯ МОДЕЛЬ
# ==========================================================================

class Rheology:
    """
    Реологическая модель раствора, восстановленная по показаниям
    вискозиметра либо по паре PV / ДНС.
    """

    def __init__(self, rho_gcm3, fann=None, pv_cP=None, yp_lb100=None,
                 model=None, name=""):
        self.name = name
        self.rho = rho_gcm3 * 1000.0
        self.rho_gcm3 = rho_gcm3
        self.model = model or getattr(CFG, "RHEOLOGY_MODEL",
                                      "herschel_bulkley")

        f = {k: v for k, v in (fann or {}).items()
             if isinstance(v, (int, float)) and v is not None and v > 0}
        self.measured = bool(f.get("t600") and f.get("t300"))

        if not self.measured:
            # показания восстанавливаются из PV и ДНС по модели Бингама
            pv = pv_cP if pv_cP is not None else CFG.DEFAULT_RHEOLOGY["pv_cP"]
            yp = (yp_lb100 if yp_lb100 is not None
                  else CFG.DEFAULT_RHEOLOGY["yp_lb100ft2"])
            f = {"t600": 2.0 * pv + yp, "t300": pv + yp,
                 "t200": pv * 2.0 / 3.0 + yp, "t100": pv / 3.0 + yp,
                 "t6": pv * 0.02 + yp, "t3": pv * 0.01 + yp}
        self.dial = f

        self.pv = f["t600"] - f["t300"]                 # сПз
        self.yp = f["t300"] - self.pv                   # фунт/100 фут2
        self.mu_p = self.pv * 1e-3                      # Па*с
        self.tau_y_bingham = self.yp * DIAL_TO_PA       # Па

        self._fit()

    # ------------------------------------------------------------------
    def _fit(self):
        """Определение tau0, K, n по показаниям вискозиметра."""
        d = self.dial
        t600, t300 = d["t600"], d["t300"]
        t6 = d.get("t6")
        t3 = d.get("t3")

        if self.model == "bingham":
            self.tau0 = self.tau_y_bingham
            self.n = 1.0
            self.K = self.mu_p
            self.fit_note = "модель Бингама"
            return

        if self.model == "power_law" or not (t3 and t6):
            self.tau0 = 0.0
            self.n = math.log(t600 / t300) / math.log(2.0)
            self.n = min(max(self.n, 0.10), 1.0)
            self.K = DIAL_TO_PA * t600 / (SHEAR[600] ** self.n)
            self.fit_note = ("степенная модель"
                             if self.model == "power_law"
                             else "степенная (нет theta6 / theta3)")
            return

        # --- Гершель-Балкли ---
        # начальное приближение: tau0 = 2*theta3 - theta6 (API RP 13D)
        tau0 = max(2.0 * t3 - t6, 0.0) * DIAL_TO_PA
        best = None
        # уточнение методом наименьших квадратов по всем показаниям
        pts = [(SHEAR[int(k[1:])], DIAL_TO_PA * v)
               for k, v in d.items()
               if k.startswith("t") and k[1:].isdigit()]
        pts.sort()
        tau_min = min(p[1] for p in pts)
        for cand in np.linspace(0.0, 0.98 * tau_min, 60):
            ys = [(g, t - cand) for g, t in pts if t - cand > 1e-9]
            if len(ys) < 2:
                continue
            lx = np.log([g for g, _ in ys])
            ly = np.log([t for _, t in ys])
            n = float(np.polyfit(lx, ly, 1)[0])
            n = min(max(n, 0.10), 1.0)
            K = float(np.exp(np.mean(ly - n * lx)))
            err = sum((cand + K * g ** n - t) ** 2 for g, t in pts)
            if best is None or err < best[0]:
                best = (err, cand, K, n)
        _, self.tau0, self.K, self.n = best
        self.fit_note = "Гершель-Балкли (МНК по показаниям Фанна)"

    # ------------------------------------------------------------------
    def tau(self, gamma):
        """Напряжение сдвига, Па."""
        gamma = max(gamma, 0.0)
        return self.tau0 + self.K * gamma ** self.n

    def gamma_of(self, tau):
        """Обратная зависимость: скорость сдвига при заданном напряжении."""
        if tau <= self.tau0:
            return 0.0
        return ((tau - self.tau0) / self.K) ** (1.0 / self.n)

    def mu_app(self, gamma):
        """Кажущаяся (эффективная) вязкость при данной скорости сдвига."""
        gamma = max(gamma, 1e-6)
        return self.tau(gamma) / gamma

    def local_index(self, gamma):
        """
        Локальный показатель нелинейности N = d(ln tau)/d(ln gamma).
        Для степенной модели N = n, для Гершеля-Балкли зависит от gamma.
        """
        gamma = max(gamma, 1e-6)
        t = self.tau(gamma)
        if t <= 0:
            return self.n
        return self.n * self.K * gamma ** self.n / t


# ==========================================================================
#  2. ЛАМИНАРНОЕ ТЕЧЕНИЕ: РЕШЕНИЕ ОТНОСИТЕЛЬНО НАПРЯЖЕНИЯ НА СТЕНКЕ
# ==========================================================================

def _pipe_velocity(rh: Rheology, tau_w, R, npts=200):
    """Средняя скорость в трубе при заданном напряжении на стенке."""
    if tau_w <= rh.tau0:
        return 0.0
    r = np.linspace(0.0, R, npts)
    tau_r = tau_w * r / R
    # профиль скорости: u(r) = int_r^R gamma(tau(s)) ds
    g = np.array([rh.gamma_of(t) for t in tau_r])
    u = np.concatenate([[0.0], np.cumsum(0.5 * (g[1:] + g[:-1]) * np.diff(r))])
    u = u[-1] - u                                   # u(R) = 0
    # средняя по расходу: V = 2/R^2 * int_0^R u*r dr
    integ = np.trapezoid(u * r, r) if hasattr(np, "trapezoid") \
        else np.trapz(u * r, r)
    return 2.0 / R ** 2 * integ


def _slot_velocity(rh: Rheology, tau_w, H):
    """
    Средняя скорость в плоской щели полушириной H (половина радиального
    зазора). Для tau = tau0 + K*gamma^n решение получается в замкнутом виде:

        u(xi) = C * [ (1-a)^((n+1)/n) - (xi-a)^((n+1)/n) ],
        C = H * (tau_w/K)^(1/n) * n/(n+1),   a = tau0/tau_w,
        V = C * (1-a)^((n+1)/n) * [ 1 - (1-a)*n/(2n+1) ].

    Проверка: при n=1, tau0=0 даёт V = H*tau_w/(3*mu), что вместе с
    балансом сил dP/dL = tau_w/H приводит к dP/dL = 48*mu*V/(do-di)^2.
    """
    if tau_w <= rh.tau0:
        return 0.0
    a = rh.tau0 / tau_w
    n = rh.n
    C = H * (tau_w / rh.K) ** (1.0 / n) * n / (n + 1.0)
    return C * (1.0 - a) ** ((n + 1.0) / n) * (1.0 - (1.0 - a) * n /
                                               (2.0 * n + 1.0))


def _solve_tau_w(target_V, fn, lo, hi, iters=80):
    """Подбор напряжения на стенке под заданную среднюю скорость."""
    if target_V <= 0:
        return lo
    for _ in range(60):
        if fn(hi) >= target_V:
            break
        hi *= 2.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if fn(mid) < target_V:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ==========================================================================
#  3. КОЭФФИЦИЕНТ ТРЕНИЯ В ТУРБУЛЕНТНОМ РЕЖИМЕ
# ==========================================================================

def colebrook_fanning(Re, rel_rough):
    """
    Коэффициент трения Фаннинга по Колбруку для шероховатой трубы.
    Корреляция Доджа-Метцнера выведена для ГЛАДКОЙ трубы; реальные
    бурильные трубы с замками и износом дают заметно большие потери.
    """
    if Re <= 2100.0:
        return 16.0 / max(Re, 1e-9)
    fd = 0.02
    for _ in range(40):
        inv = -2.0 * math.log10(rel_rough / 3.7 + 2.51 / (Re * math.sqrt(fd)))
        fd_new = 1.0 / inv ** 2
        if abs(fd_new - fd) < 1e-10:
            fd = fd_new
            break
        fd = fd_new
    return fd / 4.0


def friction_factor(Re, N, geometry="pipe", d_h=None):
    """
    Коэффициент трения Фаннинга.
    Ламинарный режим: f = 16/Re для трубы и f = 24/Re для щели (затрубья).
    Множитель 24 обязателен: при 16/Re потери в затрубье занижаются на 33 %.
    Турбулентный: корреляция Доджа-Метцнера в форме API RP 13D.
    """
    lam_c = 16.0 if geometry == "pipe" else 24.0
    if Re <= 0:
        return lam_c / 1e-9, t("fl_laminar")

    Re_lam = 3470.0 - 1370.0 * N
    Re_tur = 4270.0 - 1370.0 * N
    a = (math.log10(N) + 3.93) / 50.0
    b = (1.75 - math.log10(N)) / 7.0

    if Re < Re_lam:
        return lam_c / Re, t("fl_laminar")
    f_l = lam_c / Re_lam
    f_t_at = a / (Re_tur ** b)
    if Re > Re_tur:
        return _rough(a / (Re ** b), Re, d_h), t("fl_turbulent")
    w = (Re - Re_lam) / max(Re_tur - Re_lam, 1e-9)
    return f_l + w * (f_t_at - f_l), t("fl_transition")


def _rough(f_smooth, Re, d_h):
    """Поправка на шероховатость: берётся большее из двух значений."""
    if not getattr(CFG, "ACCOUNT_ROUGHNESS", False) or not d_h:
        return f_smooth
    eps = getattr(CFG, "ROUGHNESS", 4.57e-5)
    return max(f_smooth, colebrook_fanning(Re, eps / d_h))


# ==========================================================================
#  4. ЭКСЦЕНТРИСИТЕТ
# ==========================================================================

def eccentricity_factor(e, n, d_in, d_out, regime="laminar"):
    """
    Отношение потерь в эксцентричном затрубье к концентричному.
    Haciislamoglu & Langlinais (1990) - ламинарный режим,
    Haciislamoglu & Cartalos (1994) - турбулентный.
    Область применимости: 0,3 <= d_in/d_out <= 0,9; 0 <= e <= 0,95.
    """
    if e <= 0:
        return 1.0
    e = min(max(e, 0.0), 0.95)
    r = min(max(d_in / d_out, 0.3), 0.9)
    n = min(max(n, 0.4), 1.0)
    sq = math.sqrt(n)
    if regime == "turbulent":
        R = (1.0 - 0.048 * (e / n) * r ** 0.8454
             - (2.0 / 3.0) * e ** 2 * sq * r ** 0.1852
             + 0.285 * e ** 3 * sq * r ** 0.2527)
    else:
        R = (1.0 - 0.072 * (e / n) * r ** 0.8454
             - 1.5 * e ** 2 * sq * r ** 0.1852
             + 0.96 * e ** 3 * sq * r ** 0.2527)
    return min(max(R, 0.35), 1.0)


def eccentricity_at(inc_deg, centralized=False):
    """
    Оценка эксцентриситета по зенитному углу.
    В вертикали колонна близка к оси, в наклонном стволе ложится
    на нижнюю стенку. Границы задаются в конфигурации.
    """
    cfg = getattr(CFG, "ECCENTRICITY", None)
    if cfg is None:
        cfg = {"вертикаль": 0.0, "угол_начала": 15.0,
               "угол_полки": 60.0, "наклон": 0.80,
               "с_центраторами": 0.30}
    if centralized:
        return cfg["с_центраторами"]
    a0, a1 = cfg["угол_начала"], cfg["угол_полки"]
    if inc_deg <= a0:
        return cfg["вертикаль"]
    if inc_deg >= a1:
        return cfg["наклон"]
    w = (inc_deg - a0) / max(a1 - a0, 1e-9)
    return cfg["вертикаль"] + w * (cfg["наклон"] - cfg["вертикаль"])


# ==========================================================================
#  5. ВРАЩЕНИЕ КОЛОННЫ
# ==========================================================================

def rotation_effect(rh: Rheology, rpm, d_in, d_out, gamma_axial):
    """
    Влияние вращения на потери в затрубье. Возвращает
    (множитель к потерям, число Тейлора, вклад сдвига от вращения).

    Учитываются два встречных механизма:
      1) вращение добавляет скорость сдвига, эффективная вязкость
         псевдопластичной жидкости падает - потери снижаются;
      2) при потере устойчивости течения Куэтта возникают вихри Тейлора -
         потери растут.
    Модель оценочная; отключается параметром ROTATION_MODEL = "off".
    """
    mode = getattr(CFG, "ROTATION_MODEL", "shear+taylor")
    if mode == "off" or not rpm or rpm <= 0:
        return 1.0, 0.0, 0.0

    r_i, r_o = d_in / 2.0, d_out / 2.0
    gap = max(r_o - r_i, 1e-6)
    omega = 2.0 * math.pi * rpm / 60.0
    gamma_rot = omega * r_i / gap

    # 1) снижение вязкости из-за добавочного сдвига
    g_ax = max(gamma_axial, 1e-6)
    g_eff = math.sqrt(g_ax ** 2 + gamma_rot ** 2)
    k_shear = rh.mu_app(g_eff) / rh.mu_app(g_ax)
    k_shear = min(max(k_shear, 0.4), 1.0)

    # 2) вихри Тейлора.
    # Число Тейлора показывает лишь возможность их возникновения. Осевой
    # поток вихри подавляет, поэтому величина надбавки определяется не
    # самим Ta, а отношением окружной скорости к осевой: добавочная
    # диссипация пропорциональна квадрату этого отношения. При
    # V_окр << V_ос вращение на потери практически не влияет.
    mu = rh.mu_app(g_eff)
    Ta = (rh.rho ** 2 * omega ** 2 * r_i * gap ** 3) / max(mu ** 2, 1e-12)
    Ta_cr = 1700.0
    k_taylor = 1.0
    if "taylor" in mode and Ta > Ta_cr:
        v_tang = omega * r_i
        v_ax = max(gamma_axial * gap / 12.0, 1e-6)   # обратно к скорости
        ratio = v_tang / v_ax
        coef = getattr(CFG, "TAYLOR_COEF", 0.15)
        cap = getattr(CFG, "TAYLOR_CAP", 1.30)
        k_taylor = min(1.0 + coef * ratio ** 2, cap)

    if mode == "shear":
        return k_shear, Ta, gamma_rot
    return k_shear * k_taylor, Ta, gamma_rot


# ==========================================================================
#  6. ОСНОВНЫЕ ФУНКЦИИ РАСЧЁТА УЧАСТКА
# ==========================================================================

class FlowResult:
    __slots__ = ("dpdl", "V", "Re", "mode", "tau_w", "gamma_w", "mu_eff",
                 "N", "k_ecc", "k_rot", "Ta")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k, 0.0))


def pipe_flow(Q, d_in, rh: Rheology):
    """Течение внутри трубы. Q м3/с, d_in м."""
    if d_in <= 0 or Q <= 0:
        return FlowResult(mode="-")
    R = d_in / 2.0
    A = math.pi * R ** 2
    V = Q / A

    tau_w = _solve_tau_w(V, lambda t: _pipe_velocity(rh, t, R),
                         rh.tau0 + 1e-9, max(rh.tau0 * 2.0, 1.0))
    gamma_w = rh.gamma_of(tau_w)
    gamma_nom = 8.0 * V / d_in
    N = rh.local_index(max(gamma_w, gamma_nom))
    mu_eff = rh.mu_app(max(gamma_nom, 1e-6))

    Re = rh.rho * V * d_in / max(mu_eff, 1e-9)
    f, mode = friction_factor(Re, N, "pipe", d_in)

    if mode == t("fl_laminar"):
        dpdl = 4.0 * tau_w / d_in            # точное решение
    else:
        dpdl = 2.0 * f * rh.rho * V * V / d_in

    return FlowResult(dpdl=dpdl, V=V, Re=Re, mode=mode, tau_w=tau_w,
                      gamma_w=gamma_w, mu_eff=mu_eff, N=N,
                      k_ecc=1.0, k_rot=1.0)


def annulus_flow(Q, d_out, d_in, rh: Rheology, ecc=0.0, rpm=0.0):
    """Течение в затрубье. Модель щели с поправками на эксцентриситет
    и вращение колонны."""
    if d_out <= d_in or Q <= 0:
        return FlowResult(mode="-")
    A = math.pi * (d_out ** 2 - d_in ** 2) / 4.0
    V = Q / A
    h = d_out - d_in                       # гидравлический диаметр
    H = h / 4.0                            # полуширина эквивалентной щели

    tau_w = _solve_tau_w(V, lambda t: _slot_velocity(rh, t, H),
                         rh.tau0 + 1e-9, max(rh.tau0 * 2.0, 1.0))
    gamma_w = rh.gamma_of(tau_w)
    gamma_nom = 12.0 * V / h
    N = rh.local_index(max(gamma_w, gamma_nom))
    mu_eff = rh.mu_app(max(gamma_nom, 1e-6))

    Re = rh.rho * V * h / max(mu_eff, 1e-9)
    f, mode = friction_factor(Re, N, "annulus", h)

    if mode == t("fl_laminar"):
        dpdl = tau_w / H                    # точное решение для щели
    else:
        dpdl = 2.0 * f * rh.rho * V * V / h

    k_ecc = eccentricity_factor(
        ecc, N, d_in, d_out,
        "turbulent" if mode == t("fl_turbulent") else "laminar")
    k_rot, Ta, _ = rotation_effect(rh, rpm, d_in, d_out, gamma_nom)

    return FlowResult(dpdl=dpdl * k_ecc * k_rot, V=V, Re=Re, mode=mode,
                      tau_w=tau_w, gamma_w=gamma_w, mu_eff=mu_eff, N=N,
                      k_ecc=k_ecc, k_rot=k_rot, Ta=Ta)


# ==========================================================================
#  7. ДАВЛЕНИЕ СТРАГИВАНИЯ (РАЗРУШЕНИЕ СТРУКТУРЫ)
# ==========================================================================

def gel_break_pressure(snс_10min_lb100, parts, ann_segments):
    """
    Давление, необходимое для страгивания раствора после стоянки.
    Для трубы:   dP = 4*tau_gel*L/D,  для затрубья: dP = 4*tau_gel*L/(D-d).
    Возвращает (в колонне, в затрубье, суммарно), Па.
    """
    tau = (snс_10min_lb100 or 0.0) * DIAL_TO_PA
    if tau <= 0:
        return 0.0, 0.0, 0.0
    dp_in = sum(4.0 * tau * (p.md_bot - p.md_top) / (p.id_mm * 1e-3)
                for p in parts if getattr(p, "id_mm", 0) > 0)
    dp_an = sum(4.0 * tau * (s.md_bot - s.md_top) /
                ((s.d_out - s.d_in) * 1e-3)
                for s in ann_segments if s.d_out > s.d_in)
    return dp_in, dp_an, dp_in + dp_an


# ==========================================================================
#  8. ВЛИЯНИЕ ТЕМПЕРАТУРЫ И ДАВЛЕНИЯ НА ПЛОТНОСТЬ
# ==========================================================================

def density_at(rho_surf, T_degC, P_Pa, T0=20.0, P0=101325.0):
    """
    Плотность раствора на глубине.
    rho(T,P) = rho0 * [1 + beta_p*(P - P0) - beta_t*(T - T0)]

    Сжимаемость и температурное расширение задаются в конфигурации.
    Для раствора на водной основе типично beta_p ~ 3e-10 1/Па,
    beta_t ~ 3e-4 1/°C: на 1500 м это даёт около 0,01-0,02 г/см3.
    Давление сжимает раствор, нагрев его расширяет, эффекты частично
    компенсируют друг друга.
    """
    bp = getattr(CFG, "MUD_COMPRESSIBILITY", 3.0e-10)
    bt = getattr(CFG, "MUD_THERMAL_EXPANSION", 3.0e-4)
    k = 1.0 + bp * (P_Pa - P0) - bt * (T_degC - T0)
    return rho_surf * min(max(k, 0.90), 1.10)


def temperature_profile(temp_points, tvd, T_surface=None):
    """Температура на заданной глубине по вертикали, °C."""
    if not temp_points:
        grad = getattr(CFG, "GEOTHERMAL_GRADIENT", 0.022)   # °C/м
        T0 = T_surface if T_surface is not None else getattr(
            CFG, "SURFACE_TEMPERATURE", 6.0)
        return T0 + grad * tvd
    xs = [p[0] for p in temp_points]
    ys = [p[1] for p in temp_points]
    return float(np.interp(tvd, xs, ys))


# ==========================================================================
#  9. ОПТИМИЗАЦИЯ НАСАДОК ДОЛОТА
# ==========================================================================

def optimum_bit_share(criterion="power", m=1.86):
    """
    Классическая оптимизация промывки долота.
    Потери в циркуляционной системе растут как Q^m (m ~ 1,86 при
    турбулентном течении). Доля перепада на долоте, при которой
    достигается максимум:
      - гидравлической мощности на долоте:  m / (m + 1)
      - силы удара струи:                   m / (m + 2)
    """
    if criterion == "impact":
        return m / (m + 2.0)
    return m / (m + 1.0)


def optimum_nozzles(p_max_Pa, dp_share, Q, rho, n_nozzles=6):
    """
    Подбор насадок под заданную долю перепада на долоте.
    Возвращает (TFA дюйм2, количество, размер в 1/32", перепад Па).
    """
    dp = p_max_Pa * dp_share
    A = Q / CFG.CD_NOZZLE * math.sqrt(rho / (2.0 * dp))     # м2
    tfa = A / 0.0254 ** 2
    best = None
    for cnt in (n_nozzles, n_nozzles - 1, n_nozzles + 1, 5, 4, 3):
        if cnt < 3:
            continue
        d32 = round(math.sqrt(4.0 * tfa / cnt / math.pi) * 32.0)
        if 8 <= d32 <= 28:
            got = cnt * math.pi / 4.0 * (d32 / 32.0) ** 2
            err = abs(got - tfa) / tfa
            if best is None or err < best[2]:
                best = (cnt, d32, err)
    if best is None:
        return tfa, None, None, dp
    return tfa, best[0], best[1], dp
