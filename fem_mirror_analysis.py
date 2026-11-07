#!/usr/bin/env python3
"""
fem_mirror_analysis.py
======================
Análisis de desplazamientos de superficie de espejo a partir de resultados FEM.

Portado de las rutinas MATLAB: extract_rigid.m, zerfit.m, zernike.m,
zernikeISO2nm.m  (MatlabToolsJCL, IAC / JCL)


FORMATO DEL FICHERO DE ENTRADA TXT
===================================
Una línea por nodo FEM, campos separados por espacios o tabuladores:

    node_id   X   Y   Z   dX   dY   dZ        (7 columnas)
    X   Y   Z   dX   dY   dZ                  (6 columnas, sin node_id)

  - X, Y, Z    : coordenadas del nodo.
  - dX, dY, dZ : desplazamientos del nodo (mismas unidades que X Y Z).
  - Las líneas que empiezan por '#' o vacías se ignoran.
  - El orden de los nodos es indiferente.
  - Sólo deben exportarse los nodos de la SUPERFICIE ÓPTICA.
  - Si la primera columna tiene valores repetidos se interpreta como número
    de CASO DE CARGA (varios casos apilados, p. ej. AARESULTADOS2.TXT) y hay
    que elegir uno con --case.
  - El programa es agnóstico a unidades: RMS, PV y coeficientes salen en
    las unidades de dX dY dZ.


FLUJO DE TRABAJO
----------------
1. Leer la nube de puntos FEM.
2. Sistema de referencia (--frame):
     global  : Z del fichero = eje óptico (por defecto, como el MATLAB).
     bestfit : girar a la normal del plano best-fit (SVD).  Útil si el espejo
               plano está exportado inclinado.  NO usar en modelos parciales de
               espejos curvos ni en segmentos fuera de eje.
   Para un espejo plano exportado con Z = eje óptico ambos coinciden.
3. Triangulación de Delaunay → áreas nodales (proyectadas en la pupila) y
   normales nodales.
4. Eliminar los modos de sólido rígido seleccionados (Tx Ty Tz Rx Ry Rz),
   ajuste por mínimos cuadrados ponderado por área.
5. Error de superficie (--quantity):
     sag    : cambio de sag Δz = (u·n̂)/n_z  (por defecto).  Incluye el efecto
              del movimiento en el plano en superficies curvas, como
              recomiendan Doyle, Genberg, Michels et al. (SPIE 5867, 2005).
     normal : desplazamiento normal u·n̂ (MATLAB original).
   En espejos planos ambos coinciden.
6. Ajuste polinómico WLS (ponderado por área proyectada) sobre la apertura:
     circular     → Zernike, convención Fringe o Noll
     anular       → Zernike anulares de Mahajan (1981)
     hexagonal    → ortonormales hexagonales de Mahajan & Dai (2006)
     rectangular  → ortonormales rectangulares de Mahajan & Dai (2007);
                    el cuadrado es el caso ancho = alto
7. Aporte de cada término al RMS, independiente del número de términos
   (Gram–Schmidt ponderado sobre los nodos), y RMS/PV residual acumulado.
8. Calidad óptica (--wavelength, --incidence, --units): WFE en reflexión
   = 2·cosθ·superficie, Strehl de Maréchal y numérico (PSF por FFT).
9. Magnitudes de forma ISO 10110-5:2015 (potencia A, irregularidad B,
   irregularidad rotacionalmente invariante C, RMSt/RMSi/RMSa, PVr) y
   comprobación opcional frente a una indicación «3/A(B/C) RMSx < D»
   (--iso-spec).
10. Combinación de casos de carga calculados con la misma malla:
    gravedad a distintos ángulos u(θ) = cosθ·A + sinθ·B (+C) (--gravity,
    --elevation, --sweep) o combinación lineal Σ cₖ·uₖ (--combine).


CONVENCIONES DE ZERNIKE (apertura circular)
-------------------------------------------
Fringe (--convention fringe, por defecto).  Índices del script 0-based,
históricos de zernikeISO2nm.m.  Script Zk ↔ Fringe Z(k+1):
  Z0 pistón · Z1 tilt X (cosθ) · Z2 tilt Y (sinθ) · Z3 desenfoque ·
  Z4 astig. 0°/90° (cos2θ) · Z5 astig. ±45° (sin2θ) · Z6/Z7 coma X/Y ·
  Z8 esférica primaria · Z9/Z10 trébol · ...

Noll (--convention noll).  Índices 1-based estándar (Noll 1976):
  Z1 pistón · Z2 tilt X · Z3 tilt Y · Z4 desenfoque · Z5 astig. ±45° ·
  Z6 astig. 0°/90° · Z7/Z8 coma · Z9/Z10 trébol · Z11 esférica · ...

¡Atención!  "Términos 1-5" NO son lo mismo en Fringe (incluye astig. 0°)
que en Noll (incluye astig. 45°).

Normalización (--norm): 'pico' (valor máximo 1 en el borde) o 'rms'
(RMS unidad sobre el disco, normalización de Noll).  Sólo cambia el valor
de los coeficientes; el residuo, su RMS y su PV NO dependen de ella.


POLINOMIOS PARA PUPILAS NO CIRCULARES
-------------------------------------
Ortonormalización de Gram–Schmidt de los Zernike de Noll sobre la pupila
ideal inscrita en el círculo unidad (anillo de obscuración ε = r_in/R;
hexágono regular; rectángulo con semilados a, b, a² + b² = 1).  Se calcula
con cuadratura de Gauss exacta, por lo que no depende de la malla, y
reproduce las expresiones cerradas publicadas (p. ej. A4 = √3(2ρ²−1−ε²)/(1−ε²),
R4 = √5(3ρ²−1)/(2√(1−2a²+2a⁴)), H2 = 2√(6/5)·x).  Índices en orden de Noll
(A1, H1, R1 = pistón; 2, 3 = tilts; 4 = desenfoque...).  Son siempre
ortonormales: el coeficiente es directamente el RMS del término.


Uso
---
python fem_mirror_analysis.py RESULTADOS.TXT [opciones]

Ejemplos
--------
# Apertura circular, ajustar los 5 primeros Fringe (Z0..Z4)
python fem_mirror_analysis.py RESULTADOS.TXT --terms 0 1 2 3 4

# Los 5 primeros términos de Noll (Z1..Z5)
python fem_mirror_analysis.py RESULTADOS.TXT --convention noll --terms 1 2 3 4 5

# Espejo rectangular 120 x 80, 6 términos de Mahajan–Dai
python fem_mirror_analysis.py RESULTADOS.TXT --aperture rectangular \\
    --width 120 --height 80 --nterms 6 --plot

# Espejo anular (hueco detectado automáticamente), 11 términos
python fem_mirror_analysis.py RESULTADOS.TXT --aperture annular --nterms 11

# Strehl a 1 µm con 10° de incidencia y comprobación ISO 10110-5
python fem_mirror_analysis.py RESULTADOS.TXT --nterms 4 --wavelength 1000 \\
    --incidence 10 --iso-spec "3/500 nm (100 nm/50 nm) RMSi < 20 nm"

# Gravedad a 60° de elevación a partir de casos a 0° y 45°, y barrido 0–90°
python fem_mirror_analysis.py --gravity g0.TXT 0 --gravity g45.TXT 45 \\
    --elevation 60 --sweep 0 90 15 --save-combined g60.TXT

# Exportar a Zemax (Grid Sag) y QUADOA (CSV) + Zernike, en mm, el residuo
# tras quitar pistón, tilts y desenfoque
python fem_mirror_analysis.py RESULTADOS.TXT --units m --nterms 4 \\
    --export salida/espejo --export-surface residuo --export-units mm

# Listar términos
python fem_mirror_analysis.py --list-terms --convention noll

Dependencias
------------
numpy, scipy, matplotlib
  pip install numpy scipy matplotlib
"""

__version__ = "1.0.0"

import argparse
import math
import os
import sys

import numpy as np
from scipy.spatial import Delaunay


# ═══════════════════════════════════════════════════════════════════════════════
#  APERTURAS Y BASES DISPONIBLES
# ═══════════════════════════════════════════════════════════════════════════════

# Aperturas disponibles y la base polinómica que usa cada una
APERTURE_BASIS = {
    'circular':    'zernike',        # Zernike Fringe o Noll
    'annular':     'annular',        # Zernike anular (Mahajan 1981)
    'hexagonal':   'hexagonal',      # Mahajan & Dai (2006)
    'rectangular': 'rectangular',    # Mahajan & Dai (2007); incluye el cuadrado
    'elliptical':  'zernike',        # Zernike circular en coordenadas escaladas
}                                    # (ISO/TR 14999-2:2019, 6.8.3)
APERTURES_PENDING = ()

# Magnitud que se toma como error de superficie
QUANTITIES = ('sag', 'normal')

ZERNIKE_CONVENTIONS = ('fringe', 'noll')
FRINGE_MAX_TERMS = 37      # el conjunto Fringe estándar termina en Z37 = (12, 0)


def surface_cmap():
    """
    Escala de color de los mapas de superficie, con el mismo convenio que
    ANSYS: azul = valor mínimo -> cian -> verde -> amarillo -> rojo = máximo.
    'turbo' (matplotlib >= 3.3); si no existe, 'jet'.
    """
    import matplotlib
    try:
        matplotlib.colormaps['turbo']
        return 'turbo'
    except Exception:
        try:
            import matplotlib.cm as _cm
            _cm.get_cmap('turbo')
            return 'turbo'
        except Exception:
            return 'jet'


# ═══════════════════════════════════════════════════════════════════════════════
#  POLINOMIOS DE ZERNIKE
# ═══════════════════════════════════════════════════════════════════════════════

# Nombres por (n, m).  m > 0 → cos(mθ) ; m < 0 → sin(|m|θ)
_ZERNIKE_NM_NAMES = {
    (0, 0):  "Pistón",
    (1, 1):  "Tilt X (cos θ)",
    (1, -1): "Tilt Y (sin θ)",
    (2, 0):  "Desenfoque",
    (2, 2):  "Astigmatismo 0°/90° (cos 2θ)",
    (2, -2): "Astigmatismo ±45° (sin 2θ)",
    (3, 1):  "Coma X",
    (3, -1): "Coma Y",
    (3, 3):  "Trébol X (cos 3θ)",
    (3, -3): "Trébol Y (sin 3θ)",
    (4, 0):  "Esférica primaria",
    (4, 2):  "Astigmatismo secundario 0°/90°",
    (4, -2): "Astigmatismo secundario ±45°",
    (4, 4):  "Tetrafoil (cos 4θ)",
    (4, -4): "Tetrafoil (sin 4θ)",
    (5, 1):  "Coma secundaria X",
    (5, -1): "Coma secundaria Y",
    (5, 3):  "Trébol secundario X",
    (5, -3): "Trébol secundario Y",
    (6, 0):  "Esférica secundaria",
    (8, 0):  "Esférica terciaria",
}


def zernike_name(n, m):
    """Nombre descriptivo del polinomio Z_n^m."""
    return _ZERNIKE_NM_NAMES.get((int(n), int(m)), f"Z(n={n}, m={m:+d})")


def zernike_iso2nm(nterms):
    """
    Órdenes (n, m) de los primeros `nterms` polinomios en la ordenación
    histórica de zernikeISO2nm.m.  Coincide con la ordenación FRINGE
    (0-based, script Zk ↔ Fringe Z(k+1)) para los 36 primeros términos;
    Fringe Z37 = (12, 0) es un caso especial tratado en zernike_index_to_nm.

        Z0 (0,0)  Z1 (1,+1)  Z2 (1,-1)  Z3 (2,0)  Z4 (2,+2)  Z5 (2,-2)
        Z6 (3,+1) Z7 (3,-1)  Z8 (4,0)   Z9 (3,+3) Z10 (3,-3) ...

    Devuelve
    --------
    n_arr, m_arr : ndarray (nterms,), dtype int
    """
    n_arr = np.zeros(nterms, dtype=int)
    m_arr = np.zeros(nterms, dtype=int)
    idx = 0
    for shell in range(0, 2 * nterms + 2, 2):
        for inn in range(shell // 2, shell + 1):
            angular = shell - inn
            n_arr[idx] = inn
            m_arr[idx] = angular
            idx += 1
            if idx == nterms:
                return n_arr, m_arr
            if angular != 0:
                n_arr[idx] = inn
                m_arr[idx] = -angular
                idx += 1
                if idx == nterms:
                    return n_arr, m_arr
    return n_arr, m_arr


def zernike_noll2nm(j):
    """
    Órdenes (n, m) del polinomio de Noll j (1-based, Noll 1976).

    j par → cos(|m|θ) (m > 0) ; j impar → sin(|m|θ) (m < 0).
        Z1 (0,0)  Z2 (1,+1)  Z3 (1,-1)  Z4 (2,0)  Z5 (2,-2)  Z6 (2,+2)
        Z7 (3,-1) Z8 (3,+1)  Z9 (3,-3)  Z10 (3,+3) Z11 (4,0) ...
    """
    if j < 1:
        raise ValueError(f"Índice de Noll inválido: {j} (debe ser ≥ 1)")
    n = 0
    while j > (n + 1) * (n + 2) // 2:
        n += 1
    k = j - n * (n + 1) // 2            # posición dentro de la fila, 1..n+1
    if n % 2 == 0:
        m_abs = 2 * (k // 2)
    else:
        m_abs = 2 * ((k - 1) // 2) + 1
    if m_abs == 0:
        return n, 0
    return n, (m_abs if j % 2 == 0 else -m_abs)


def zernike_index_to_nm(t, convention='fringe'):
    """
    (n, m) del término `t` en la convención indicada.
      fringe : t 0-based (índice histórico del script; Fringe 1-based = t+1)
      noll   : t 1-based (índice de Noll estándar)
    """
    if convention == 'fringe':
        if t < 0 or t >= FRINGE_MAX_TERMS:
            raise ValueError(
                f"Índice Fringe inválido: {t}.  El conjunto Fringe estándar "
                f"tiene {FRINGE_MAX_TERMS} términos (índices 0..{FRINGE_MAX_TERMS - 1}).")
        if t == 36:
            return 12, 0                 # Fringe Z37 = esférica de 6º orden
        n_arr, m_arr = zernike_iso2nm(t + 1)
        return int(n_arr[t]), int(m_arr[t])
    if convention == 'noll':
        return zernike_noll2nm(t)
    raise ValueError(f"Convención de Zernike desconocida: {convention}")


def zernike_radial_coeffs(n, m_abs, norm='pico'):
    """
    Coeficientes del polinomio radial R_n^|m|(r), en orden descendente de
    potencias (compatible con numpy.polyval).

        R_n^m(r) = Σ_{s=0}^{(n-m)/2} (-1)^s (n-s)! /
                   [s! ((n+m)/2-s)! ((n-m)/2-s)!]  r^{n-2s}

    norm : 'pico' → máximo = 1 ;  'rms' → RMS sobre el disco unidad = 1
    """
    if (n + m_abs) % 2 != 0:
        raise ValueError(f"n={n}, |m|={m_abs}: n+|m| debe ser par")
    if m_abs > n:
        raise ValueError(f"n={n}, |m|={m_abs}: |m| debe ser ≤ n")

    coeffs = np.zeros(n + 1)
    for s in range((n - m_abs) // 2 + 1):
        num = math.factorial(n - s)
        den = (math.factorial(s)
               * math.factorial((n + m_abs) // 2 - s)
               * math.factorial((n - m_abs) // 2 - s))
        coeffs[2 * s] = ((-1) ** s) * num / den

    if norm == 'rms':
        factor = math.sqrt(n + 1) if m_abs == 0 else math.sqrt(2 * (n + 1))
        coeffs *= factor
    return coeffs


def eval_zernike_term(n, m, r, theta, norm='pico'):
    """
    Z_n^m(r, θ):   m ≥ 0 → R_n^m(r) cos(mθ) ;  m < 0 → R_n^|m|(r) sin(|m|θ)
    """
    R = np.polyval(zernike_radial_coeffs(n, abs(m), norm), r)
    if m >= 0:
        return R * np.cos(m * theta)
    return R * np.sin(-m * theta)


def build_zernike_matrix(terms, r, theta, norm='pico', convention='fringe'):
    """Matriz de diseño (N_puntos × N_terms) de Zernike."""
    A = np.zeros((len(r), len(terms)))
    for col, t in enumerate(terms):
        n, m = zernike_index_to_nm(t, convention)
        A[:, col] = eval_zernike_term(n, m, r, theta, norm)
    return A


# ═══════════════════════════════════════════════════════════════════════════════
#  POLINOMIOS ORTONORMALES PARA PUPILAS NO CIRCULARES
#  (Mahajan 1981: anular · Mahajan & Dai 2006/2007: hexagonal y rectangular)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Los polinomios de Mahajan y Mahajan & Dai se definen como la
# ortonormalización de Gram–Schmidt de los polinomios de Zernike circulares
# (ordenación y normalización de Noll) sobre la pupila no circular inscrita
# en el círculo unidad, con peso uniforme.  Aquí se calculan numéricamente:
# se integra con cuadratura de Gauss exacta para polinomios sobre la pupila
# IDEAL (no sobre la malla FEM), de modo que la base no depende de la malla.
#
#   P_j(ρ,θ) = Σ_{i≤j} T_ij · Z_i(ρ,θ)        ⟨P_i, P_j⟩_pupila = δ_ij
#
# Cada P_j tiene RMS unidad sobre la pupila y es una combinación de Z_1..Z_j
# (Z_j más correcciones de órdenes inferiores), por lo que conserva el
# significado físico de Z_j (tilt, desenfoque, astigmatismo...).

ORTHO_BASES = ('annular', 'hexagonal', 'rectangular')
ORTHO_PREFIX = {'annular': 'A', 'hexagonal': 'H', 'rectangular': 'R'}
ORTHO_MAX_TERMS = 66          # hasta orden radial n = 10

_ORTHO_CACHE = {}


def _gauss01(n):
    """Nodos y pesos de Gauss–Legendre en [0, 1]."""
    x, w = np.polynomial.legendre.leggauss(n)
    return 0.5 * (x + 1.0), 0.5 * w


def _hexagon_vertices(rotation_deg=0.0):
    """Vértices del hexágono regular inscrito en el círculo unidad.
    rotation_deg = 0 → vértices en ±X ; 30 → vértices en ±Y."""
    a = np.radians(rotation_deg) + np.arange(6) * np.pi / 3.0
    return np.column_stack([np.cos(a), np.sin(a)])


def _pupil_quadrature(shape):
    """
    Cuadratura (x, y, w) sobre la pupila ideal inscrita en el círculo unidad.
    Exacta para polinomios del grado que se usa (≤ 2·10).
    """
    kind = shape['type']
    ng = 48
    if kind == 'annular':
        eps = float(shape['eps'])
        u, wu = _gauss01(ng)
        r = eps + (1.0 - eps) * u
        wr = (1.0 - eps) * wu * r                 # dA = r dr dθ
        nt = 128
        t = np.arange(nt) * 2 * np.pi / nt
        R, Tt = np.meshgrid(r, t, indexing='ij')
        W = np.outer(wr, np.full(nt, 2 * np.pi / nt))
        return (R * np.cos(Tt)).ravel(), (R * np.sin(Tt)).ravel(), W.ravel()
    if kind == 'rectangular':
        a, b = float(shape['a']), float(shape['b'])
        u, wu = _gauss01(ng)
        x, y = (2 * u - 1) * a, (2 * u - 1) * b
        X, Y = np.meshgrid(x, y, indexing='ij')
        W = np.outer(2 * a * wu, 2 * b * wu)
        return X.ravel(), Y.ravel(), W.ravel()
    if kind == 'hexagonal':
        V = _hexagon_vertices(shape.get('rotation', 0.0))
        u, wu = _gauss01(ng)
        U, Vv = np.meshgrid(u, u, indexing='ij')
        WU = np.outer(wu, wu)
        xs, ys, ws = [], [], []
        for k in range(6):
            A, B = V[k], V[(k + 1) % 6]
            # Triángulo (0, A, B) por transformación de Duffy desde [0,1]²
            P = U[..., None] * (A + Vv[..., None] * (B - A))
            jac = abs(A[0] * B[1] - A[1] * B[0]) * U
            xs.append(P[..., 0].ravel()); ys.append(P[..., 1].ravel())
            ws.append((WU * jac).ravel())
        return np.concatenate(xs), np.concatenate(ys), np.concatenate(ws)
    raise ValueError(f"Pupila desconocida: {kind}")


def _shape_key(shape):
    kind = shape['type']
    if kind == 'annular':
        return (kind, round(float(shape['eps']), 6))
    if kind == 'rectangular':
        return (kind, round(float(shape['a']), 6))
    return (kind, round(float(shape.get('rotation', 0.0)), 6))


def ortho_transform(shape, nterms):
    """
    Matriz T (nterms × nterms, triangular superior) tal que
    P = Z_noll_rms @ T es ortonormal sobre la pupila ideal (Gram–Schmidt
    en orden de Noll, con diagonal positiva).
    """
    key = (_shape_key(shape), int(nterms))
    if key in _ORTHO_CACHE:
        return _ORTHO_CACHE[key]
    if shape['type'] == 'annular' and float(shape['eps']) <= 0.0:
        T = np.eye(nterms)                       # sin obscuración = Zernike
    else:
        x, y, w = _pupil_quadrature(shape)
        w = w / w.sum()
        Z = build_zernike_matrix(list(range(1, nterms + 1)), np.hypot(x, y),
                                 np.arctan2(y, x), 'rms', convention='noll')
        Q, R = np.linalg.qr(Z * np.sqrt(w)[:, None])
        s = np.sign(np.diag(R)); s[s == 0] = 1.0
        R = R * s[:, None]                       # diagonal positiva (G–S)
        if np.min(np.abs(np.diag(R))) < 1e-10:
            raise ValueError("Base mal condicionada para esta pupila.")
        T = np.linalg.solve(R, np.eye(nterms))   # R⁻¹ (triangular superior)
    _ORTHO_CACHE[key] = T
    return T


def build_ortho_matrix(shape, terms, r, theta):
    """Matriz de diseño con los polinomios ortonormales de la pupila."""
    J = max(terms)
    T = ortho_transform(shape, J)
    Z = build_zernike_matrix(list(range(1, J + 1)), r, theta, 'rms', convention='noll')
    P = Z @ T
    return P[:, [t - 1 for t in terms]]


# ═══════════════════════════════════════════════════════════════════════════════
#  INTERFAZ COMÚN DE BASES
# ═══════════════════════════════════════════════════════════════════════════════

BASIS_FAMILY_ES = {
    'fringe': 'Zernike Fringe', 'noll': 'Zernike Noll',
    'annular': 'Zernike anular (Mahajan)',
    'hexagonal': 'hexagonales (Mahajan–Dai)',
    'rectangular': 'rectangulares (Mahajan–Dai)',
}


def basis_key(aperture, convention='fringe'):
    """Base a usar: 'fringe' | 'noll' | 'annular' | 'hexagonal' | 'rectangular'."""
    if aperture in ORTHO_BASES:
        return aperture
    if aperture not in ('circular', 'elliptical'):
        raise ValueError(f"Apertura desconocida: {aperture}")
    if convention not in ZERNIKE_CONVENTIONS:
        raise ValueError(f"Convención desconocida: {convention}")
    return convention


def max_terms(basis):
    return FRINGE_MAX_TERMS if basis == 'fringe' else ORTHO_MAX_TERMS


def default_terms(basis, nterms):
    """Los `nterms` primeros términos de la base, en sus índices nativos
    (Fringe 0-based; Noll y bases ortonormales 1-based, orden de Noll)."""
    if basis == 'fringe':
        return list(range(nterms))
    return list(range(1, nterms + 1))


def term_nm(basis, t):
    """(n, m) del Zernike que genera el término t."""
    if basis == 'fringe':
        return zernike_index_to_nm(t, 'fringe')
    return zernike_noll2nm(t)


def term_info(basis, t):
    """
    Información de un término para imprimir.

    Devuelve (etiqueta, índice 1-based de la convención, orden, nombre).
    En las bases ortonormales el nombre es el del Zernike del que procede.
    """
    n, m = term_nm(basis, t)
    if basis == 'fringe':
        return f"Z{t}", t + 1, f"n={n} m={m:+d}", zernike_name(n, m)
    if basis == 'noll':
        return f"Z{t}", t, f"n={n} m={m:+d}", zernike_name(n, m)
    if basis in ORTHO_BASES:
        return f"{ORTHO_PREFIX[basis]}{t}", t, f"n={n} m={m:+d}", zernike_name(n, m)
    raise ValueError(f"Base desconocida: {basis}")


def build_design_matrix(basis, terms, coords, norm='pico'):
    """
    Matriz de diseño para cualquier base.
      coords : dict con 'r' y 'theta' (normalizados al círculo unidad que
               inscribe la pupila) y, para las bases ortonormales, 'shape'.
    Las bases ortonormales tienen siempre normalización RMS (unidad).
    """
    if basis in ZERNIKE_CONVENTIONS:
        return build_zernike_matrix(terms, coords['r'], coords['theta'],
                                    norm, convention=basis)
    if basis in ORTHO_BASES:
        return build_ortho_matrix(coords['shape'], terms, coords['r'], coords['theta'])
    raise ValueError(f"Base desconocida: {basis}")


# ═══════════════════════════════════════════════════════════════════════════════
#  GEOMETRÍA DE SUPERFICIE: SISTEMA LOCAL, ÁREAS NODALES Y NORMALES
# ═══════════════════════════════════════════════════════════════════════════════

def compute_bestfit_normal(coor):
    """
    Normal del plano best-fit de la nube de puntos (SVD / PCA): dirección de
    mínima varianza.  Se orienta con componente Z ≥ 0.

    Devuelve un vector unitario (3,).
    """
    centered = coor - coor.mean(axis=0)
    _, _, Vt = np.linalg.svd(centered, full_matrices=False)
    normal = Vt[-1]
    if normal[2] < 0:
        normal = -normal
    return normal / np.linalg.norm(normal)


def rotation_to_z(normal):
    """
    Matriz de giro R (3×3) que lleva `normal` a +Z con la rotación mínima
    (fórmula de Rodrigues), conservando lo más posible la orientación de X, Y.
    """
    n = np.asarray(normal, dtype=float)
    n = n / np.linalg.norm(n)
    z = np.array([0.0, 0.0, 1.0])
    v = np.cross(n, z)
    s = np.linalg.norm(v)
    c = float(n @ z)
    if s < 1e-12:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    vx = np.array([[0, -v[2], v[1]],
                   [v[2], 0, -v[0]],
                   [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx * ((1 - c) / s ** 2)


def to_local_frame(coor, disp):
    """
    Gira coordenadas y desplazamientos al sistema local de la superficie
    (normal best-fit → +Z).  No traslada el origen, para que los giros de sólido rígido
    se sigan refiriendo al mismo punto que en el sistema global.

    Devuelve
    --------
    coor_l, disp_l : ndarray (N, 3)
    info           : dict con 'normal', 'R' y 'tilt_deg' (ángulo normal–Z)
    """
    normal = compute_bestfit_normal(coor)
    R = rotation_to_z(normal)
    tilt = math.degrees(math.acos(max(-1.0, min(1.0, float(normal[2])))))
    return coor @ R.T, disp @ R.T, {'normal': normal, 'R': R, 'tilt_deg': tilt}


def _local_spacing(xy, k=6):
    """Separación local entre nodos: distancia media a los k vecinos más
    próximos (robusta frente a pares de nodos muy cercanos)."""
    from scipy.spatial import cKDTree
    k = min(k, len(xy) - 1)
    d = cKDTree(xy).query(xy, k=k + 1)[0][:, 1:]
    d = np.where(d > 0, d, np.nan)
    with np.errstate(all='ignore'):
        loc = np.nanmean(d, axis=1)
    loc[~np.isfinite(loc)] = np.inf
    return loc


def _spurious_triangles(xy, simplices, max_edge_factor=4.0, k=16, cone_deg=30.0):
    """
    Máscara (True = falso) de los triángulos que Delaunay crea sobre huecos
    (pupila anular), muescas o entrantes del contorno, que no son malla.

    Criterio direccional: una arista (a, b) de longitud L es falsa si, en
    sus DOS extremos, hay otro nodo a menos de L / max_edge_factor en la
    dirección de la propia arista (cono de ±cone_deg°).  En un hueco, detrás
    de cada extremo hay material mallado con paso fino; en una malla
    anisótropa (mapeada polar, tira estrecha, transición gradual) no hay
    nodos más cercanos en esa dirección y la arista se conserva.  Sólo se
    examinan los k vecinos más próximos: si no aparece ninguno en el cono,
    la arista se conserva (criterio conservador).
    """
    from scipy.spatial import cKDTree
    n = len(xy)
    m = len(simplices)
    if not max_edge_factor or m == 0 or n < 4:
        return np.zeros(m, bool)
    e = np.concatenate([simplices[:, [0, 1]], simplices[:, [1, 2]],
                        simplices[:, [2, 0]]])
    e.sort(axis=1)
    ue, inv = np.unique(e, axis=0, return_inverse=True)
    inv = np.asarray(inv).ravel().reshape(3, m).T
    kk = min(k, n - 1)
    dist, idx = cKDTree(xy).query(xy, k=kk + 1)
    dist, idx = dist[:, 1:], idx[:, 1:]
    d1 = np.where(dist > 0, dist, np.inf).min(axis=1)   # vecino no coincidente
    a, b = ue[:, 0], ue[:, 1]
    vec = xy[b] - xy[a]
    L = np.hypot(vec[:, 0], vec[:, 1])
    f = float(max_edge_factor)
    bad = np.zeros(len(ue), bool)
    cand = np.nonzero((L > 0) & (L > f * d1[a]) & (L > f * d1[b]))[0]
    cosc = math.cos(math.radians(cone_deg))
    for s0 in range(0, len(cand), 20000):
        c = cand[s0:s0 + 20000]
        u = vec[c] / L[c, None]

        def closest_along(v):
            w = xy[idx[v]] - xy[v][:, None, :]
            dw = dist[v]
            with np.errstate(invalid='ignore', divide='ignore'):
                cosang = np.abs(np.einsum('mkj,mj->mk', w, u)) / dw
            ok = (dw > 0) & (cosang >= cosc)
            return np.where(ok, dw, np.inf).min(axis=1)

        s_ab = np.maximum(closest_along(a[c]), closest_along(b[c]))
        bad[c] = L[c] > f * s_ab
    return bad[inv].any(axis=1)


def _mesh_triangles(xy, max_edge_factor=4.0, area_threshold=0.0):
    """
    Triangulación de Delaunay de los nodos (XY) y máscara de triángulos
    válidos: sin área (o por debajo de area_threshold), degenerados
    (área < 1e-10·arista²) o falsos (_spurious_triangles) → no válidos.

    Devuelve (simplices, valid, area2d) con area2d = doble del área en XY.
    """
    xy = np.asarray(xy, float)
    if len(xy) < 3:
        raise ValueError(f"Hacen falta al menos 3 nodos para triangular ({len(xy)}).")
    try:
        simplices = Delaunay(xy).simplices
    except Exception:
        # Puntos alineados o casi coincidentes: se reintenta con «joggle»
        try:
            simplices = Delaunay(xy, qhull_options='QJ').simplices
        except Exception:
            raise ValueError(f"No se puede triangular la superficie ({len(xy)} nodos): "
                             f"los nodos están alineados o coinciden.") from None
    P = xy[simplices]
    v12 = P[:, 1] - P[:, 0]
    v13 = P[:, 2] - P[:, 0]
    area2d = np.abs(v12[:, 0] * v13[:, 1] - v13[:, 0] * v12[:, 1])
    e2 = np.max(np.stack([(v12 ** 2).sum(1), (v13 ** 2).sum(1),
                          ((P[:, 2] - P[:, 1]) ** 2).sum(1)], axis=1), axis=1)
    valid = (area2d > max(area_threshold, 0.0)) & (area2d > 1e-10 * e2)
    if max_edge_factor:
        valid &= ~_spurious_triangles(xy, simplices, max_edge_factor)
    return simplices, valid, area2d


def compute_nodal_areas_and_normals(coor, area_threshold=0.0, max_edge_factor=4.0):
    """
    Triangulación de Delaunay en XY.  Áreas nodales (área proyectada del
    triángulo / 3) y normales unitarias en cada nodo.

    Equivale a la triangulación de extract_rigid.m / lee.m.

    area_threshold : área mínima (en XY, unidades del modelo²) para aceptar
        un triángulo.  ¡Ojo! es absoluta: MATLAB usaba 1 para un espejo de
        1,2 m en mm; en espejos pequeños un umbral de 1 descarta casi toda
        la malla.  Por defecto 0 (sólo se descartan triángulos de área nula).
    max_edge_factor : se descartan los triángulos falsos que Delaunay crea
        sobre huecos (pupila anular), muescas o entrantes del contorno: los
        que tienen una arista más larga que este factor por la separación
        entre nodos medida en la dirección de la propia arista, en sus dos
        extremos (véase _spurious_triangles).  No afecta a mallas mapeadas
        anisótropas ni a mallas graduales.  None/0 → desactivado.

    Devuelve
    --------
    simplices : ndarray (M, 3)   Triángulos válidos
    an        : ndarray (N,)     Áreas nodales normalizadas (suma = 1);
                                 0 en nodos que no pertenecen a ningún
                                 triángulo válido (p. ej. nodos duplicados)
    normals   : ndarray (N, 3)   Normales unitarias (0 en esos nodos)
    """
    npts = len(coor)
    simplices, valid, area2d = _mesh_triangles(coor[:, :2], max_edge_factor,
                                               area_threshold)
    simplices = simplices[valid]
    area2d = area2d[valid]
    if len(simplices) == 0:
        raise ValueError(
            f"No se puede triangular la superficie ({npts} nodos): los nodos están "
            f"alineados, son muy pocos o el umbral de área es demasiado grande.")

    # Normales de triángulo en 3D, orientadas con la normal global
    p0 = coor[simplices[:, 0]]
    p1 = coor[simplices[:, 1]]
    p2 = coor[simplices[:, 2]]
    face_n = np.cross(p1 - p0, p2 - p0)
    global_normal = compute_bestfit_normal(coor)
    sign_n = np.sign(face_n @ global_normal)
    sign_n[sign_n == 0] = 1.0
    face_n *= sign_n[:, np.newaxis]

    an = np.zeros(npts)
    for j in range(3):
        np.add.at(an, simplices[:, j], area2d / 3.0)
    if an.sum() > 0:
        an /= an.sum()

    node_n = np.zeros((npts, 3))
    for j in range(3):
        np.add.at(node_n, simplices[:, j], face_n)
    mag = np.linalg.norm(node_n, axis=1, keepdims=True)
    mag[mag == 0] = 1.0
    node_n /= mag

    return simplices, an, node_n


# ═══════════════════════════════════════════════════════════════════════════════
#  EXTRACCIÓN DEL MOVIMIENTO DE SÓLIDO RÍGIDO
# ═══════════════════════════════════════════════════════════════════════════════

def extract_rigid(coor, disp, rigidmodes=(0, 0, 1, 0, 0, 0),
                  area_threshold=0.0, quantity='normal'):
    """
    Elimina el movimiento de sólido rígido y devuelve el error de superficie
    residual.  Traducción de extract_rigid.m (IAC), ampliada.

    quantity : 'normal' → desplazamiento normal  u·n̂  (como el MATLAB)
               'sag'    → cambio de sag lineal medido a lo largo de Z en la
                          misma posición (x, y):  Δs = u_z − ∇f·u_xy.
                          Con n̂ = (−f_x, −f_y, 1)/√(1+|∇f|²) resulta
                          Δs = (u·n̂) / n_z.  Es lo que recomiendan Doyle,
                          Genberg, Michels et al. (SPIE 5867, 2005) para
                          superficies curvas: incluye el efecto del
                          movimiento en el plano.  En espejos planos
                          (n_z = 1) coincide con la normal.

        rigidmodes = [Tx, Ty, Tz, Rx, Ry, Rz]   0 = conservar, 1 = eliminar

    Ajuste por mínimos cuadrados del campo 3D (dX, dY, dZ) ponderado por
    √(área nodal).  Los giros se toman respecto al ORIGEN de coordenadas.

    Devuelve
    --------
    un  : ndarray (N,)   Error de superficie residual (normal o sag; NaN en
                         nodos sin área, fuera de la triangulación)
    an  : ndarray (N,)   Áreas nodales normalizadas
    pos : ndarray (6,)   Coeficientes [Tx, Ty, Tz, Rx, Ry, Rz]
    """
    _, an, node_norms = compute_nodal_areas_and_normals(coor, area_threshold)

    pos = np.zeros(6)
    disp_corr = disp.astype(float).copy()
    active = [i for i, f in enumerate(rigidmodes) if f != 0]

    if active:
        an_sqrt = np.sqrt(an)
        npts = len(coor)
        A = np.zeros((3 * npts, 6))
        A[0:npts, 0] = an_sqrt                       # Tx → dX
        A[npts:2 * npts, 1] = an_sqrt                # Ty → dY
        A[2 * npts:3 * npts, 2] = an_sqrt            # Tz → dZ
        A[npts:2 * npts, 3] = -coor[:, 2] * an_sqrt  # Rx: dY = -Z·Rx
        A[2 * npts:3 * npts, 3] = coor[:, 1] * an_sqrt   # dZ = +Y·Rx
        A[0:npts, 4] = coor[:, 2] * an_sqrt          # Ry: dX = +Z·Ry
        A[2 * npts:3 * npts, 4] = -coor[:, 0] * an_sqrt  # dZ = -X·Ry
        A[0:npts, 5] = -coor[:, 1] * an_sqrt         # Rz: dX = -Y·Rz
        A[npts:2 * npts, 5] = coor[:, 0] * an_sqrt   # dY = +X·Rz

        A_act = A[:, active]
        b = (disp_corr * an_sqrt[:, np.newaxis]).ravel(order='F')
        coef, *_ = np.linalg.lstsq(A_act, b, rcond=None)
        pos[active] = coef

        # Campo rígido SIN ponderar (válido también en nodos de área nula)
        rigid = np.zeros_like(disp_corr)
        for k, idx in enumerate(active):
            c = coef[k]
            if idx == 0:
                rigid[:, 0] += c
            elif idx == 1:
                rigid[:, 1] += c
            elif idx == 2:
                rigid[:, 2] += c
            elif idx == 3:
                rigid[:, 1] += -coor[:, 2] * c
                rigid[:, 2] += coor[:, 1] * c
            elif idx == 4:
                rigid[:, 0] += coor[:, 2] * c
                rigid[:, 2] += -coor[:, 0] * c
            elif idx == 5:
                rigid[:, 0] += -coor[:, 1] * c
                rigid[:, 1] += coor[:, 0] * c
        disp_corr -= rigid

    un = (disp_corr * node_norms).sum(axis=1)
    if quantity == 'sag':
        nz = node_norms[:, 2]
        with np.errstate(divide='ignore', invalid='ignore'):
            un = np.where(np.abs(nz) > 0.05, un / nz, np.nan)   # >87° → sin sentido
    elif quantity != 'normal':
        raise ValueError(f"Magnitud desconocida: {quantity}")
    un[an <= 0] = np.nan          # nodos fuera de la triangulación
    return un, an, pos


# ═══════════════════════════════════════════════════════════════════════════════
#  APERTURAS
# ═══════════════════════════════════════════════════════════════════════════════

def surface_centroid(xy, an=None):
    """
    Centro geométrico de la superficie mallada.  Con áreas nodales es el
    centroide ponderado por área (independiente de la densidad de malla);
    sin ellas, la media de los nodos.
    """
    if an is not None and np.sum(an) > 0:
        w = an / np.sum(an)
        return float(w @ xy[:, 0]), float(w @ xy[:, 1])
    return float(xy[:, 0].mean()), float(xy[:, 1].mean())


def _center(xy, center):
    if center is None:
        return float(xy[:, 0].mean()), float(xy[:, 1].mean())
    return float(center[0]), float(center[1])


def aperture_circular(xy, radius=None, center=None, tol=0.0):
    """
    Máscara circular.

    center : (xc, yc) o None (media de los nodos)
    radius : radio de normalización; None → distancia máxima al centro
    tol    : tolerancia absoluta en el borde (coordenadas redondeadas en el
             fichero: un nodo del borde puede quedar a 1e-5 fuera del radio)

    Devuelve mask (N,), r_norm (M,), theta (M,)
    """
    cx, cy = _center(xy, center)
    xc, yc = xy[:, 0] - cx, xy[:, 1] - cy
    r = np.hypot(xc, yc)
    if radius is None:
        radius = r.max()
    mask = r <= radius * (1 + 1e-9) + tol
    return mask, np.minimum(r[mask] / radius, 1.0), np.arctan2(yc[mask], xc[mask])


def aperture_annular(xy, radius=None, inner_radius=0.0, center=None, tol=0.0):
    """
    Máscara anular  r_in ≤ r ≤ R.  Coordenadas normalizadas a R.
    Devuelve mask, r_norm, theta.
    """
    cx, cy = _center(xy, center)
    xc, yc = xy[:, 0] - cx, xy[:, 1] - cy
    r = np.hypot(xc, yc)
    if radius is None:
        radius = r.max()
    mask = (r <= radius * (1 + 1e-9) + tol) & (r >= inner_radius * (1 - 1e-9) - tol)
    return mask, np.minimum(r[mask] / radius, 1.0), np.arctan2(yc[mask], xc[mask])


def aperture_rectangular(xy, width=None, height=None, center=None, tol=0.0):
    """
    Máscara rectangular (lados paralelos a X e Y).  Para la base de
    Mahajan–Dai el rectángulo se inscribe en el círculo unidad: las
    coordenadas se normalizan por la semidiagonal.

    Devuelve mask, r_norm, theta, a, b  (a, b = semilados normalizados,
    a² + b² = 1)
    """
    cx, cy = _center(xy, center)
    xc, yc = xy[:, 0] - cx, xy[:, 1] - cy
    if width is None:
        width = 2.0 * np.abs(xc).max()
    if height is None:
        height = 2.0 * np.abs(yc).max()
    hw, hh = width / 2.0, height / 2.0
    mask = ((np.abs(xc) <= hw * (1 + 1e-9) + tol)
            & (np.abs(yc) <= hh * (1 + 1e-9) + tol))
    hd = math.hypot(hw, hh)
    return (mask, np.minimum(np.hypot(xc[mask], yc[mask]) / hd, 1.0),
            np.arctan2(yc[mask], xc[mask]), hw / hd, hh / hd)


def aperture_elliptical(xy, width=None, height=None, center=None, tol=0.0):
    """
    Máscara elíptica con ejes paralelos a X (ancho) e Y (alto), p. ej. un
    espejo plegado.  Según ISO/TR 14999-2:2019, 6.8.3, las coordenadas se
    escalan para que la pupila sea circular y se usan Zernike circulares:
        ρ = √((x/a)² + (y/b)²),  θ = atan2(y/b, x/a)   (a, b = semiejes)
    Devuelve mask, r_norm, theta.
    """
    cx, cy = _center(xy, center)
    xc, yc = xy[:, 0] - cx, xy[:, 1] - cy
    if width is None:
        width = 2.0 * np.abs(xc).max()
    if height is None:
        height = 2.0 * np.abs(yc).max()
    a, b = width / 2.0, height / 2.0
    u, v = xc / a, yc / b
    rho = np.hypot(u, v)
    mask = rho <= 1 + 1e-9 + tol / min(a, b)
    return mask, np.minimum(rho[mask], 1.0), np.arctan2(v[mask], u[mask])


def aperture_hexagonal(xy, circumradius=None, center=None, rotation=0.0, tol=0.0):
    """
    Máscara hexagonal regular inscrita en el círculo de radio `circumradius`.
    rotation = 0 → vértices en ±X ; 30 → vértices en ±Y (lados verticales).
    Devuelve mask, r_norm, theta (normalizados al circunradio).
    """
    cx, cy = _center(xy, center)
    xc, yc = xy[:, 0] - cx, xy[:, 1] - cy
    if circumradius is None:
        circumradius = np.hypot(xc, yc).max()
    # Girar al sistema "vértice en +X" para aplicar el test
    c, s = math.cos(math.radians(-rotation)), math.sin(math.radians(-rotation))
    xr, yr = c * xc - s * yc, s * xc + c * yc
    apothem = circumradius * math.sqrt(3) / 2.0 * (1 + 1e-9) + tol
    c1 = np.abs(yr) <= apothem
    c2 = np.abs(xr * (math.sqrt(3) / 2) + yr * 0.5) <= apothem
    c3 = np.abs(xr * (math.sqrt(3) / 2) - yr * 0.5) <= apothem
    mask = c1 & c2 & c3
    return (mask, np.minimum(np.hypot(xc[mask], yc[mask]) / circumradius, 1.0),
            np.arctan2(yc[mask], xc[mask]))


def apply_aperture(xy, un, an, aperture, radius=None, width=None, height=None,
                   center=None, inner_radius=None, hex_rotation=0.0):
    """
    Selecciona los nodos de la apertura y devuelve sus coordenadas
    normalizadas para la base correspondiente.

    aperture : 'circular' | 'annular' | 'hexagonal' | 'rectangular'
    radius   : radio exterior (circular, anular) o circunradio (hexagonal)
    inner_radius : radio interior del anillo (None → hueco central de la malla)
    hex_rotation : 0 → vértices en ±X ; 30 → vértices en ±Y

    Se excluyen los nodos con NaN (sin área en la triangulación).
    El centro por defecto es el centroide ponderado por área.

    Devuelve
    --------
    mask   : ndarray (N,) bool
    coords : dict  'r', 'theta' (normalizados al círculo que inscribe la
             pupila) y, en pupilas no circulares, 'shape'
    geom   : dict  geometría de la apertura (contornos, área, informe)
    """
    valid = np.isfinite(un) & (an > 0)
    nvalid = int(valid.sum())
    if nvalid < 3:
        raise ValueError("No hay nodos válidos (con área en la triangulación) "
                         "para aplicar la apertura.")
    if center is None:
        center = surface_centroid(xy[valid], an[valid])
    cx, cy = center
    rv = np.hypot(xy[valid, 0] - cx, xy[valid, 1] - cy)
    # Tolerancia de borde: 1 % de la separación entre nodos.  Las coordenadas
    # del fichero vienen redondeadas (p. ej. 5 decimales) y los nodos del
    # contorno pueden quedar ligeramente fuera de la cota nominal.
    tol = 0.01 * float(np.median(_local_spacing(xy[valid])))
    if not np.isfinite(tol):
        tol = 0.0
    for nm, val in (('radio', radius), ('ancho', width), ('alto', height)):
        if val is not None and not (np.isfinite(val) and val > 0):
            raise ValueError(f"El {nm} de la apertura debe ser un número positivo ({val}).")
    if inner_radius is not None and not (np.isfinite(inner_radius) and inner_radius >= 0):
        raise ValueError(f"El radio interior debe ser ≥ 0 ({inner_radius}).")

    if aperture == 'circular':
        if radius is None:
            radius = float(rv.max())
        mask, r, th = aperture_circular(xy, radius, center, tol)
        coords = {'r': r, 'theta': th}
        geom = {'type': 'circular', 'center': center, 'radius': radius}
    elif aperture == 'annular':
        if radius is None:
            radius = float(rv.max())
        if inner_radius is None:
            inner_radius = float(rv.min())
            if inner_radius < 0.01 * radius:     # sin hueco apreciable
                inner_radius = 0.0
        eps = inner_radius / radius
        if not 0.0 <= eps < 0.95:
            raise ValueError(f"Obscuración ε = r_int/R = {eps:.3f} fuera de rango [0, 0.95): "
                             f"el radio interior ({inner_radius:g}) debe ser menor que "
                             f"el 95 % del exterior ({radius:g}).")
        mask, r, th = aperture_annular(xy, radius, inner_radius, center, tol)
        coords = {'r': r, 'theta': th, 'shape': {'type': 'annular', 'eps': eps}}
        geom = {'type': 'annular', 'center': center, 'radius': radius,
                'inner_radius': inner_radius, 'eps': eps}
    elif aperture == 'hexagonal':
        if radius is None:
            radius = float(rv.max())
        mask, r, th = aperture_hexagonal(xy, radius, center, hex_rotation, tol)
        coords = {'r': r, 'theta': th,
                  'shape': {'type': 'hexagonal', 'rotation': float(hex_rotation)}}
        geom = {'type': 'hexagonal', 'center': center, 'radius': radius,
                'rotation': float(hex_rotation)}
    elif aperture == 'rectangular':
        if width is None:
            width = 2.0 * float(np.abs(xy[valid, 0] - cx).max())
        if height is None:
            height = 2.0 * float(np.abs(xy[valid, 1] - cy).max())
        mask, r, th, a, b = aperture_rectangular(xy, width, height, center, tol)
        coords = {'r': r, 'theta': th, 'shape': {'type': 'rectangular', 'a': a, 'b': b}}
        geom = {'type': 'rectangular', 'center': center,
                'width': width, 'height': height}
    elif aperture == 'elliptical':
        auto = width is None and height is None
        if width is None:
            width = 2.0 * float(np.abs(xy[valid, 0] - cx).max())
        if height is None:
            height = 2.0 * float(np.abs(xy[valid, 1] - cy).max())
        if auto:
            # Elipse automática: los semiejes salen de los extremos en X e Y,
            # pero eso no garantiza que contenga a todos los nodos (contorno
            # poligonal): se amplía uniformemente hasta que los contiene.
            rho = np.hypot((xy[valid, 0] - cx) / (width / 2), (xy[valid, 1] - cy) / (height / 2))
            grow = max(1.0, float(rho.max()))
            width, height = width * grow, height * grow
        mask, r, th = aperture_elliptical(xy, width, height, center, tol)
        coords = {'r': r, 'theta': th}
        geom = {'type': 'elliptical', 'center': center,
                'width': width, 'height': height}
    else:
        raise ValueError(f"Apertura desconocida: {aperture}")

    keep = valid[mask]
    mask &= valid
    coords['r'] = coords['r'][keep]
    coords['theta'] = coords['theta'][keep]
    if mask.sum() < 3:
        raise ValueError(f"La apertura sólo contiene {int(mask.sum())} nodo(s) válido(s) "
                         f"(de {nvalid}): revisa el centro y las dimensiones.")
    return mask, coords, geom


def aperture_outline(geom, n=181):
    """Contorno(s) de la apertura en coordenadas del modelo: lista de (x, y)."""
    cx, cy = geom['center']
    t = np.linspace(0, 2 * np.pi, n)
    if geom['type'] in ('circular', 'annular'):
        out = [(cx + geom['radius'] * np.cos(t), cy + geom['radius'] * np.sin(t))]
        if geom['type'] == 'annular' and geom.get('inner_radius', 0) > 0:
            ri = geom['inner_radius']
            out.append((cx + ri * np.cos(t), cy + ri * np.sin(t)))
        return out
    if geom['type'] == 'hexagonal':
        V = _hexagon_vertices(geom.get('rotation', 0.0)) * geom['radius']
        V = np.vstack([V, V[:1]])
        return [(cx + V[:, 0], cy + V[:, 1])]
    if geom['type'] == 'rectangular':
        w, h = geom['width'] / 2, geom['height'] / 2
        return [(cx + np.array([-w, w, w, -w, -w]), cy + np.array([-h, -h, h, h, -h]))]
    if geom['type'] == 'elliptical':
        return [(cx + geom['width'] / 2 * np.cos(t), cy + geom['height'] / 2 * np.sin(t))]
    return []


def describe_geometry(geom):
    """Texto breve con la geometría de la apertura."""
    t = geom['type']
    if t == 'circular':
        return f"Radio de normalización: {geom['radius']:.6g}"
    if t == 'annular':
        return (f"Radio exterior {geom['radius']:.6g} · interior "
                f"{geom['inner_radius']:.6g} · obscuración ε = {geom['eps']:.4f}")
    if t == 'hexagonal':
        return (f"Circunradio {geom['radius']:.6g} · vértices en "
                f"{'±X' if abs(geom.get('rotation', 0)) < 1 else '±Y'}")
    if t == 'elliptical':
        return f"Elipse, ejes X × Y: {geom['width']:.6g} × {geom['height']:.6g}"
    return f"Anchura × altura: {geom['width']:.6g} × {geom['height']:.6g}"


def plot_triangulation(x, y, max_edge_factor=4.0):
    """
    Triangulación para dibujar e interpolar (matplotlib) con la misma malla
    que las áreas nodales: sin triángulos falsos sobre huecos o entrantes ni
    triángulos degenerados (que invalidan el buscador de matplotlib).
    """
    import matplotlib.tri as mtri
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    simplices, valid, _ = _mesh_triangles(np.column_stack([x, y]), max_edge_factor)
    tri = mtri.Triangulation(x, y, triangles=simplices)
    tri.set_mask(~valid)
    return tri


def aperture_area(geom):
    """Área teórica de la apertura."""
    t = geom['type']
    if t == 'circular':
        return math.pi * geom['radius'] ** 2
    if t == 'annular':
        return math.pi * (geom['radius'] ** 2 - geom.get('inner_radius', 0.0) ** 2)
    if t == 'hexagonal':
        return 1.5 * math.sqrt(3) * geom['radius'] ** 2
    if t == 'rectangular':
        return geom['width'] * geom['height']
    if t == 'elliptical':
        return math.pi * geom['width'] * geom['height'] / 4.0
    return None


def mesh_coverage(xy, an, geom):
    """
    Fracción del área teórica de la apertura cubierta por la malla
    (casco convexo de los nodos válidos).  < ~0.8 indica modelo parcial.
    """
    area_ap = aperture_area(geom)
    if not area_ap:
        return None
    from scipy.spatial import ConvexHull
    pts = xy[an > 0]
    if len(pts) < 3:
        return None
    try:
        hull = ConvexHull(pts).volume                # en 2D .volume = área
    except Exception:
        return None
    if geom['type'] == 'annular':                    # el casco cubre el hueco
        hull -= math.pi * geom.get('inner_radius', 0.0) ** 2
    return hull / area_ap


# ═══════════════════════════════════════════════════════════════════════════════
#  AJUSTE POLINÓMICO SOBRE DATOS DISPERSOS
# ═══════════════════════════════════════════════════════════════════════════════

def fit_weighted_ls(u, A, weights=None):
    """
    Mínimos cuadrados (ponderados si `weights` no es None):
        minimizar  Σ wᵢ (Aᵢ·c − uᵢ)²
    Devuelve coeffs, residual.
    """
    if weights is not None:
        w = np.sqrt(np.asarray(weights, dtype=float))
        coeffs, *_ = np.linalg.lstsq(A * w[:, np.newaxis], u * w, rcond=None)
    else:
        coeffs, *_ = np.linalg.lstsq(A, u, rcond=None)
    return coeffs, u - A @ coeffs


def fit_surface(u, coords, basis, terms, norm='pico', weights=None):
    """
    Ajuste de la base `basis` ('fringe' | 'noll' | 'annular' | 'hexagonal' |
    'rectangular').  Por defecto debe pasarse weights = áreas nodales (WLS).

    Devuelve coeffs, residual, A
    """
    if len(u) < len(terms):
        raise ValueError(f"La apertura sólo contiene {len(u)} nodos y se piden "
                         f"{len(terms)} términos: reduce el número de términos o "
                         f"revisa la apertura.")
    A = build_design_matrix(basis, terms, coords, norm)
    coeffs, residual = fit_weighted_ls(u, A, weights)
    return coeffs, residual, A


def term_contributions(u, A, weights):
    """
    Aporte de cada término, independiente del número de términos ajustados.

    En una malla FEM los polinomios no son exactamente ortogonales (Genberg,
    Michels & Doyle, SPIE 4771, 2002): el coeficiente de un término cambia
    según qué otros términos se ajusten.  Aquí se ortonormalizan las columnas
    de A sobre los propios nodos (Gram–Schmidt ponderado por área, en el
    orden de `terms`) y se proyectan los datos:

        b_k  = ⟨u, Φ_k⟩_w      con  ⟨Φ_i, Φ_j⟩_w = δ_ij
        RMS² residual tras k términos = RMS²(u) − Σ_{i≤k} b_i²

    Devuelve
    --------
    contrib   : |b_k|, aporte de cada término al RMS (unidades de u)
    rms_after : RMS residual tras quitar los términos 1..k
    pv_after  : PV residual tras quitar los términos 1..k
    """
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    sw = np.sqrt(w)
    Q, R = np.linalg.qr(A * sw[:, None])
    s = np.sign(np.diag(R)); s[s == 0] = 1.0
    Q = Q * s
    b = Q.T @ (u * sw)
    with np.errstate(divide='ignore', invalid='ignore'):
        Phi = np.where(sw[:, None] > 0, Q / sw[:, None], 0.0)
    res = u[:, None] - np.cumsum(Phi * b, axis=1)
    rms_after = np.sqrt(np.sum(w[:, None] * res ** 2, axis=0))
    pv_after = res.max(axis=0) - res.min(axis=0)
    return np.abs(b), rms_after, pv_after


def zernike_fit_scatter(un, r_norm, theta, terms, norm='pico', weights=None,
                        convention='fringe'):
    """
    Ajuste de Zernike (compatibilidad con versiones anteriores).
    weights = áreas nodales → WLS ;  None → LS ordinario.
    """
    return fit_surface(un, {'r': r_norm, 'theta': theta}, convention,
                       terms, norm, weights)


# ═══════════════════════════════════════════════════════════════════════════════
#  ESTADÍSTICAS
# ═══════════════════════════════════════════════════════════════════════════════

def rms_area_weighted(values, an):
    """
    RMS ponderado por área:  sqrt( Σ aᵢ uᵢ² / Σ aᵢ ).  Ignora NaN.
    (No resta la media; ver std_area_weighted.)
    """
    v = np.asarray(values, dtype=float)
    a = np.asarray(an, dtype=float)
    ok = np.isfinite(v) & (a > 0)
    if not ok.any():
        return float('nan')
    return math.sqrt(float(np.sum(a[ok] * v[ok] ** 2) / np.sum(a[ok])))


def std_area_weighted(values, an):
    """RMS respecto a la media ponderada por área (desviación típica)."""
    v = np.asarray(values, dtype=float)
    a = np.asarray(an, dtype=float)
    ok = np.isfinite(v) & (a > 0)
    if not ok.any():
        return float('nan')
    mean = np.sum(a[ok] * v[ok]) / np.sum(a[ok])
    return math.sqrt(float(np.sum(a[ok] * (v[ok] - mean) ** 2) / np.sum(a[ok])))


def peak_to_valley(values):
    """Pico a valle (ignora NaN)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    return float(v.max() - v.min()) if v.size else float('nan')


# ═══════════════════════════════════════════════════════════════════════════════
#  CALIDAD ÓPTICA: FRENTE DE ONDA, STREHL Y PSF
# ═══════════════════════════════════════════════════════════════════════════════
#
# Error de frente de onda en reflexión: un desplazamiento de la superficie
# a lo largo de su normal añade un camino óptico 2·d·cosθ (θ = ángulo de
# incidencia respecto a la normal).  Con el cambio de sag a lo largo del eje
# (incidencia normal) WFE = 2·Δz.
#
# Strehl por la aproximación de Maréchal:  S ≈ exp(−(2π σ_W / λ)²), fiable
# para S ≳ 0.3 (σ_W ≲ λ/6); el criterio de "limitado por difracción" es
# S ≥ 0.8 (σ_W ≲ λ/14).  Se compara con el Strehl numérico de la PSF
# calculada por FFT de la pupila.

UNIT_TO_NM = {'m': 1e9, 'mm': 1e6, 'µm': 1e3, 'um': 1e3, 'nm': 1.0}


def unit_factor_nm(units):
    """Factor de las unidades del fichero a nm (KeyError si no se conoce)."""
    return UNIT_TO_NM[str(units).strip()]


def wfe_factor(incidence_deg=0.0):
    """Factor superficie → frente de onda en reflexión: 2·cos θ."""
    return 2.0 * math.cos(math.radians(float(incidence_deg)))


def marechal_strehl(rms_wfe_nm, wavelength_nm):
    """Strehl de Maréchal  exp(−(2π σ/λ)²)."""
    return math.exp(-(2.0 * math.pi * rms_wfe_nm / wavelength_nm) ** 2)


def aperture_mask_points(xy, geom):
    """Máscara de puntos arbitrarios dentro de la apertura `geom`."""
    c = geom['center']
    t = geom['type']
    if t == 'circular':
        return aperture_circular(xy, geom['radius'], c)[0]
    if t == 'annular':
        return aperture_annular(xy, geom['radius'], geom.get('inner_radius', 0.0), c)[0]
    if t == 'hexagonal':
        return aperture_hexagonal(xy, geom['radius'], c, geom.get('rotation', 0.0))[0]
    if t == 'rectangular':
        return aperture_rectangular(xy, geom['width'], geom['height'], c)[0]
    if t == 'elliptical':
        return aperture_elliptical(xy, geom['width'], geom['height'], c)[0]
    raise ValueError(f"Apertura desconocida: {t}")


def psf_from_surface(x, y, surf, geom, wavelength_nm, units='mm', incidence_deg=0.0,
                     n_pupil=128, pad=8, crop=8):
    """
    PSF de la pupila con la fase producida por el error de superficie `surf`
    (valores nodales en x, y; NaN fuera).  La superficie se interpola en una
    malla regular sobre la apertura; fuera de la malla FEM la amplitud es 0.

    Devuelve dict:
      psf     : imagen (2·crop·pad)² normalizada al pico de la PSF perfecta
      strehl  : Strehl numérico = pico PSF / pico PSF perfecta
      extent  : [−crop, crop, −crop, crop] en unidades de λ/D
      D       : tamaño de la pupila usado (unidades del fichero)
      fill    : fracción de la pupila con datos
    """
    from matplotlib.tri import LinearTriInterpolator
    ok = np.isfinite(surf)
    tri = plot_triangulation(x[ok], y[ok])
    interp = LinearTriInterpolator(tri, surf[ok])

    xs, ys = [], []
    for ox, oy in aperture_outline(geom):
        xs.append(ox); ys.append(oy)
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    cx, cy = 0.5 * (xs.min() + xs.max()), 0.5 * (ys.min() + ys.max())
    L = max(xs.max() - xs.min(), ys.max() - ys.min())
    g = (np.arange(n_pupil) + 0.5) / n_pupil - 0.5
    GX, GY = np.meshgrid(cx + g * L, cy + g * L)
    pts = np.column_stack([GX.ravel(), GY.ravel()])
    inside = aperture_mask_points(pts, geom).reshape(GX.shape)
    W = np.ma.filled(interp(GX, GY), np.nan)
    A = (inside & np.isfinite(W)).astype(float)
    fill = A.sum() / max(inside.sum(), 1)
    W = np.where(A > 0, W, 0.0)
    W = W - (W * A).sum() / max(A.sum(), 1)                  # quitar pistón
    phase = 2 * np.pi * wfe_factor(incidence_deg) * W * unit_factor_nm(units) / wavelength_nm

    N = n_pupil * pad
    field = np.zeros((N, N), complex)
    perfect = np.zeros((N, N), complex)
    field[:n_pupil, :n_pupil] = A * np.exp(1j * phase)
    perfect[:n_pupil, :n_pupil] = A
    P = np.abs(np.fft.fftshift(np.fft.fft2(field))) ** 2
    P0 = np.abs(np.fft.fftshift(np.fft.fft2(perfect))) ** 2
    strehl = float(P.max() / P0.max())
    c = N // 2
    h = int(crop * pad)
    img = P[c - h:c + h, c - h:c + h] / P0.max()
    return {'psf': img, 'strehl': strehl, 'extent': [-crop, crop, -crop, crop],
            'D': L, 'fill': fill}


def optical_quality(surf_rms, wavelength_nm, units='mm', incidence_deg=0.0):
    """σ de superficie → σ_W (nm y ondas) y Strehl de Maréchal."""
    k = wfe_factor(incidence_deg) * unit_factor_nm(units)
    w_nm = surf_rms * k
    return {'wfe_rms_nm': w_nm, 'wfe_rms_waves': w_nm / wavelength_nm,
            'strehl': marechal_strehl(w_nm, wavelength_nm)}


# ═══════════════════════════════════════════════════════════════════════════════
#  PROCESO COMPLETO (SÓLIDO RÍGIDO + APERTURA + AJUSTE)
# ═══════════════════════════════════════════════════════════════════════════════

def run_pipeline(coor, disp, rigid=(1, 1, 1, 1, 1, 1), quantity='sag',
                 aperture='circular', aperture_kw=None, basis='fringe', terms=None,
                 norm='pico', wls=True, area_threshold=0.0):
    """
    Cadena completa sobre un campo de desplazamientos.  Todas las etapas son
    lineales en `disp`, de modo que el resultado de una combinación de casos
    es la combinación de los resultados.

    Devuelve dict con un, an, mask, coords, geom, residual, coeffs.
    """
    un, an, pos = extract_rigid(coor, disp, rigid, area_threshold, quantity=quantity)
    mask, coords, geom = apply_aperture(coor[:, :2], un, an, aperture, **(aperture_kw or {}))
    out = {'un': un, 'an': an, 'pos': pos, 'mask': mask, 'coords': coords, 'geom': geom,
           'residual': None, 'coeffs': None}
    if terms:
        w = an[mask] / an[mask].sum()
        out['coeffs'], out['residual'], _ = fit_surface(
            un[mask], coords, basis, terms, norm, w if wls else None)
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  COMBINACIÓN DE CASOS DE CARGA
# ═══════════════════════════════════════════════════════════════════════════════
#
# Por linealidad elástica, la respuesta a la gravedad con un ángulo θ en un
# plano (p. ej. la elevación del telescopio) es
#
#     u(θ) = cos θ · A + sin θ · B  (+ C)
#
# donde A y B son las respuestas a 1 g en dos direcciones perpendiciales del
# plano y C un término constante opcional (precargas, montaje, térmico) que
# no cambia con θ.  A, B (y C) se obtienen por mínimos cuadrados a partir de
# 2 casos (3 con C) calculados a ángulos distintos; con más casos que
# incógnitas se comprueba la linealidad.  El convenio de ángulos es libre
# siempre que sea el mismo para todos los casos y la gravedad gire en un
# plano.

def load_case_aligned(fname, case=None, ref_coor=None, tol_rel=1e-6):
    """
    Lee un caso y, si se da `ref_coor`, reordena sus nodos para que coincidan
    con los de referencia.  Error si las mallas no coinciden.
    """
    _, coor, disp = load_fem_data(fname, case)
    if ref_coor is None:
        return coor, disp
    if len(coor) != len(ref_coor):
        raise ValueError(
            f"{fname}: {len(coor)} nodos frente a {len(ref_coor)} del primer caso.  "
            "Los casos deben calcularse con la misma malla.")
    from scipy.spatial import cKDTree
    span = float(np.ptp(ref_coor, axis=0).max()) or 1.0
    tol = tol_rel * span
    if float(np.max(np.abs(coor - ref_coor))) <= tol:
        return ref_coor, disp                       # mismo orden de nodos
    tree = cKDTree(coor)
    d, idx = tree.query(ref_coor)
    mismatch = ValueError(
        f"{fname}: las coordenadas de los nodos no coinciden con las del primer "
        f"caso (desviación máx. {d.max():.3g}).  Los casos deben calcularse con "
        "la misma malla.")
    if d.max() > tol:
        raise mismatch
    uniq, counts = np.unique(idx, return_counts=True)
    if len(uniq) != len(idx):
        # Nodos con coordenadas repetidas (p. ej. costuras sin fusionar): se
        # emparejan en el orden en que aparecen en cada fichero.
        idx = idx.copy()
        conflict = np.isin(idx, uniq[counts > 1])
        used = np.zeros(len(coor), bool)
        used[idx[~conflict]] = True
        for i in np.nonzero(conflict)[0]:
            free = [j for j in sorted(tree.query_ball_point(ref_coor[i], tol)) if not used[j]]
            if not free:
                raise mismatch
            idx[i] = free[0]
            used[free[0]] = True
    return ref_coor, disp[idx]


def fit_gravity_basis(disps, angles_deg, constant=False):
    """
    Respuestas unitarias A, B (y C) a partir de casos a distintos ángulos.

    Devuelve dict con 'A', 'B', 'C' (o None), 'misfit' (desajuste relativo de
    cada caso, sólo informativo si hay más casos que incógnitas) y 'dof'.
    """
    th = np.radians(np.asarray(angles_deg, dtype=float))
    cols = [np.cos(th), np.sin(th)] + ([np.ones_like(th)] if constant else [])
    M = np.column_stack(cols)                       # (ncasos, nincógnitas)
    n_unk = M.shape[1]
    if len(th) < n_unk:
        raise ValueError(f"Hacen falta al menos {n_unk} casos "
                         f"({'con' if constant else 'sin'} término constante).")
    if np.linalg.matrix_rank(M) < n_unk:
        raise ValueError("Los ángulos no permiten separar las respuestas "
                         "(¿ángulos repetidos o separados 180°?).")
    D = np.stack([np.asarray(d, float).ravel() for d in disps])      # (ncasos, 3N)
    X, *_ = np.linalg.lstsq(M, D, rcond=None)
    pred = M @ X
    shape = np.asarray(disps[0]).shape
    misfit = [float(np.linalg.norm(pred[k] - D[k]) / (np.linalg.norm(D[k]) or 1.0))
              for k in range(len(th))]
    return {'A': X[0].reshape(shape), 'B': X[1].reshape(shape),
            'C': X[2].reshape(shape) if constant else None,
            'misfit': misfit, 'dof': len(th) - n_unk}


def gravity_combination(gbasis, angle_deg, ref_angle_deg=None):
    """Desplazamiento a un ángulo; con referencia, el cambio respecto a ella."""
    t = math.radians(float(angle_deg))
    u = math.cos(t) * gbasis['A'] + math.sin(t) * gbasis['B']
    if gbasis.get('C') is not None:
        u = u + gbasis['C']
    if ref_angle_deg is not None:
        r = math.radians(float(ref_angle_deg))
        u = u - (math.cos(r) * gbasis['A'] + math.sin(r) * gbasis['B']
                 + (gbasis['C'] if gbasis.get('C') is not None else 0.0))
    return u


def linear_combination(disps, coeffs):
    """Σ c_k · u_k."""
    return sum(float(c) * np.asarray(d, float) for c, d in zip(coeffs, disps))


def save_fem_txt(fname, coor, disp, header=None, units=None):
    """
    Escribe un fichero X Y Z dX dY dZ.  Las coordenadas van en notación
    exponencial (no pierden resolución si el fichero está en metros).
    units : si se da, se añade «# unidades: …», que se lee al cargarlo.
    """
    with open(fname, 'w', encoding='utf-8') as fh:
        if header:
            for line in str(header).splitlines():
                fh.write(f"# {line}\n")
        if units:
            fh.write(f"# unidades: {units}\n")
        for (x, y, z), (dx, dy, dz) in zip(coor, disp):
            fh.write(f"{x:18.10E}{y:18.10E}{z:18.10E}{dx:18.10E}{dy:18.10E}{dz:18.10E}\n")


def elevation_sweep(coor, gbasis, angles_deg, ref_angle_deg=None, **pipeline_kw):
    """
    RMS y PV (superficie sin sólido rígido y residuo del ajuste) frente al
    ángulo.  Usa la linealidad: se procesan A, B y C una sola vez.
    """
    parts = {'A': gbasis['A'], 'B': gbasis['B']}
    if gbasis.get('C') is not None:
        parts['C'] = gbasis['C']
    res = {k: run_pipeline(coor, v, **pipeline_kw) for k, v in parts.items()}
    an = res['A']['an']
    mask = res['A']['mask']
    w_ap = an[mask] / an[mask].sum()
    has_fit = res['A']['residual'] is not None

    def combo(field, t):
        c, s = math.cos(math.radians(t)), math.sin(math.radians(t))
        v = c * res['A'][field] + s * res['B'][field]
        if 'C' in res:
            v = v + res['C'][field]
        return v

    rows = []
    for t in angles_deg:
        un = combo('un', t)
        rv = combo('residual', t) if has_fit else None
        if ref_angle_deg is not None:
            un = un - combo('un', ref_angle_deg)
            if has_fit:
                rv = rv - combo('residual', ref_angle_deg)
        rows.append({'angle': float(t),
                     'rms': rms_area_weighted(un, an), 'pv': peak_to_valley(un),
                     'rms_res': rms_area_weighted(rv, w_ap) if has_fit else None,
                     'pv_res': peak_to_valley(rv) if has_fit else None})
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
#  TOLERANCIAS DE FORMA ISO 10110-5:2015
# ═══════════════════════════════════════════════════════════════════════════════
#
# Descomposición de la desviación de forma (Tabla B.2 de la norma, funciones
# definidas en ISO 14999-4):
#
#   f_WD  = medida − tilt                    → PV(Q), RMSt
#   f_WS  = parte de esfera best-fit de f_WD → A  (PV de la potencia)
#   f_WI  = f_WD − f_WS (irregularidad)      → B  (PV), RMSi
#   f_WRI = parte rotacionalmente invariante de f_WI → C (PV)
#   f_WRV = f_WI − f_WRI (asimétrica)        → RMSa
#   PVr   = PV robusto de f_WD (sólo apertura circular)
#
# Definiciones de ISO 14999-4:2007 (3.1–3.3):
#   · rms(f) = [∫∫ f² dA / ∫∫ dA]^½ sobre la apertura (sin restar la media);
#   · f_TLT  = plano que mejor aproxima (rms) la medida → incluye el pistón;
#   · f_WS   = función de forma esférica que mejor aproxima f_WD;
#   · f_WRI  = función asférica rotacionalmente invariante que mejor
#              aproxima f_WI.
# Implementación:
#   · f_TLT y la esfera por WLS ponderado por área nodal (≈ la integral);
#   · la esfera se aproxima por el término ρ² (más pistón y tilt), es decir
#     paraxialmente; el error relativo en A es del orden de s²/4, con
#     s = semiapertura / radio nominal (se avisa si supera el 1 %);
#   · la mejor función rotacionalmente invariante en sentido rms es la media
#     azimutal; se aproxima por polinomios pares en ρ (Legendre en 2ρ²−1
#     hasta ρ^(2·n_radial)).  Los RMS son estables; el PV (C) depende algo
#     de la resolución radial, como cualquier PV;
#   · PVr según Evans (Opt. Eng. 48(4), 2009), PV del ajuste de Zernike +
#     3·RMS del residuo, con los 37 términos Fringe (Z1–Z36 y Z(12,0)) que
#     recomienda ISO 14999-4 según Schake & Ehret (Metrologia 63, 055007,
#     2026), y los casos límite de Murphy (Proc. SPIE 12778, 2023):
#     PVr ≥ 6·RMS del residuo y PVr ≤ PV;
#   · PV% (PV recortado) según Murphy (2023): PV del 99,8 % de la
#     superficie, eligiendo cuánto se recorta de cada cola para que el PV
#     sea mínimo.  Murphy recorta por número de puntos (píxeles iguales);
#     aquí, con nodos de área distinta, se recorta por área nodal.  Se da
#     para f_WD y f_WI: la revisión de ISO 10110-5 en preparación prevé
#     admitir PV99.8% o PVr en lugar del PV máx−mín salvo indicación;  ISO 10110-5:2015 lo limita a aperturas circulares; en las
#     demás se calcula (Zernike sobre el círculo que circunscribe la
#     apertura, como en Schake & Ehret) pero se marca como fuera de norma;
#   · pendientes (informativas): gradiente de f_WI en los triángulos de la
#     malla FEM, con el muestreo de la malla, no con la longitud de
#     muestreo G/H de la norma.
# Todas las magnitudes son de superficie (no de frente de onda).  Una
# «fringe spacing» equivale a λ/2 de superficie.  ISO 10110-5 define la
# desviación de forma normal a la superficie (3.1) y la desviación de
# sagita ΔZ a lo largo de z (3.2); en espejos planos coinciden.



def _wfit(A, u, w):
    sw = np.sqrt(w)
    c, *_ = np.linalg.lstsq(A * sw[:, None], u * sw, rcond=None)
    return c, A @ c


def _wrms(v, w):
    return math.sqrt(float(np.sum(w * v ** 2)))


def pv_clipped(values, weights=None, keep=0.998):
    """
    PV recortado PV% (Murphy, Proc. SPIE 12778, 2023): PV de la fracción
    `keep` de la superficie, quitando de las dos colas la combinación que
    da el PV mínimo.  Con `weights` (áreas nodales) la fracción es de área.
    """
    v = np.asarray(values, float)
    w = np.ones_like(v) if weights is None else np.asarray(weights, float)
    ok = np.isfinite(v) & (w > 0)
    v, w = v[ok], w[ok]
    if v.size < 2:
        return float('nan')
    order = np.argsort(v)
    v, w = v[order], w[order] / w.sum()
    q = 1.0 - float(keep)
    cw = np.concatenate([[0.0], np.cumsum(w)])          # cw[k] = área de los k primeros
    best = float(v[-1] - v[0])
    k = 0
    while k < v.size and cw[k] <= q + 1e-12:
        budget = q - cw[k]
        j = int(np.searchsorted(cw, 1.0 - budget - 1e-12, side='left'))
        hi = min(j, v.size) - 1
        if hi > k:
            best = min(best, float(v[hi] - v[k]))
        k += 1
    return best


def _nominal_curvatures(xy, z, w, center, angle_deg=0.0):
    """
    Curvaturas nominales de la superficie a partir de las coordenadas de los
    nodos: ajuste z ≈ c0 + c1·X + c2·Y + kx·X² + ky·Y² + kxy·X·Y en ejes
    girados `angle_deg`.  Devuelve (Rx, Ry, R, n_sph): radios paraxiales en
    X, Y, radio de la esfera best-fit (inf si es plana) y, si la esfera se
    ha ajustado, la normal de la esfera en cada nodo (N×3) para la función
    de potencia exacta.
    """
    X, Y = _iso_axes(xy, center, angle_deg)
    z = np.asarray(z, float)
    A = np.column_stack([np.ones_like(X), X, Y, X ** 2, Y ** 2, X * Y])
    c, _ = _wfit(A, z, w)
    inv = lambda k: (1.0 / (2.0 * k)) if abs(k) > 1e-300 else math.inf
    Rm = inv(0.5 * (c[3] + c[4]))
    # Radio medio: esfera best-fit (ajuste algebraico x²+y²+z² = 2ax+2by+2cz+d),
    # exacto también para superficies rápidas
    semi = float(np.max(np.hypot(X, Y))) or 1.0
    n_sph = None
    if math.isfinite(Rm) and semi / abs(Rm) > 1e-3:
        try:
            zc = z - float(w @ z)
            M = np.column_stack([2 * X, 2 * Y, 2 * zc, np.ones_like(X)])
            q, _ = _wfit(M, X ** 2 + Y ** 2 + zc ** 2, w)
            R2 = q[3] + q[0] ** 2 + q[1] ** 2 + q[2] ** 2
            if R2 > 0:
                Rm = math.copysign(math.sqrt(R2), Rm)
                P = np.column_stack([X, Y, zc]) - q[:3]
                n_sph = P / np.linalg.norm(P, axis=1)[:, None]
        except np.linalg.LinAlgError:
            pass
    return inv(c[3]), inv(c[4]), Rm, n_sph


def _iso_axes(xy, center, angle_deg=0.0):
    """Coordenadas físicas respecto al centro, en ejes girados `angle_deg`."""
    X = np.asarray(xy[:, 0], float) - center[0]
    Y = np.asarray(xy[:, 1], float) - center[1]
    if angle_deg:
        c, s = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
        X, Y = c * X + s * Y, -s * X + c * Y
    return X, Y


def _power_function(r, R):
    """
    Desviación normal que produce un cambio del radio de curvatura nominal R
    (vértice fijo): ∝ 1 − √(1 − r²/R²) (ISO/TR 14999-2:2019, 6.8.1).  Para
    superficies lentas o planas tiende a r²/(2R) ∝ r², la aproximación
    paraxial.  Devuelve la función escalada para que coincida con r² en el
    límite paraxial.
    """
    r = np.asarray(r, float)
    if not math.isfinite(R) or np.max(np.abs(r)) / abs(R) < 1e-3:
        return r ** 2
    q = np.clip((r / R) ** 2, 0.0, 1.0)
    return 2.0 * R ** 2 * (1.0 - np.sqrt(1.0 - q))


ISO_KEYS = ('A', 'AX', 'AY', 'B', 'C', 'CX', 'CY', 'RMSt', 'RMSi', 'RMSa', 'PV', 'PVr')
SLOPE_UNITS = {'mrad': 1.0, 'µrad': 1e-3, 'urad': 1e-3, 'rad': 1e3,
               '°': math.pi / 180 * 1e3, 'deg': math.pi / 180 * 1e3,
               "'": math.pi / 180 / 60 * 1e3, "''": math.pi / 180 / 3600 * 1e3,
               '"': math.pi / 180 / 3600 * 1e3, 'arcmin': math.pi / 180 / 60 * 1e3,
               'arcsec': math.pi / 180 / 3600 * 1e3}


def iso10110_analysis(u, weights, coords, units='mm', xy=None, n_radial=12,
                      circular=True, z=None, form='rot', center=None, axis_angle_deg=0.0,
                      slope_specs=None, geom=None):
    """
    Magnitudes ISO 10110-5 / ISO 14999-4:2015 de la desviación de forma `u`
    (unidades del fichero; debe ser la desviación NORMAL a la superficie,
    ISO 14999-4, 3.2.1) sobre los nodos de la apertura.

    form = 'rot' : superficies de revolución (esféricas, asféricas, planas):
                   f_WD, f_WS, f_WI, f_WRI, f_WRV → A, B, C, RMSt, RMSi, RMSa
    form = 'cyl' : cilíndricas y tóricas (ISO 14999-4:2015, 3.2.3–3.2.13):
                   f_TLT + f_TWST, f_WC,x, f_WC,y, f_WI,CY, f_WTI,x, f_WTI,y,
                   f_WTV → AX, AY, B, CX, CY, RMSt, RMSi, RMSa.  Los ejes del
                   cilindro/toro son X e Y girados `axis_angle_deg`.
    La potencia usa la función exacta 1 − √(1 − r²/R²) con el radio nominal
    R estimado de las coordenadas `z` (ISO/TR 14999-2:2019, 6.8.1).
    slope_specs : lista de especificaciones de pendiente (parse_iso10110)
                  que se evalúan según ISO 14999-4:2015, cap. 6.
    Valores en nm; pendientes en mrad.
    """
    k = unit_factor_nm(units)
    u = np.asarray(u, float) * k
    w = np.asarray(weights, float)
    w = w / w.sum()
    r, th = np.asarray(coords['r'], float), np.asarray(coords['theta'], float)
    one = np.ones_like(r)
    if xy is None:                                    # sin XY: coordenadas normalizadas
        xy = np.column_stack([r * np.cos(th), r * np.sin(th)])
        z = None
    xy = np.asarray(xy, float)
    if center is None:
        center = (float(w @ xy[:, 0]), float(w @ xy[:, 1]))
    X, Y = _iso_axes(xy, center, axis_angle_deg if form == 'cyl' else 0.0)
    rho = np.hypot(X, Y)
    Rx = Ry = Rm = math.inf
    n_sph = None
    if z is not None and len(z) >= 6:
        Rx, Ry, Rm, n_sph = _nominal_curvatures(xy, z, w, center,
                                                axis_angle_deg if form == 'cyl' else 0.0)
    semi = float(rho.max()) or 1.0

    out = {'form': form, 'n_radial': int(n_radial), 'A': None, 'AX': None, 'AY': None,
           'C': None, 'CX': None, 'CY': None, 'RMS_RI': None, 'RMS_TIX': None,
           'RMS_TIY': None, 'power_coef': None, 'R_nom': None, 'Rx_nom': None,
           'Ry_nom': None, 'axis_angle': float(axis_angle_deg) if form == 'cyl' else 0.0}
    fields = {}
    if form == 'cyl':
        _, tlt = _wfit(np.column_stack([one, X, Y, X * Y]), u, w)     # f_TLT + f_TWST
        WD = u - tlt
        bx, by = _power_function(X, Rx), _power_function(Y, Ry)
        c, fit_c = _wfit(np.column_stack([one, bx, by]), WD, w)
        WCx, WCy = c[1] * bx, c[2] * by
        WI = WD - fit_c
        xn, yn = X / (np.abs(X).max() or 1.0), Y / (np.abs(Y).max() or 1.0)
        Px = np.polynomial.legendre.legvander(xn, int(n_radial))
        Py = np.polynomial.legendre.legvander(yn, int(n_radial))[:, 1:]
        ct, fit_t = _wfit(np.column_stack([Px, Py]), WI, w)
        npx = Px.shape[1]
        WTIx = Px[:, 1:] @ ct[1:npx]
        WTIy = Py @ ct[npx:]
        WRV = WI - fit_t
        out.update({
            'AX': peak_to_valley(WCx), 'AY': peak_to_valley(WCy),
            'CX': peak_to_valley(WTIx), 'CY': peak_to_valley(WTIy),
            'RMS_TIX': _wrms(WTIx - np.sum(w * WTIx), w),
            'RMS_TIY': _wrms(WTIy - np.sum(w * WTIy), w),
            'Rx_nom': Rx, 'Ry_nom': Ry,
        })
        fields.update({'WD': WD, 'WCx': WCx, 'WCy': WCy, 'WI': WI,
                       'WTIx': WTIx, 'WTIy': WTIy, 'WTV': WRV})
        s_fast = max(semi / abs(Rx) if math.isfinite(Rx) else 0.0,
                     semi / abs(Ry) if math.isfinite(Ry) else 0.0)
    else:
        _, tilt = _wfit(np.column_stack([one, X, Y]), u, w)          # f_TLT
        WD = u - tilt
        if n_sph is not None:
            # Cambio de radio de la esfera nominal: δn ∝ 1 − cos α, con α el ángulo
            # entre la normal de la esfera en el nodo y la del centro de la apertura
            # (válido también para segmentos fuera de eje)
            n0 = np.sum(w[:, None] * n_sph, axis=0)
            n0 /= np.linalg.norm(n0)
            b = 2.0 * Rm ** 2 * (1.0 - np.clip(n_sph @ n0, -1.0, 1.0))
        else:
            b = _power_function(rho, Rm)
        c, fit_s = _wfit(np.column_stack([one, X, Y, b]), WD, w)
        WI = WD - fit_s
        WS = WD - WI
        t = 2 * r ** 2 - 1
        P = np.polynomial.legendre.legvander(t, int(n_radial))
        _, WRI = _wfit(P, WI, w)
        WRV = WI - WRI
        out.update({'A': peak_to_valley(WS), 'power_coef': float(c[3]),
                    'C': peak_to_valley(WRI), 'RMS_RI': _wrms(WRI, w), 'R_nom': Rm})
        fields.update({'WD': WD, 'WS': WS, 'WI': WI, 'WRI': WRI, 'WRV': WRV})
        s_fast = semi / abs(Rm) if math.isfinite(Rm) else 0.0

    out.update({
        'PV': peak_to_valley(WD), 'RMSt': _wrms(WD, w),
        'B': peak_to_valley(WI), 'RMSi': _wrms(WI, w),
        'PV_RV': peak_to_valley(WRV), 'RMSa': _wrms(WRV, w),
        'sphere_s': s_fast if (z is not None) else None,
        'power_exact': bool(z is not None and s_fast >= 1e-3),
    })
    # PVr (Evans 2009; ISO 14999-4:2015, 3.3.19): Z(N≤10) y Z(12,0) = Fringe Z1–Z37
    Z = build_zernike_matrix(list(range(37)), r, th, 'pico', 'fringe')
    cz, fz = _wfit(Z, WD, w)
    out['Z20'] = float(cz[3])                    # Fringe Z(2,0) = 2ρ²−1, pico
    rms_z = _wrms(WD - fz, w)
    pvr = max(peak_to_valley(fz) + 3.0 * rms_z, 6.0 * rms_z)     # Murphy (4)
    out['PVr'] = min(pvr, out['PV'])                             # Murphy (3)
    out['PV%'] = pv_clipped(WD, w)
    out['PV%_I'] = pv_clipped(WI, w)
    out['PVr_in_scope'] = bool(circular) and form == 'rot'

    # Pendiente local informativa sobre la malla FEM (sin G/H de la norma)
    out['slope_rms_urad'] = out['slope_max_urad'] = None
    try:
        tri = plot_triangulation(xy[:, 0], xy[:, 1])
        T = tri.get_masked_triangles()
        p = xy[T]
        f = WI[T] / k
        d1, d2 = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
        det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
        e2 = np.maximum.reduce([(d1 ** 2).sum(1), (d2 ** 2).sum(1),
                                ((p[:, 2] - p[:, 1]) ** 2).sum(1)])
        ok = np.abs(det) > 1e-3 * e2         # sin astillas casi degeneradas
        g1, g2 = f[:, 1] - f[:, 0], f[:, 2] - f[:, 0]
        gx = (g1 * d2[:, 1] - g2 * d1[:, 1])[ok] / det[ok]
        gy = (g2 * d1[:, 0] - g1 * d2[:, 0])[ok] / det[ok]
        sl = np.arctan(np.hypot(gx, gy)) * 1e6                    # µrad
        a = 0.5 * np.abs(det[ok])
        out['slope_rms_urad'] = math.sqrt(float(np.sum(a * sl ** 2) / np.sum(a)))
        out['slope_max_urad'] = float(sl.max())
    except Exception:
        pass

    # Pendientes según ISO 14999-4:2015, cap. 6 (f_det = f_WI o f_WI,CY)
    out['slopes'] = []
    if slope_specs:
        g = geom or {'type': 'circular', 'center': center, 'radius': semi}
        for sp in slope_specs:
            try:
                res = slope_deviation(xy, WI / k, g, units, sp,
                                      axis_angle_deg=out['axis_angle'])
            except Exception as e:
                res = {'max_mrad': None, 'rms_mrad': None, 'n': 0,
                       'notes': [f"pendiente no evaluada: {e}"]}
            out['slopes'].append({**sp, **res})
    out['fields'] = fields
    return out


def slope_deviation(xy, f, geom, units, spec, axis_angle_deg=0.0, max_points=4_000_000):
    """
    Pendiente local según ISO 14999-4:2015, cap. 6, de la función detrended
    `f` (mismas unidades de longitud que `xy`) sobre la apertura `geom`.

    spec : dict con 'v' ('1-dim' | '2-dim' | None), 'w' ('x', 'y', 'ρ', 'φ'
           o None), 'G_mm' (longitud de muestreo / lado del área de muestreo)
           y 'H_mm' (intervalo de muestreo espacial).
    · 2-dim: plano LSQ en cada cuadrado de lado G contenido por completo en
      el área de ensayo, con centros cada H (6.2).
    · 1-dim en X o Y: recta LSQ en cada tramo de longitud G (6.1).
    · 1-dim en ρ o φ: proyección del gradiente del plano local sobre la
      dirección radial o tangencial (aproximación de la medida por líneas).
    · 1-dim sin dirección (todas): máximo sobre las direcciones = módulo del
      gradiente local, igual que 2-dim.
    Los datos FEM se interpolan linealmente a una rejilla de paso H.
    Devuelve max_mrad, rms_mrad, n (nº de posiciones), h_used, notes.
    """
    import matplotlib.tri as mtri
    from scipy.signal import fftconvolve
    to_file = 1.0 / LENGTH_TO_MM[str(units).strip()]           # mm → unidades fichero
    G = float(spec['G_mm']) * to_file
    H = float(spec['H_mm']) * to_file
    notes = []
    cx, cy = geom['center']
    xs, ys = [], []
    for ox, oy in aperture_outline(geom):
        xs.append(ox); ys.append(oy)
    xs, ys = np.concatenate(xs), np.concatenate(ys)
    hx, hy = 0.5 * (xs.max() - xs.min()), 0.5 * (ys.max() - ys.min())
    h = H
    npts = (2 * hx / h + 1) * (2 * hy / h + 1)
    if npts > max_points:
        h = H * math.sqrt(npts / max_points)
        notes.append(f"rejilla limitada a {max_points/1e6:.0f}·10⁶ puntos: paso "
                     f"{h / to_file:.3g} mm en lugar de H")
    nwin = max(2, int(round(G / h)) + 1)
    gx_ = np.arange(-hx, hx + 0.5 * h, h) + 0.5 * (xs.min() + xs.max())
    gy_ = np.arange(-hy, hy + 0.5 * h, h) + 0.5 * (ys.min() + ys.max())
    GX, GY = np.meshgrid(gx_, gy_)
    ok = np.isfinite(f)
    tri = plot_triangulation(xy[ok, 0], xy[ok, 1])
    F = mtri.LinearTriInterpolator(tri, f[ok])(GX, GY)
    valid = ~np.ma.getmaskarray(F)
    F = np.where(valid, np.ma.getdata(F), 0.0)
    inside = aperture_mask_points(np.column_stack([GX.ravel(), GY.ravel()]),
                                  geom).reshape(GX.shape)
    valid &= inside
    F = np.where(valid, F, 0.0)
    d_nn = float(np.median(_local_spacing(xy[ok])))
    if d_nn > 0.5 * G:
        notes.append(f"la malla FEM (separación ≈ {d_nn / to_file:.3g} mm) no es mucho más fina "
                     f"que G = {spec['G_mm']:g} mm: la pendiente interpolada no resuelve escalas "
                     f"menores que la malla")
    off = (np.arange(nwin) - (nwin - 1) / 2.0) * h
    v, wdir = spec.get('v'), spec.get('w')
    directional = wdir in ('x', 'y', 'ρ', 'φ') and v != '2-dim'
    along_x = directional and wdir == 'x' and not axis_angle_deg
    along_y = directional and wdir == 'y' and not axis_angle_deg
    need = (1 if along_x else nwin, 1 if along_y else nwin)        # (filas, columnas)
    if F.shape[0] < need[0] or F.shape[1] < need[1]:
        return {'max_mrad': None, 'rms_mrad': None, 'n': 0, 'h_used_mm': h / to_file,
                'notes': notes + [f"la longitud de muestreo G = {spec['G_mm']:g} mm es mayor "
                                  f"que el área de ensayo"]}
    if directional and wdir in ('x', 'y') and not axis_angle_deg:
        # 1-dim (6.1): recta LSQ en tramos de longitud G a lo largo de X o Y
        kern = off / np.sum(off ** 2)
        kern = kern[None, :] if wdir == 'x' else kern[:, None]
        box = np.ones(kern.shape)
        g1 = fftconvolve(F, kern[::-1, ::-1], mode='valid')
        cnt = fftconvolve(valid.astype(float), box, mode='valid')
        xi = np.arctan(np.abs(g1[cnt > box.size - 0.5]))
    else:
        # 2-dim (6.2): plano LSQ en cuadrados de lado G
        kx = np.tile(off / (nwin * np.sum(off ** 2)), (nwin, 1))
        ky = kx.T.copy()
        gxw = fftconvolve(F, kx[::-1, ::-1], mode='valid')
        gyw = fftconvolve(F, ky[::-1, ::-1], mode='valid')
        cnt = fftconvolve(valid.astype(float), np.ones((nwin, nwin)), mode='valid')
        full = cnt > nwin * nwin - 0.5
        gxw, gyw = gxw[full], gyw[full]
        if directional:
            sl = (nwin - 1) // 2
            CXg = GX[sl:sl + full.shape[0], sl:sl + full.shape[1]][full] - cx
            CYg = GY[sl:sl + full.shape[0], sl:sl + full.shape[1]][full] - cy
            if wdir in ('x', 'y'):
                a = math.radians(axis_angle_deg) + (0.0 if wdir == 'x' else math.pi / 2)
                ex, ey = math.cos(a), math.sin(a)
                notes.append("1-dim en ejes girados: gradiente del plano local proyectado")
            else:
                rr = np.hypot(CXg, CYg)
                rr[rr == 0] = np.inf
                ex, ey = CXg / rr, CYg / rr
                if wdir == 'φ':
                    ex, ey = -ey, ex
                notes.append("1-dim en ρ/φ: gradiente del plano local proyectado")
            xi = np.arctan(np.abs(gxw * ex + gyw * ey))
        else:
            xi = np.arctan(np.hypot(gxw, gyw))
    if xi.size == 0:
        return {'max_mrad': None, 'rms_mrad': None, 'n': 0, 'h_used_mm': h / to_file,
                'notes': notes + ["ninguna ventana de muestreo cabe completa en el área de ensayo"]}
    xi = xi * 1e3                                                   # mrad
    return {'max_mrad': float(xi.max()), 'rms_mrad': float(np.sqrt(np.mean(xi ** 2))),
            'n': int(xi.size), 'h_used_mm': h / to_file, 'notes': notes}


def _iso_num(txt):
    return float(txt.replace(',', '.'))


def _parse_slopes(s, warn):
    """Extrae ΔSv,w(F/G/H) y RMSΔSv,w(K/L/M) de la indicación (ISO 10110-5, 5.2.4.1)."""
    import re
    num = r'(\d+(?:[.,]\d+)?|[.,]\d+)'
    rx = re.compile(r"(RMS)?\s*ΔS\s*(1-dim|2-dim)?\s*,?\s*([XYxyρφ])?\s*\(\s*" + num +
                    r"\s*(mrad|µrad|urad|rad|°|deg|arcmin|arcsec|''|\"|'|’’|’|′′|″|′)?\s*/\s*"
                    + num + r"\s*(?:mm)?\s*/\s*" + num + r"\s*(?:mm)?\s*\)")
    specs = []
    for m in rx.finditer(s):
        unit = (m.group(5) or 'mrad').replace('’', "'").replace('′', "'").replace('″', "''")
        if m.group(5) is None:
            warn.append(f"Pendiente sin unidad en «{m.group(0).strip()}»: se toma mrad "
                        "(unidad preferente de ISO 10110-5).")
        wdir = m.group(3).lower() if m.group(3) and m.group(3) in 'XYxy' else m.group(3)
        specs.append({'kind': 'rms' if m.group(1) else 'max', 'v': m.group(2), 'w': wdir,
                      'lim_mrad': _iso_num(m.group(4)) * SLOPE_UNITS[unit],
                      'G_mm': _iso_num(m.group(6)), 'H_mm': _iso_num(m.group(7)),
                      'text': m.group(0).strip()})
    s = rx.sub('', s)
    if re.search(r'ΔS', s):
        warn.append("Indicación de pendiente no reconocida (formato ΔSv,w(F/G/H)).")
        s = re.sub(r'(RMS)?\s*ΔS[^()]*\([^)]*\)', '', s)
    return specs, s


def parse_iso10110(spec):
    """
    Interpreta una indicación ISO 10110-5:2015:

        3/A(B/C) RMSt < D; RMSi < D; RMSa < D; PV(Q); PVr(R); λ = E
        3/AX;AY(B/CX;CY) …                       (cilíndricas y tóricas)
        ΔSv,w(F/G/H); RMSΔSv,w(K/L/M)            (pendiente, 5.2.4.1)

    A, B, C… pueden ser '-' (sin tolerancia).  Unidades nm, µm o, sin unidad,
    «fringe spacings» (requieren λ; 1 fringe = λ/2 de superficie).  Las
    pendientes van en mrad (por defecto), µrad, °, ' o ''; G y H en mm.
    Devuelve dict {clave: valor en nm}, 'form' ('rot' | 'cyl'), 'slopes',
    'wavelength' y 'warnings'.  ValueError si no se entiende.
    """
    import re
    s = str(spec).strip()
    for a, b in (('μ', 'µ'), ('—', '-'), ('–', '-'), ('−', '-'), ('＜', '<'),
                 ('≤', '<'), ('<=', '<'), ('=<', '<'), ('lambda', 'λ'), ('Lambda', 'λ'),
                 ('∆', 'Δ')):
        s = s.replace(a, b)
    s = re.sub(r'(?<![\d.,])(1|2)\s*-\s*dim\b', r'\1-dim', s, flags=re.I)
    s = re.sub(r'(1|2)-DIM', r'\1-dim', s, flags=re.I)
    if not s.startswith('3/'):
        raise ValueError("La indicación debe empezar por «3/».")
    warn = []
    num = r'(\d+(?:[.,]\d+)?|[.,]\d+)'
    unit = r'\s*(nm|µm|um)?'

    lam = None
    m = re.search(r'λ\s*=\s*' + num + r'\s*(nm|µm|um)?', s)
    if m:
        lam = round(_iso_num(m.group(1)) * (1e3 if m.group(2) in ('µm', 'um') else 1.0), 6)
        if not 100.0 <= lam <= 20000.0:
            warn.append(f"λ = {lam:g} nm parece fuera de rango: revisa las unidades "
                        f"(sin unidad se toma nm).")
        s = s[:m.start()] + s[m.end():]
    if re.search(r'\(\s*all\b', s):
        warn.append("Campo de prueba «(all …)» ignorado: se evalúa la apertura completa.")
        s = re.sub(r'\(\s*all[^)]*\)', '', s)
    if re.search(r'Z\s*\(', s):
        warn.append("Tolerancias de coeficientes de Zernike Z(n,m) no evaluadas.")
        s = re.sub(r'Z\s*\([^)]*\)\s*(\([^)]*\))?', '', s)
    slopes, s = _parse_slopes(s, warn)

    def to_nm(val, u):
        v = _iso_num(val)
        if u in ('µm', 'um'):
            return v * 1e3
        if u == 'nm':
            return v
        if lam is None:
            raise ValueError(f"«{val}» no tiene unidades: se interpreta como fringe "
                             "spacings y entonces hace falta «λ = … nm» en la indicación.")
        return v * lam / 2.0

    tol = {}
    body = s[2:]
    for key, rx in (('PVr', r'PVr\s*\(\s*' + num + unit + r'\s*\)'),
                    ('PV', r'PV\s*\(\s*' + num + unit + r'\s*\)')):
        m = re.search(rx, body, flags=re.I)
        if m:
            tol[key] = to_nm(m.group(1), m.group(2))
            body = body[:m.start()] + body[m.end():]
    for m in re.finditer(r'RMS\s*([tia])\s*<\s*' + num + unit, body, flags=re.I):
        tol['RMS' + m.group(1).lower()] = to_nm(m.group(2), m.group(3))
    body = re.sub(r'RMS\s*[tia]\s*<\s*' + num + unit, '', body, flags=re.I)

    def val(txt, what):
        txt = (txt or '').strip()
        if txt in ('', '-'):
            return None
        mm = re.fullmatch(num + unit, txt)
        if not mm:
            raise ValueError(f"No se entiende «{txt}» ({what}).")
        return to_nm(mm.group(1), mm.group(2))

    if '(' in body:
        i0 = body.index('(')
        i1 = body.find(')', i0)
        if i1 < 0:
            raise ValueError("Falta el paréntesis de cierre en «(B/C)».")
        head, inner, rest = body[:i0], body[i0 + 1:i1], body[i1 + 1:]
    else:
        head, inner, rest = body, None, ''
    head = head.strip(' ;')
    cyl = ';' in head or (inner is not None and ';' in inner)
    if cyl:
        ax, _, ay = head.partition(';')
        tol['AX'], tol['AY'] = val(ax, 'AX'), val(ay, 'AY')
    elif head:
        tol['A'] = val(head, 'A')
    if inner is not None:
        b_txt, _, c_txt = inner.partition('/')
        tol['B'] = val(b_txt, 'B')
        if cyl:
            cx_t, _, cy_t = c_txt.partition(';')
            tol['CX'], tol['CY'] = val(cx_t, 'CX'), val(cy_t, 'CY')
        else:
            tol['C'] = val(c_txt, 'C')
    rest = rest.strip(' ;')
    if rest:
        warn.append(f"Texto no interpretado: «{rest}».")
    tol = {k_: v for k_, v in tol.items() if v is not None}
    if not any(k_ in tol for k_ in ISO_KEYS) and not slopes:
        raise ValueError("No se ha encontrado ninguna tolerancia en la indicación.")
    tol['form'] = 'cyl' if cyl else 'rot'
    tol['slopes'] = slopes
    tol['wavelength'] = lam
    tol['warnings'] = warn
    return tol


def iso10110_check(res, tol):
    """
    Lista de (clave, medido, tolerancia, cumple, unidad) de lo especificado.
    Para B y PV se añade, como referencia, la evaluación con PV99.8%.
    Las pendientes se comprueban en mrad.
    """
    rows = []
    for key in ISO_KEYS:
        if key in tol and res.get(key) is not None:
            rows.append((key, res[key], tol[key], res[key] <= tol[key], 'nm'))
            alt = {'B': 'PV%_I', 'PV': 'PV%'}.get(key)
            if alt and res.get(alt) is not None:
                rows.append((f"{key} (PV99.8%)", res[alt], tol[key], res[alt] <= tol[key], 'nm'))
        elif key in tol:
            rows.append((key, None, tol[key], None, 'nm'))
    for sp in res.get('slopes', []):
        meas = sp.get('max_mrad') if sp['kind'] == 'max' else sp.get('rms_mrad')
        rows.append((sp['text'], meas, sp['lim_mrad'],
                     None if meas is None else meas <= sp['lim_mrad'], 'mrad'))
    return rows


def format_iso10110(res, decimals=1, comma=True):
    """Valores medidos en notación ISO 10110-5 (nm)."""
    def f(v):
        txt = f"{v:.{decimals}f}"
        return txt.replace('.', ',') if comma else txt
    if res.get('form') == 'cyl':
        s = (f"3/{f(res['AX'])} nm;{f(res['AY'])} nm ({f(res['B'])} nm/"
             f"{f(res['CX'])} nm;{f(res['CY'])} nm)")
    else:
        s = f"3/{f(res['A'])} nm ({f(res['B'])} nm/{f(res['C'])} nm)"
    s += (f" RMSt < {f(res['RMSt'])} nm; RMSi < {f(res['RMSi'])} nm; "
          f"RMSa < {f(res['RMSa'])} nm")
    if res.get('PVr') is not None and res.get('PVr_in_scope', True):
        s += f"; PVr({f(res['PVr'])} nm)"
    return s


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRADA/SALIDA
# ═══════════════════════════════════════════════════════════════════════════════

def _read_text(fname):
    """
    Texto del fichero respetando la codificación: UTF-8 (con o sin BOM) o
    UTF-16 con BOM (p. ej. salida redirigida desde PowerShell).  Si no es
    UTF-8 válido se lee como Latin-1.
    """
    with open(fname, 'rb') as fh:
        raw = fh.read()
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        return raw.decode('utf-16')
    try:
        return raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        return raw.decode('latin-1')


def _read_table(fname):
    import io
    text = _read_text(fname)
    try:
        data = np.loadtxt(io.StringIO(text))
    except ValueError:
        first = next((ln.strip() for ln in text.splitlines()
                      if ln.strip() and not ln.lstrip().startswith('#')), '')
        msg = ("El fichero no es una tabla numérica de nodos (X Y Z dX dY dZ).\n"
               f"Primera línea que no se puede leer: «{first[:80]}»")
        if any(k in text[:2000] for k in ('Prescription', 'Zemax', 'OpticStudio', 'LENS DATA')):
            msg += "\n(Parece un informe de Zemax, no un fichero de resultados FEM.)"
        else:
            msg += ("\nSi la cabecera son títulos de columna, coméntala con '#'.  "
                    "Los decimales deben ir con punto.")
        raise ValueError(msg) from None
    if data.size == 0:
        raise ValueError("El fichero no contiene datos numéricos.")
    if data.ndim == 1:
        data = data[np.newaxis, :]
    if data.shape[1] < 6:
        raise ValueError(
            f"El fichero debe tener 6 columnas (X Y Z dX dY dZ) o "
            f"7 columnas (id X Y Z dX dY dZ). Encontradas: {data.shape[1]}")
    return data


def read_header_meta(fname, max_lines=100):
    """
    Metadatos «# clave: valor» de las líneas de comentario iniciales del
    fichero (p. ej. «# unidades: mm» que escribe el botón de ANSYS
    Mechanical).  Claves en minúsculas.
    """
    meta = {}
    try:
        for i, line in enumerate(_read_text(fname).splitlines()):
            s = line.strip()
            if i >= max_lines or (s and not s.startswith('#')):
                break
            body = s.lstrip('#').strip()
            if ':' in body:
                k, v = body.split(':', 1)
                meta.setdefault(k.strip().lower(), v.strip())
    except OSError:
        pass
    return meta


def normalize_units(u):
    """Normaliza una unidad de longitud escrita a mano ('um', 'μm' griega,
    'micron', 'MM'…).  Devuelve la clave de UNIT_TO_NM o None."""
    t = str(u or '').strip().replace('\u03bc', '\u00b5')      # μ griega → µ
    t = {'um': 'µm', 'micron': 'µm', 'microns': 'µm', 'µ': 'µm',
         'micra': 'µm', 'micras': 'µm'}.get(t.lower(), t)
    t = t if t in UNIT_TO_NM else t.lower()
    return t if t in UNIT_TO_NM else None


def header_units(fname):
    """
    Unidades declaradas en la cabecera del fichero («# unidades: mm»), o
    None si no se declaran.  Si se declaran pero no se reconocen (p. ej.
    «desconocida», que escribe el botón de ANSYS cuando no pudo leerlas)
    se lanza ValueError: no se debe suponer mm en silencio.
    """
    meta = read_header_meta(fname)
    raw = meta.get('unidades', meta.get('units', '')).strip()
    if not raw:
        return None
    u = normalize_units(raw)
    if u is None:
        raise ValueError(f"La cabecera del fichero declara unas unidades que no se "
                         f"reconocen («{raw}»).  Indica las unidades a mano "
                         f"(m, mm, µm o nm).")
    return u


def _case_ids(data):
    """
    Si la primera columna tiene valores repetidos no puede ser un número de
    nodo: es un identificador de CASO DE CARGA (ficheros con varios casos
    apilados, como AARESULTADOS2.TXT, que proc.m separa en bloques).
    Devuelve la lista de casos, o None si el fichero tiene un único caso.
    """
    if data.shape[1] < 7:
        return None
    ids = data[:, 0]
    uniq, counts = np.unique(ids, return_counts=True)
    if len(uniq) == len(ids) or len(uniq) == 1:
        return None
    if counts.min() != counts.max():
        # Recuentos distintos: no son bloques de casos (todos los casos tienen
        # los mismos nodos), sino números de nodo con alguna repetición.  Si
        # casi todo son repeticiones, el fichero es ambiguo: mejor avisar.
        if len(uniq) <= 0.5 * len(ids):
            raise ValueError(
                f"La primera columna repite valores con frecuencias distintas "
                f"({len(uniq)} valores en {len(ids)} filas): no parecen ni números "
                f"de nodo ni bloques de casos de carga del mismo tamaño.  Revisa "
                f"el fichero.")
        return None
    return [int(v) if float(v).is_integer() else float(v) for v in uniq]


def list_load_cases(fname):
    """Casos de carga presentes en el fichero (None si sólo hay uno)."""
    return _case_ids(_read_table(fname))


def load_fem_data(fname, case=None):
    """
    Carga el fichero TXT de resultados FEM.
      7+ columnas : id X Y Z dX dY dZ [extras ignoradas]
      6 columnas  : X Y Z dX dY dZ

    Si la primera columna contiene valores repetidos se interpreta como
    número de caso de carga y hay que indicar `case`; si no se indica se
    produce un error (mezclar casos daría resultados sin sentido).

    Devuelve node (N,), coor (N, 3), disp (N, 3)
    """
    data = _read_table(fname)
    cases = _case_ids(data)
    rows = np.arange(len(data))
    if cases is not None:
        if case is None:
            lst = ", ".join(f"{c:g}" for c in cases[:10]) + (" …" if len(cases) > 10 else "")
            raise ValueError(
                f"El fichero contiene {len(cases)} casos de carga apilados "
                f"(primera columna = {lst}).  Indica cuál analizar "
                f"(--case en línea de comandos o 'Caso de carga' en la GUI).")
        sel = data[:, 0] == float(case)
        if not sel.any():
            raise ValueError(f"El caso {case} no existe en el fichero. Casos: {cases}")
        data, rows = data[sel], rows[sel]
        node, coor, disp = np.arange(len(data), dtype=float), data[:, 1:4], data[:, 4:7]
    elif data.shape[1] >= 7:
        node, coor, disp = data[:, 0], data[:, 1:4], data[:, 4:7]
    else:
        node, coor, disp = np.arange(len(data), dtype=float), data[:, 0:3], data[:, 3:6]
    bad = ~(np.isfinite(coor).all(axis=1) & np.isfinite(disp).all(axis=1))
    if bad.any():
        first = ", ".join(str(int(r) + 1) for r in rows[bad][:5])
        raise ValueError(
            f"El fichero tiene {int(bad.sum())} fila(s) de datos con valores no "
            f"numéricos (NaN o infinito); primeras filas de datos afectadas: {first}.  "
            f"Revisa la exportación del FEM.")
    if len(coor) < 3:
        raise ValueError(f"El fichero sólo tiene {len(coor)} nodos: hacen falta al menos 3.")
    return node, coor, disp


def check_duplicates(coor, tol_rel=1e-9):
    """Número de nodos con coordenadas XY repetidas."""
    span = float(np.ptp(coor[:, :2], axis=0).max()) or 1.0
    q = np.round(coor[:, :2] / (span * tol_rel)).astype(np.int64)
    _, counts = np.unique(q, axis=0, return_counts=True)
    return int((counts - 1).clip(min=0).sum())


def print_term_table(basis, nterms=21):
    """Imprime la tabla de términos de la base."""
    titles = {'fringe': "Zernike Fringe (índices del script 0-based)",
              'noll': "Zernike Noll (índices 1-based)",
              'annular': "Zernike anular de Mahajan (orden de Noll, 1-based)",
              'hexagonal': "Hexagonales de Mahajan–Dai (orden de Noll, 1-based)",
              'rectangular': "Rectangulares de Mahajan–Dai (orden de Noll, 1-based)"}
    print(f"\n  {titles[basis]}")
    print(f"  {'Término':>8}  {'Nº 1-based':>10}  {'Orden':>12}  Nombre")
    print(f"  {'-'*8:>8}  {'-'*10:>10}  {'-'*12:>12}  ------")
    for t in default_terms(basis, nterms):
        lab, sc, order, name = term_info(basis, t)
        print(f"  {lab:>8}  {sc:>10d}  {order:>12}  {name}")


def print_rigid_body_results(pos, rigidmodes):
    """Imprime los coeficientes de sólido rígido extraídos."""
    labels = ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']
    activos = [(labels[i], pos[i]) for i in range(6) if rigidmodes[i]]
    if activos:
        print("\n  Coeficientes de sólido rígido eliminados:")
        for name, val in activos:
            print(f"    {name} = {val:+.6g}")


def format_fit_table(basis, terms, coeffs, contrib=None):
    """
    Tabla de coeficientes como lista de líneas de texto.
    contrib : (aporte, rms_after, pv_after) de term_contributions, opcional.
    """
    head = f"  {'Término':>8}  {'#':>3}  {'Orden':>11}  {'Coeficiente':>13}"
    sep = f"  {'-'*8:>8}  {'-'*3:>3}  {'-'*11:>11}  {'-'*13:>13}"
    if contrib is not None:
        head += f"  {'Aporte RMS':>11}  {'RMS resid.':>11}  {'PV resid.':>11}"
        sep += f"  {'-'*11:>11}  {'-'*11:>11}  {'-'*11:>11}"
    lines = [head + "  Nombre", sep + "  ------"]
    for k, (t, c) in enumerate(zip(terms, coeffs)):
        lab, sc, order, name = term_info(basis, t)
        row = f"  {lab:>8}  {sc:>3d}  {order:>11}  {c:>+13.4e}"
        if contrib is not None:
            row += (f"  {contrib[0][k]:>11.4e}  {contrib[1][k]:>11.4e}"
                    f"  {contrib[2][k]:>11.4e}")
        lines.append(row + "  " + name)
    lines.append("  # = índice 1-based de la convención.  Aporte RMS: contribución del término al"
                 " RMS, independiente")
    lines.append("  del número de términos (Gram–Schmidt sobre los nodos).  RMS/PV resid.:"
                 " tras quitar hasta ese término.")
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
#  VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

def plot_results(coor, un, mask, residual, aperture_name, output_file='fem_analysis.png'):
    """Figura con el desplazamiento normal y el residuo del ajuste."""
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri

    x, y = coor[:, 0], coor[:, 1]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    ok = np.isfinite(un)
    triang_full = plot_triangulation(x[ok], y[ok])
    cf1 = axes[0].tricontourf(triang_full, un[ok], levels=64, cmap=surface_cmap())
    plt.colorbar(cf1, ax=axes[0], label='Error de superficie')
    axes[0].set_title('Error de superficie\n(tras quitar sólido rígido)')
    axes[0].set_aspect('equal')
    axes[0].set_xlabel('X')
    axes[0].set_ylabel('Y')

    fitted = residual is not None and np.size(residual) == int(np.sum(mask))
    un_res_full = np.full(len(coor), np.nan)
    un_res_full[mask] = residual if fitted else un[mask]
    valid = np.isfinite(un_res_full)
    if valid.sum() > 3:
        triang_ap = plot_triangulation(x[valid], y[valid])
        cf2 = axes[1].tricontourf(triang_ap, un_res_full[valid], levels=64, cmap=surface_cmap())
        plt.colorbar(cf2, ax=axes[1], label='Residuo' if fitted else 'Error de superficie')
    axes[1].set_title(f'Residuo tras el ajuste\n(apertura {aperture_name})' if fitted
                      else f'Apertura {aperture_name}\n(sin ajuste polinómico)')
    axes[1].set_aspect('equal')
    axes[1].set_xlabel('X')
    axes[1].set_ylabel('Y')

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"\n  Gráfico guardado en: {output_file}")
    if plt.get_backend().lower() != 'agg':
        plt.show()
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════════
#  FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def _split_case(spec):
    """«ruta::caso» → (ruta, caso|None)."""
    if '::' in spec:
        path, case = spec.rsplit('::', 1)
        return path, float(case)
    return spec, None


def _cli_combination(args):
    """Construye coor/disp a partir de --gravity o --combine."""
    items = args.gravity or args.combine
    coor = None
    disps, vals, desc = [], [], []
    for spec, val in items:
        path, case = _split_case(spec)
        c, d = load_case_aligned(path, case, coor)
        if coor is None:
            coor = c
        disps.append(d)
        vals.append(float(val))
    if args.combine:
        disp = linear_combination(disps, vals)
        desc.append("Combinación lineal: " + " + ".join(
            f"{v:g}·[{s}]" for (s, _), v in zip(items, vals)))
        return coor, disp, None, desc
    gb = fit_gravity_basis(disps, vals, constant=args.constant)
    desc.append(f"Gravedad: casos a {', '.join(f'{v:g}°' for v in vals)}"
                f"{' + término constante' if args.constant else ''}")
    if gb['dof'] > 0:
        desc.append("Comprobación de linealidad (desajuste relativo por caso): " +
                    ", ".join(f"{v:g}°: {m*100:.2f}%" for v, m in zip(vals, gb['misfit'])))
    else:
        desc.append("Sin casos redundantes: no se puede comprobar la linealidad.")
    disp = None
    if args.elevation is not None:
        disp = gravity_combination(gb, args.elevation, args.ref_elevation)
        desc.append(f"Ángulo analizado: {args.elevation:g}°" +
                    (f" respecto a {args.ref_elevation:g}°" if args.ref_elevation is not None else ""))
    return coor, disp, gb, desc


def _cli_sweep(args, coor, gbasis, rigid, basis, terms, ap_kw):
    if gbasis is None:
        print("  ⚠  --sweep sólo se aplica con --gravity.")
        return
    a0, a1, da = args.sweep
    if da <= 0:
        raise SystemExit("--sweep: el paso debe ser positivo.")
    angles = list(np.arange(a0, a1 + 0.5 * da, da))
    rows = elevation_sweep(coor, gbasis, angles, args.ref_elevation,
                           rigid=rigid, quantity=args.quantity, aperture=args.aperture,
                           aperture_kw=ap_kw, basis=basis,
                           terms=None if args.no_zernike else terms,
                           norm=args.norm, wls=not args.no_wls,
                           area_threshold=args.area_threshold)
    print(f"\n  ── Barrido de ángulo (sin sólido rígido{'' if args.no_zernike else ' / residuo del ajuste'}) ──")
    print(f"  {'Ángulo':>8} {'RMS':>12} {'PV':>12}" +
          ("" if args.no_zernike else f" {'RMS res.':>12} {'PV res.':>12}"))
    for r in rows:
        line = f"  {r['angle']:8.2f} {r['rms']:12.5g} {r['pv']:12.5g}"
        if r['rms_res'] is not None:
            line += f" {r['rms_res']:12.5g} {r['pv_res']:12.5g}"
        print(line)


def optics_summary(un_ap, w, coords, geom, xy_ap, units='mm', wavelength_nm=632.8,
                   incidence_deg=0.0, residual=None, iso_spec=None, x=None, y=None,
                   psf_on='residual', z_ap=None, iso_u=None, iso_form='rot',
                   axis_angle_deg=0.0):
    """
    Calidad óptica y magnitudes ISO 10110-5 de la superficie en la apertura.

    un_ap, w, coords, xy_ap : valores, pesos (áreas), coordenadas normalizadas y
                              XY de los nodos de la apertura
    residual : residuo del ajuste en esos nodos (o None)
    x, y     : XY de toda la malla (para la PSF); si faltan se usa xy_ap
    psf_on   : 'residual' (si hay ajuste) o 'surface'
    iso_u    : desviación NORMAL a la superficie en los nodos (ISO 14999-4,
               3.2.1); si es None se usa un_ap
    iso_form : 'rot' (revolución) o 'cyl' (cilíndrica/tórica); una indicación
               AX;AY en `iso_spec` fuerza 'cyl'
    axis_angle_deg : giro de los ejes X/Y del cilindro o toro
    Devuelve dict con iso, wfe_surface, wfe_residual, psf, tol, check, lines.
    """
    w = np.asarray(w, float) / np.sum(w)
    tol, check = None, []
    form_note = None
    if iso_spec:
        tol = parse_iso10110(iso_spec)
        if tol['form'] == 'cyl' and iso_form != 'cyl':
            iso_form = 'cyl'
            form_note = "La indicación es cilíndrica/tórica (AX;AY): se usa esa descomposición."
    u_iso = un_ap if iso_u is None else iso_u
    iso = iso10110_analysis(u_iso, w, coords, units, xy=xy_ap,
                            circular=geom['type'] == 'circular', z=z_ap, form=iso_form,
                            center=geom['center'], axis_angle_deg=axis_angle_deg,
                            slope_specs=tol['slopes'] if tol else None, geom=geom)
    if tol is not None:
        check = iso10110_check(iso, tol)
    k = unit_factor_nm(units)
    oq_s = optical_quality(iso['RMSt'] / k, wavelength_nm, units, incidence_deg)
    oq_r = None
    if residual is not None:
        r0 = residual - float(np.sum(w * residual))
        oq_r = optical_quality(rms_area_weighted(r0, w), wavelength_nm, units, incidence_deg)
    use_res = residual is not None and psf_on == 'residual'
    if x is None:
        x, y = xy_ap[:, 0], xy_ap[:, 1]
    field = residual if use_res else un_ap
    psf = None
    try:
        if len(x) == len(field):
            full = np.asarray(field, float)
        else:
            full = np.full(len(x), np.nan)
            full[_ap_index(x, y, xy_ap)] = field
        psf = psf_from_surface(x, y, full, geom, wavelength_nm, units, incidence_deg)
        psf['on'] = 'residual' if use_res else 'surface'
    except Exception as e:                                     # pragma: no cover
        psf = {'error': str(e)}

    L = []
    L.append(f"── Calidad óptica (λ = {wavelength_nm:g} nm, incidencia {incidence_deg:g}°, "
             f"unidades {units}) ──")
    L.append("Frente de onda en reflexión WFE = 2·cosθ·superficie; sin pistón ni tilt.")

    def _ln(name, oq):
        if oq['wfe_rms_waves'] > 0:
            return (f"{name:<26} σ_W = {oq['wfe_rms_nm']:9.3f} nm = λ/{1/oq['wfe_rms_waves']:<7.1f}"
                    f" Strehl Maréchal = {oq['strehl']:.4f}")
        return f"{name:<26} σ_W = 0"
    L.append(_ln("Superficie sin s. rígido", oq_s))
    if oq_r is not None:
        L.append(_ln("Residuo del ajuste", oq_r))
    if psf and 'strehl' in psf:
        L.append(f"Strehl numérico (PSF por FFT, "
                 f"{'residuo' if psf['on'] == 'residual' else 'superficie'}): {psf['strehl']:.4f}"
                 f"   pupila con datos {psf['fill']*100:.1f}%")
    smin = min(oq_s['strehl'], oq_r['strehl'] if oq_r else 1.0)
    if smin < 0.3:
        L.append("⚠ Strehl < 0.3: la aproximación de Maréchal no es fiable; usar el valor FFT.")
    lam_iso = tol['wavelength'] if tol and tol.get('wavelength') else wavelength_nm
    fr = lam_iso / 2.0
    L.append("")
    cyl = iso['form'] == 'cyl'
    L.append(f"── ISO 10110-5 / ISO 14999-4:2015 ({'cilíndrica/tórica' if cyl else 'revolución'}; "
             f"superficie, nm; 1 fringe = λ/2 = {fr:g} nm"
             f"{' con la λ de la indicación' if lam_iso != wavelength_nm else ''}) ──")
    L.append("Desviación normal a la superficie u·n̂ (ISO 14999-4:2015, 3.2.1)." if iso_u is not None
             else "⚠ ISO calculado con la magnitud del análisis; la norma usa la desviación "
                  "normal a la superficie (ISO 14999-4:2015, 3.2.1).")
    if form_note:
        L.append(form_note)
    if cyl:
        rows = [("AX potencia en X  PV(f_WC,x)", iso['AX']), ("AY potencia en Y  PV(f_WC,y)", iso['AY']),
                ("B  irregularidad  PV(f_WI,CY)", iso['B']),
                ("CX irreg. trasl. inv.  PV(f_WTI,x)", iso['CX']),
                ("CY irreg. trasl. inv.  PV(f_WTI,y)", iso['CY']),
                ("PV total  PV(f_WD,CY)", iso['PV']), ("RMSt  rms(f_WD,CY)", iso['RMSt']),
                ("RMSi  rms(f_WI,CY)", iso['RMSi']), ("RMSa  rms(f_WTV)", iso['RMSa'])]
    else:
        rows = [("A  potencia  PV(f_WS)", iso['A']), ("B  irregularidad  PV(f_WI)", iso['B']),
                ("C  irreg. rot. inv.  PV(f_WRI)", iso['C']), ("PV total  PV(f_WD)", iso['PV']),
                ("RMSt  rms(f_WD)", iso['RMSt']), ("RMSi  rms(f_WI)", iso['RMSi']),
                ("RMSa  rms(f_WRV)", iso['RMSa'])]
    if iso['PVr'] is not None:
        rows.append(("PVr  PV robusto" + ("" if iso['PVr_in_scope'] else " *"), iso['PVr']))
    sfx = ',CY' if cyl else ''
    rows += [(f"PV99.8%  PV recortado f_WD{sfx}", iso['PV%']),
             (f"PV99.8%  PV recortado f_WI{sfx}", iso['PV%_I'])]
    for name, v in rows:
        L.append(f"{name:<36} {v:11.3f} nm  {v/fr:9.4f} fr")
    if iso['PVr'] is not None and not iso['PVr_in_scope']:
        L.append("* PVr fuera de ISO 10110-5:2015 (sólo apertura circular y superficies de "
                 "revolución); Zernike sobre el círculo que circunscribe la apertura.")
    if iso.get('power_exact'):
        if cyl:
            rad = ", ".join(f"R{a} ≈ {v:.4g}" for a, v in (('x', iso['Rx_nom']), ('y', iso['Ry_nom']))
                            if math.isfinite(v))
        else:
            rad = f"R ≈ {iso['R_nom']:.4g}"
        L.append(f"Potencia con la función exacta 1 − √(1 − r²/R²) (ISO/TR 14999-2, 6.8.1); "
                 f"radio nominal {rad} {units} (semiapertura/R ≈ {iso['sphere_s']:.3f}).")
    if cyl and iso.get('axis_angle'):
        L.append(f"Ejes del cilindro/toro girados {iso['axis_angle']:g}° respecto a X/Y.")
    if geom['type'] == 'elliptical' and iso.get('Z20') is not None:
        ci = math.cos(math.radians(incidence_deg))
        L.append(f"Apertura elíptica (ISO/TR 14999-2, 6.8.3): Z(2,0) en coordenadas escaladas = "
                 f"{iso['Z20']:.3f} nm → potencia en el sistema 2·Z(2,0)·cos i = "
                 f"{2 * iso['Z20'] * ci:.3f} nm; irregularidad B·cos i = {iso['B'] * ci:.3f} nm.")
    if iso['slope_rms_urad'] is not None:
        L.append(f"Pendiente local de f_WI{',CY' if cyl else ''} sobre la malla FEM (informativa): "
                 f"RMS {iso['slope_rms_urad']:.3f} µrad, máx {iso['slope_max_urad']:.3f} µrad")
    for sp in iso.get('slopes', []):
        if sp.get('n'):
            L.append(f"{sp['text']}: máx {sp['max_mrad']*1e3:.3f} µrad, RMS {sp['rms_mrad']*1e3:.3f} µrad "
                     f"({sp['n']} posiciones; G = {sp['G_mm']:g} mm, H = {sp['H_mm']:g} mm; ISO 14999-4, 6)")
        elif not sp.get('notes'):
            L.append(f"{sp['text']}: no evaluada")
        for nt in sp.get('notes', []):
            L.append(f"  ⚠ {sp['text']}: {nt}" if not sp.get('n') else f"  ⚠ {nt}")
    L.append(f"Notación: {format_iso10110(iso)}")
    if tol is not None:
        L.append(f"Comprobación frente a: {iso_spec}")
        for wmsg in tol['warnings']:
            L.append(f"⚠ {wmsg}")
        for key, meas, lim, ok, un in check:
            if meas is None and un == 'mrad':
                L.append(f"  {key}: no evaluada (véase el aviso de la pendiente)")
                continue
            if meas is None:
                L.append(f"  {key:<5} no evaluado con la descomposición "
                         f"{'cilíndrica' if cyl else 'de revolución'}")
                continue
            if un == 'mrad':
                L.append(f"  {key}: medido {meas*1e3:10.3f} µrad   tolerancia {lim*1e3:10.3f} µrad   "
                         f"{'CUMPLE' if ok else 'NO CUMPLE'}")
            else:
                L.append(f"  {key:<5} medido {meas:10.3f} nm   tolerancia {lim:10.3f} nm   "
                         f"{'CUMPLE' if ok else 'NO CUMPLE'}")
    return {'iso': {k_: v for k_, v in iso.items() if k_ != 'fields'}, 'iso_fields': iso['fields'],
            'wfe_surface': oq_s, 'wfe_residual': oq_r, 'psf': psf,
            'tol': tol, 'check': check, 'lines': L, 'units': units,
            'wavelength': wavelength_nm, 'fringe_nm': fr, 'incidence': incidence_deg,
            'spec': iso_spec}


# ═══════════════════════════════════════════════════════════════════════════════
#  EXPORTACIÓN A ZEMAX OPTICSTUDIO Y QUADOA OPTICAL CAD
# ═══════════════════════════════════════════════════════════════════════════════
#
# Se exporta la deformación de la superficie (en la apertura) en dos formas:
#
#  1. Rejilla de sag regular
#     · Zemax «Grid Sag» (.DAT): cabecera «nx ny delx dely unitflag xdec ydec»
#       y nx·ny líneas «z dz/dx dz/dy d²z/dxdy nodata», empezando en la
#       esquina (−x, +y), de izquierda a derecha y bajando en y.  nodata = 1
#       → OpticStudio usa sólo la sag base en ese punto.  Las derivadas se
#       escriben a 0: OpticStudio las estima entonces por diferencias finitas.
#       unitflag 0 = mm, 1 = cm, 2 = in, 3 = m.  Rejilla mínima 5×5.
#       (Ayuda de OpticStudio citada por Zemax en community.zemax.com y
#       artículo «How to use the Grid Sag surface type» de optics.ansys.com.)
#     · QUADOA: fichero de texto tipo CSV con columnas x, y, z en unidades de
#       longitud, igual que el «Export Pointcloud» de QUADOA (manual v26.10,
#       §3.6.1.3).  El manual no documenta el formato de importación de la
#       forma «Grid» ni del ajuste «Convert or Import Form»: se usa el mismo
#       formato que QUADOA exporta.
#
#  2. Coeficientes de Zernike de sag (unidades de lente)
#     · Fringe Z1..Z37, sin normalizar (A = 1): Zemax «Zernike Fringe Sag»
#       (misma convención que Zygo/MetroPro) y QUADOA «Zernike Fringe»
#       (manual §28.1.2, ec. 28.6).
#     · ANSI Z80.28 / ISO 24157, Z0 = pistón, normalización RMS
#       (∫Z²ρdρdφ = π): QUADOA «Zernike» (manual §28.1.1).
#     · Noll (Z1 = pistón), normalización RMS: Zemax «Zernike Standard Sag».
#       ⚠ Convención no comprobada en la ayuda de OpticStudio (requiere
#       acceso de cliente): verificar con Analyze > Surface > Sag.
#
#  En todos los casos los polinomios se evalúan con x, y normalizadas al
#  radio de normalización y centradas en el centro de la apertura;
#  θ se mide desde +X hacia +Y; m > 0 → cos(mθ), m < 0 → sin(|m|θ).

LENGTH_TO_MM = {'m': 1000.0, 'cm': 10.0, 'mm': 1.0, 'in': 25.4,
                'µm': 1e-3, 'um': 1e-3, 'nm': 1e-6}
ZEMAX_UNITFLAG = {'mm': 0, 'cm': 1, 'in': 2, 'm': 3}
EXPORT_SURFACES = {'sin_rigido': 'superficie sin sólido rígido',
                   'residuo': 'residuo tras el ajuste polinómico'}


def length_factor(from_units, to_units):
    """Factor de conversión entre unidades de longitud."""
    return LENGTH_TO_MM[str(from_units).strip()] / LENGTH_TO_MM[str(to_units).strip()]


def export_norm_radius(geom):
    """Radio del círculo que circunscribe la apertura (normalización Zernike)."""
    if geom['type'] == 'rectangular':
        return math.hypot(geom['width'] / 2.0, geom['height'] / 2.0)
    if geom['type'] == 'elliptical':
        return max(geom['width'], geom['height']) / 2.0
    return float(geom['radius'])


def export_half_extent(geom):
    """Semiejes (hx, hy) del rectángulo que contiene la apertura."""
    t = geom['type']
    if t in ('rectangular', 'elliptical'):
        return geom['width'] / 2.0, geom['height'] / 2.0
    R = float(geom['radius'])
    if t == 'hexagonal':
        rot = math.radians(float(geom.get('rotation', 0.0)))
        ang = rot + np.arange(6) * math.pi / 3.0            # vértices
        return float(np.abs(R * np.cos(ang)).max()), float(np.abs(R * np.sin(ang)).max())
    return R, R


def resample_to_grid(xy, values, geom, n=101, method='linear'):
    """
    Interpola valores nodales (dentro de la apertura) a una rejilla regular
    de n×n puntos (n impar → el centro de la apertura es un nodo) que cubre
    la apertura.  Fuera de la apertura → NaN.  Los puntos de la apertura que
    caen fuera de la triangulación (borde de malla) se extrapolan con un
    plano ajustado a los 8 nodos más próximos si el más cercano está a menos
    de 2 separaciones de malla; si no, NaN.

    method : 'linear' (sin sobreoscilaciones) | 'cubic' (C1, Clough–Tocher)

    Devuelve xg (n,), yg (n,) — yg en orden DECRECIENTE (fila 0 = +y) — y
    Z (n, n) con Z[i, j] en (xg[j], yg[i]).
    """
    import matplotlib.tri as mtri
    from scipy.spatial import cKDTree
    n = int(n)
    if n < 5:
        raise ValueError("La rejilla debe tener al menos 5×5 puntos.")
    if n % 2 == 0:
        n += 1
    ok = np.isfinite(values)
    xy, values = xy[ok], values[ok]
    cx, cy = geom['center']
    hx, hy = export_half_extent(geom)
    xg = cx + np.linspace(-hx, hx, n)
    yg = cy + np.linspace(hy, -hy, n)
    X, Y = np.meshgrid(xg, yg)
    tri = plot_triangulation(xy[:, 0], xy[:, 1])
    if method == 'cubic':
        interp = mtri.CubicTriInterpolator(tri, values, kind='geom')
    elif method == 'linear':
        interp = mtri.LinearTriInterpolator(tri, values)
    else:
        raise ValueError(f"Interpolación desconocida: {method}")
    Zm = interp(X, Y)
    Z = np.where(np.ma.getmaskarray(Zm), np.nan, np.ma.getdata(Zm)).astype(float)
    P = np.column_stack([X.ravel(), Y.ravel()])
    inside = aperture_mask_points(P, geom).reshape(X.shape)
    gap = inside & ~np.isfinite(Z)
    if gap.any():
        sp = _local_spacing(xy)
        d_nn = float(np.median(sp[np.isfinite(sp)]))
        Pg = P[gap.ravel()]
        kk = min(8, len(xy))
        d, k = cKDTree(xy).query(Pg, k=kk)
        fill = np.full(len(Pg), np.nan)
        for i in np.flatnonzero(d[:, 0] <= 2.0 * d_nn):
            q = xy[k[i]] - Pg[i]                 # plano local por los kk nodos
            M = np.column_stack([np.ones(kk), q])
            c, *_ = np.linalg.lstsq(M, values[k[i]], rcond=None)
            fill[i] = c[0]
        Z[gap] = fill
    Z[~inside] = np.nan
    return xg, yg, Z


def write_zemax_grid_sag(fname, xg, yg, Z, center, lens_units='mm'):
    """
    Fichero Grid Sag de Zemax OpticStudio.  xg, yg, Z en unidades de lente;
    yg decreciente (fila 0 = +y), como devuelve resample_to_grid.
    La rejilla se centra en el centro de la apertura y se descentra
    (xdec, ydec) respecto al vértice de la superficie base.
    """
    if lens_units not in ZEMAX_UNITFLAG:
        raise ValueError(f"Unidades no admitidas por Zemax Grid Sag: {lens_units} "
                         f"(admitidas: {', '.join(ZEMAX_UNITFLAG)})")
    ny, nx = Z.shape
    delx = (xg[-1] - xg[0]) / (nx - 1)
    dely = (yg[0] - yg[-1]) / (ny - 1)
    lines = [f"{nx:d} {ny:d} {delx:.10g} {dely:.10g} {ZEMAX_UNITFLAG[lens_units]:d} "
             f"{center[0]:.10g} {center[1]:.10g}"]
    for i in range(ny):                      # fila 0 = +y (arriba)
        for j in range(nx):                  # de −x a +x
            z = Z[i, j]
            if np.isfinite(z):
                lines.append(f"{z:.10e} 0 0 0 0")
            else:
                lines.append("0 0 0 0 1")
    with open(fname, 'w', encoding='ascii', newline='\r\n') as f:
        f.write("\n".join(lines) + "\n")


def write_quadoa_grid_csv(fname, xg, yg, Z, keep_nan=False):
    """
    Nube de puntos x, y, z (CSV, sin cabecera) en el mismo formato que el
    «Export Pointcloud» de QUADOA.  Por defecto se omiten los puntos sin
    dato (equivale a «Remove Nan Values»).
    """
    X, Y = np.meshgrid(xg, yg)
    rows = []
    for x, y, z in zip(X.ravel(), Y.ravel(), Z.ravel()):
        if np.isfinite(z):
            rows.append(f"{x:.10g},{y:.10g},{z:.10e}")
        elif keep_nan:
            rows.append(f"{x:.10g},{y:.10g},nan")
    with open(fname, 'w', encoding='ascii', newline='\n') as f:
        f.write("\n".join(rows) + "\n")


def ansi2nm(j):
    """(n, m) del índice ANSI Z80.28 / ISO 24157 j (0-based)."""
    n = int(math.ceil((-3.0 + math.sqrt(9.0 + 8.0 * j)) / 2.0))
    return n, 2 * j - n * (n + 2)


def nm2ansi(n, m):
    return (n * (n + 2) + m) // 2


def zernike_export_sets(n_max=10):
    """
    Conjuntos de Zernike que se exportan: lista de dicts con
    key, title, programs, index (etiquetas), nm [(n, m)], norm.
    """
    fr = [zernike_index_to_nm(t, 'fringe') for t in range(FRINGE_MAX_TERMS)]
    nj = (n_max + 1) * (n_max + 2) // 2
    noll = [zernike_noll2nm(j) for j in range(1, nj + 1)]
    ansi = [ansi2nm(j) for j in range(nj)]
    return [
        {'key': 'fringe', 'title': 'Zernike Fringe (Z1–Z37, sin normalizar)',
         'programs': 'Zemax «Zernike Fringe Sag» · QUADOA «Zernike Fringe»',
         'index': list(range(1, FRINGE_MAX_TERMS + 1)), 'nm': fr, 'norm': 'pico'},
        {'key': 'standard_noll', 'title': f'Zernike Standard / Noll (Z1–Z{nj}, normalización RMS)',
         'programs': 'Zemax «Zernike Standard Sag»',
         'index': list(range(1, nj + 1)), 'nm': noll, 'norm': 'rms'},
        {'key': 'ansi', 'title': f'Zernike ANSI Z80.28 / ISO 24157 (Z0–Z{nj - 1}, normalización RMS)',
         'programs': 'QUADOA «Zernike» (Sort Order ANSI/ISO)',
         'index': list(range(nj)), 'nm': ansi, 'norm': 'rms'},
    ]


def fit_zernike_export(xy, values, weights, center, r_norm, nm, norm):
    """Ajuste WLS de los Zernike (n, m) dados.  Devuelve coef, residuo."""
    xc, yc = xy[:, 0] - center[0], xy[:, 1] - center[1]
    r = np.hypot(xc, yc) / r_norm
    th = np.arctan2(yc, xc)
    A = np.column_stack([eval_zernike_term(n, m, r, th, norm) for n, m in nm])
    c, fitted = _wfit(A, values, weights)
    return c, values - fitted


def write_zernike_file(fname, zset, coeffs, header_lines, lens_units):
    """Tabla de coeficientes con cabecera de comentarios ('#')."""
    lines = [f"# {ln}" if ln else "#" for ln in header_lines]
    lines += ["#", f"# {zset['title']}", f"# Programas: {zset['programs']}", "#",
              f"# {'Z':>4s}  {'n':>3s}  {'m':>4s}  {'coef [' + lens_units + ']':>20s}  descripción"]
    for idx, (n, m), c in zip(zset['index'], zset['nm'], coeffs):
        lines.append(f"{idx:6d}  {n:3d}  {m:+4d}  {c:20.10e}  {zernike_name(n, m)}")
    with open(fname, 'w', encoding='utf-8', newline='\n') as f:
        f.write("\n".join(lines) + "\n")


def export_optical(xy, values, weights, geom, out_base, units='mm', lens_units='mm',
                   n_grid=101, interp='linear', n_max=10, surface='sin_rigido',
                   quantity='sag', source='', frame='global'):
    """
    Exporta la superficie a Zemax y QUADOA.

    xy, values, weights : nodos de la apertura, valor a exportar (unidades del
                          fichero) y pesos (áreas nodales)
    out_base   : ruta base; se añaden sufijos y extensiones
    units      : unidades del fichero FEM (coordenadas y desplazamientos)
    lens_units : unidades de lente del fichero exportado ('mm', 'cm', 'in', 'm')

    Devuelve dict con 'files' (lista de rutas) y 'lines' (resumen).
    """
    import datetime
    f = length_factor(units, lens_units)
    xy_l = np.asarray(xy, float) * f
    v_l = np.asarray(values, float) * f
    w = np.asarray(weights, float)
    ok = np.isfinite(v_l) & np.isfinite(w)
    xy_l, v_l, w = xy_l[ok], v_l[ok], w[ok] / w[ok].sum()
    g = dict(geom)
    g['center'] = (geom['center'][0] * f, geom['center'][1] * f)
    for k in ('radius', 'inner_radius', 'width', 'height'):
        if k in g and g[k] is not None:
            g[k] = g[k] * f
    center, rn = g['center'], export_norm_radius(g)

    d = os.path.dirname(out_base)
    if d:
        os.makedirs(d, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    head = [f"mirror-surface-deformation · exportación {stamp}",
            f"Origen: {source or '—'}",
            f"Superficie: {EXPORT_SURFACES.get(surface, surface)}; magnitud: "
            f"{'cambio de sag Δz' if quantity == 'sag' else 'desplazamiento normal u·n'}; "
            f"sistema: {frame}",
            f"Apertura {geom['type']}: {describe_geometry(g)} [{lens_units}]",
            f"Unidades de lente: {lens_units}  (fichero FEM en {units})",
            f"Radio de normalización: {rn:.10g} {lens_units}",
            f"Centro de normalización (x0, y0): ({center[0]:.10g}, {center[1]:.10g}) {lens_units}",
            f"Nodos: {len(v_l)};  RMS (pond. por área) = {_wrms(v_l, w):.6e};  "
            f"PV = {peak_to_valley(v_l):.6e} {lens_units}"]
    files, lines = [], []

    # ── Rejilla de sag ──────────────────────────────────────────────────────
    xg, yg, Z = resample_to_grid(xy_l, v_l, g, n_grid, interp)
    fz = out_base + '_zemax_gridsag.dat'
    write_zemax_grid_sag(fz, xg, yg, Z, center, lens_units)
    fq = out_base + '_quadoa_grid.csv'
    write_quadoa_grid_csv(fq, xg, yg, Z)
    files += [fz, fq]
    valid = np.isfinite(Z)
    ny, nx = Z.shape
    lines.append(f"Rejilla {nx}×{ny}, paso {xg[1] - xg[0]:.6g} × {yg[0] - yg[1]:.6g} {lens_units} "
                 f"({interp}); {valid.sum()} puntos con dato, {(~valid).sum()} sin dato.")
    Xg, Yg = np.meshgrid(xg, yg)
    n_hole = int((aperture_mask_points(np.column_stack([Xg.ravel(), Yg.ravel()]), g)
                  .reshape(Z.shape) & ~valid).sum())
    if n_hole:
        lines.append(f"  ⚠ {n_hole} puntos dentro de la apertura sin dato (lejos de la malla): "
                     f"en ellos Zemax usa sólo la sag base.")
    lines.append(f"  Rejilla: RMS = {np.sqrt(np.mean(Z[valid] ** 2)):.6e}, "
                 f"PV = {np.ptp(Z[valid]):.6e} {lens_units}  (sin ponderar)")

    # ── Coeficientes de Zernike ─────────────────────────────────────────────
    summary = []
    for zs in zernike_export_sets(n_max):
        c, res = fit_zernike_export(xy_l, v_l, w, center, rn, zs['nm'], zs['norm'])
        recon = v_l - res
        info = head + [
            f"Ajuste WLS (pesos = áreas nodales) sobre {len(v_l)} nodos:",
            f"  RMS residuo no representado = {_wrms(res, w):.6e} {lens_units}",
            f"  Superficie reconstruida: RMS = {_wrms(recon, w):.6e}, "
            f"PV = {peak_to_valley(recon):.6e} {lens_units}",
            "Polinomios en ρ = r / radio de normalización, θ desde +X hacia +Y;",
            "m > 0 → cos(mθ), m < 0 → sin(|m|θ).  Coeficientes = sag en unidades de lente."]
        fn = out_base + f"_zernike_{zs['key']}.txt"
        write_zernike_file(fn, zs, c, info, lens_units)
        files.append(fn)
        summary.append((zs['key'], len(c), _wrms(res, w)))
        lines.append(f"{zs['title']}: RMS residuo = {_wrms(res, w):.4e} {lens_units}")

    # ── Fichero de información ──────────────────────────────────────────────
    fi = out_base + '_LEEME_exportacion.txt'
    _write_export_readme(fi, head, files, lens_units, center, rn, geom, quantity, n_max)
    files.append(fi)
    if geom['type'] != 'circular':
        lines.append("⚠ Apertura no circular: los Zernike se ajustan sobre el círculo "
                     "circunscrito (fuera de la apertura son una extrapolación).")
    if quantity != 'sag':
        lines.append("⚠ Magnitud «normal u·n»: Grid Sag y los Zernike de sag de Zemax/QUADOA "
                     "se suman a la sagita (eje z); para superficies curvas usa «cambio de sag».")
    return {'files': files, 'lines': lines, 'grid': (xg, yg, Z), 'summary': summary}


def _write_export_readme(fname, head, files, lens_units, center, rn, geom, quantity, n_max):
    base = [os.path.basename(p) for p in files]
    flag = ZEMAX_UNITFLAG.get(lens_units)
    txt = head + [
        "",
        "FICHEROS",
        f"  {base[0]}",
        "    Zemax OpticStudio, superficie «Grid Sag».  Formato: cabecera",
        "    «nx ny delx dely unitflag xdec ydec» y nx·ny líneas",
        "    «z dz/dx dz/dy d2z/dxdy nodata», empezando en la esquina (−x, +y).",
        f"    unitflag = {flag} ({lens_units}).  xdec, ydec = centro de la apertura respecto",
        "    al vértice de la superficie.  Derivadas = 0 → OpticStudio las estima por",
        "    diferencias finitas.  nodata = 1 fuera de la apertura (sólo sag base).",
        "    Uso: Lens Data Editor → superficie tipo Grid Sag → Surface Properties →",
        "    Import → seleccionar el .DAT (copiarlo antes a {Zemax}\\Objects\\Grid Files).",
        "    La sag de la rejilla se SUMA a la sag base (radio, cónica) de la superficie:",
        "    deja en ella la prescripción nominal del espejo.",
        f"  {base[1]}",
        "    QUADOA: nube de puntos x, y, z (CSV, sin cabecera, unidades de lente), mismo",
        "    formato que «Export Pointcloud» de QUADOA, en la rejilla regular anterior.",
        "    Para la forma «Grid» o «Convert or Import Form → fit … to imported data».",
        "    ⚠ El manual de QUADOA v26.10 no documenta el formato de importación: si no lo",
        "    acepta, consulta a soporte de QUADOA o usa los coeficientes de Zernike.",
        f"  {base[2]}",
        "    Zernike Fringe Z1..Z37 sin normalizar (A = 1, convención Zygo/MetroPro).",
        "    Zemax «Zernike Fringe Sag» y QUADOA «Zernike Fringe»: Norm Radius = radio de",
        "    normalización; coeficientes en unidades de lente (no en ondas).",
        "    Nota: la tabla 28.2 del manual de QUADOA pone Z2 = 2x, Z3 = 2y, en contra de",
        "    su propia definición (A = 1 → Z2 = x, Z3 = y); sólo afecta al tilt.",
        f"  {base[3]}",
        f"    Zernike Standard (orden de Noll, normalización RMS) hasta n = {n_max}.",
        "    Zemax «Zernike Standard Sag»: Norm Radius = radio de normalización.",
        "    ⚠ Convención no comprobada en la ayuda de OpticStudio (acceso restringido).",
        "    Verifica: Analyze → Surface → Sag sobre la superficie Zernike (radio y cónica",
        "    a 0) debe dar el mismo RMS/PV que «Superficie reconstruida» en el fichero.",
        f"  {base[4]}",
        f"    Zernike ANSI Z80.28 / ISO 24157 (Z0 = pistón, normalización RMS) hasta n = {n_max}.",
        "    QUADOA «Zernike» con Sort Order ANSI/ISO; Polynomial Order = n máximo.",
        "    ⚠ El manual (§9.2.1) nombra las columnas de coeficientes «Z2…Zn» con ID z1…zn;",
        "    comprueba en el editor si la primera columna es Z0 (pistón) o Z1.",
        "",
        "CONVENIOS COMUNES",
        f"  Centro de normalización (x0, y0) = ({center[0]:.10g}, {center[1]:.10g}) {lens_units}.",
        "  Si no es (0, 0), descentra los Zernike: en Zemax con los parámetros de",
        "  descentramiento del Zernike de la superficie; en QUADOA con la posición de la",
        "  superficie.  θ se mide desde +X hacia +Y en el sistema de coordenadas del",
        "  modelo FEM; comprueba que coincide con el sistema local de la superficie en el",
        "  programa óptico (orientación de X, Y y sentido de +Z).",
        "  Las magnitudes son deformación de SUPERFICIE (sag), no frente de onda.",
    ]
    if geom['type'] != 'circular':
        txt += ["  Apertura no circular: los Zernike se ajustan con el círculo circunscrito como",
                "  radio de normalización; fuera de la apertura real son una extrapolación."]
    if quantity != 'sag':
        txt += ["  ⚠ Se ha exportado el desplazamiento normal u·n: Grid Sag y Zernike de sag se",
                "  suman a la sagita (eje z).  En superficies curvas usa «cambio de sag»."]
    with open(fname, 'w', encoding='utf-8', newline='\n') as f:
        f.write("\n".join(txt) + "\n")


def _cli_export(args, coor, un, an, mask, geom, residual):
    if args.export_surface == 'residuo':
        if residual is None or not residual.size:
            print("\n  ⚠  Exportación: no hay residuo (sin ajuste polinómico); "
                  "se exporta la superficie sin sólido rígido.")
            values, surf = un[mask], 'sin_rigido'
        else:
            values, surf = residual, 'residuo'
    else:
        values, surf = un[mask], 'sin_rigido'
    try:
        out = export_optical(coor[mask, :2], values, an[mask], geom, args.export,
                             units=args.units, lens_units=args.export_units,
                             n_grid=args.export_grid, interp=args.export_interp,
                             n_max=args.export_nmax, surface=surf, quantity=args.quantity,
                             source=os.path.basename(args.fname or 'combinación'),
                             frame=args.frame)
    except (KeyError, ValueError) as e:
        print(f"\n  ⚠  Exportación a Zemax/QUADOA: {e}")
        return
    print(f"\n  ── Exportación a Zemax / QUADOA ({EXPORT_SURFACES[surf]}) ──")
    print("\n".join("  " + ln for ln in out['lines']))
    for p in out['files']:
        print(f"    → {p}")


def _ap_index(x, y, xy_ap):
    from scipy.spatial import cKDTree
    return cKDTree(np.column_stack([x, y])).query(xy_ap)[1]


def _cli_optics(args, coor, un, an, mask, coords, geom, residual, un_normal=None):
    try:
        out = optics_summary(un[mask], an[mask], coords, geom, coor[mask, :2], args.units,
                             args.wavelength, args.incidence, residual, args.iso_spec,
                             x=coor[:, 0], y=coor[:, 1], z_ap=coor[mask, 2],
                             iso_u=(un if un_normal is None else un_normal)[mask],
                             iso_form=args.iso_form, axis_angle_deg=args.iso_axis_angle)
    except (KeyError, ValueError) as e:
        print(f"\n  ⚠  Calidad óptica / ISO 10110-5: {e}")
        return
    print()
    print("\n".join("  " + ln if ln else "" for ln in out['lines']))


def main():
    parser = argparse.ArgumentParser(
        description="Análisis FEM de desplazamientos de superficie de espejo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Uso")[0].strip(),
    )
    parser.add_argument(
        "fname", nargs="?",
        help="Fichero TXT con resultados FEM (node X Y Z dX dY dZ  ó  X Y Z dX dY dZ)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--case", type=float, default=None,
        help="Caso de carga a analizar si el fichero contiene varios casos "
             "apilados (primera columna = nº de caso).")
    parser.add_argument(
        "--rigid", nargs=6, type=int, default=[0, 0, 1, 0, 0, 0],
        metavar=("Tx", "Ty", "Tz", "Rx", "Ry", "Rz"),
        help="Modos de sólido rígido a eliminar (0/1).  Default: 0 0 1 0 0 0")
    parser.add_argument(
        "--area-threshold", type=float, default=0.0,
        help="Área mínima ABSOLUTA (unidades²) de los triángulos de Delaunay. "
             "Default: 0 (sólo se descartan triángulos degenerados).")
    parser.add_argument(
        "--frame", choices=["global", "bestfit"], default="global",
        help="Sistema de referencia: 'global' (Z del fichero = eje óptico, como "
             "el MATLAB original) o 'bestfit' (girar a la normal del plano "
             "best-fit).  No usar "
             "'bestfit' con modelos parciales de espejos curvos ni segmentos "
             "fuera de eje.  Default: global")
    parser.add_argument(
        "--center", nargs=2, type=float, default=None, metavar=("XC", "YC"),
        help="Centro de la apertura.  Default: centroide de área de la malla "
             "(para modelos parciales/simetría hay que darlo, p. ej. 0 0).")
    parser.add_argument(
        "--quantity", choices=QUANTITIES, default="sag",
        help="Error de superficie: 'sag' (cambio de sag Δz, incluye el efecto "
             "del movimiento en el plano; recomendado) o 'normal' (u·n̂, como el "
             "MATLAB original).  En espejos planos coinciden. "
             "Default: sag")
    parser.add_argument(
        "--aperture", choices=list(APERTURE_BASIS), default="circular",
        help="Forma de la apertura y base: circular (Zernike Fringe/Noll), "
             "annular (Zernike anular de Mahajan), hexagonal (Mahajan–Dai), "
             "rectangular (Mahajan–Dai; un cuadrado es un rectángulo con "
             "ancho = alto), elliptical (Zernike circular en coordenadas escaladas, "
             "ISO/TR 14999-2, 6.8.3; espejos plegados).  Default: circular")
    parser.add_argument(
        "--convention", choices=ZERNIKE_CONVENTIONS, default="fringe",
        help="Convención de Zernike para la apertura circular.  Default: fringe")
    parser.add_argument("--radius", type=float, default=None,
                        help="Radio exterior (circular, anular) o circunradio "
                             "(hexagonal).  Default: auto")
    parser.add_argument("--inner-radius", type=float, default=None,
                        help="Radio interior de la apertura anular.  Default: "
                             "hueco central de la malla")
    parser.add_argument("--hex-orientation", choices=["x", "y"], default="x",
                        help="Hexágono con vértices en ±X o en ±Y.  Default: x")
    parser.add_argument("--width", type=float, default=None,
                        help="Anchura X (rectangular) o eje X (elíptica).  Default: auto")
    parser.add_argument("--height", type=float, default=None,
                        help="Altura Y (rectangular) o eje Y (elíptica).  Default: auto")
    parser.add_argument(
        "--terms", nargs="+", type=int, default=None,
        help="Índices de los términos a ajustar en la convención de la base "
             "(Fringe 0-based; Noll y bases anular/hexagonal/rectangular "
             "1-based en orden de Noll).  Default: pistón, tilts y "
             "desenfoque.  Ver --list-terms")
    parser.add_argument(
        "--nterms", type=int, default=None,
        help="Ajustar los N primeros términos de la base (igual que la GUI). "
             "Alternativa a --terms.")
    parser.add_argument("--norm", choices=["pico", "rms"], default="pico",
                        help="Normalización de los Zernike circulares.  Las bases "
                             "anular, hexagonal y rectangular son siempre "
                             "ortonormales (RMS).  Default: pico")
    parser.add_argument(
        "--no-wls", action="store_true",
        help="Ajuste por LS ordinario en vez de WLS ponderado por área "
             "(por defecto WLS).")
    parser.add_argument("--no-zernike", action="store_true",
                        help="Omitir el ajuste polinómico")
    parser.add_argument("--plot", action="store_true",
                        help="Generar y guardar figura de resultados")
    parser.add_argument("--plot-file", default="fem_analysis.png",
                        help="Fichero de imagen.  Default: fem_analysis.png")
    parser.add_argument("--list-terms", action="store_true",
                        help="Mostrar la tabla de términos de la base y salir")
    g = parser.add_argument_group("Calidad óptica e ISO 10110-5")
    g.add_argument("--units", choices=["mm", "m", "µm", "um", "nm"], default=None,
                   help="Unidades de longitud del fichero.  Default: las de la cabecera "
                        "«# unidades: …» del fichero (botón de ANSYS Mechanical) o mm")
    g.add_argument("--wavelength", type=float, default=632.8,
                   help="Longitud de onda [nm] para Strehl y fringe spacings.  Default: 632.8")
    g.add_argument("--incidence", type=float, default=0.0,
                   help="Ángulo de incidencia [°] respecto a la normal; WFE = 2·cosθ·superficie. "
                        "Default: 0")
    g.add_argument("--iso-spec", default=None,
                   help="Tolerancia ISO 10110-5 a comprobar, p. ej. "
                        "\"3/900 nm (250 nm/100 nm) RMSi < 30 nm\"")
    g.add_argument("--iso-form", choices=["rot", "cyl"], default="rot",
                   help="Descomposición ISO: 'rot' (revolución: A, B, C) o 'cyl' "
                        "(cilíndrica/tórica: AX, AY, B, CX, CY).  Una indicación AX;AY fuerza "
                        "'cyl'.  Default: rot")
    g.add_argument("--iso-axis-angle", type=float, default=0.0,
                   help="Giro [°] de los ejes del cilindro/toro respecto a X/Y.  Default: 0")
    g.add_argument("--no-optics", action="store_true",
                   help="Omitir Strehl, PSF y magnitudes ISO 10110-5")
    e = parser.add_argument_group("Exportación a Zemax OpticStudio y QUADOA")
    e.add_argument("--export", default=None, metavar="RUTA_BASE",
                   help="Exportar rejilla de sag (Zemax Grid Sag .DAT y CSV x,y,z para QUADOA) y "
                        "coeficientes de Zernike (Fringe, Standard/Noll, ANSI).  Se añaden "
                        "sufijos a RUTA_BASE.")
    e.add_argument("--export-surface", choices=list(EXPORT_SURFACES), default="sin_rigido",
                   help="Superficie a exportar: sin sólido rígido o residuo tras el ajuste. "
                        "Default: sin_rigido")
    e.add_argument("--export-units", choices=list(ZEMAX_UNITFLAG), default="mm",
                   help="Unidades de lente del fichero exportado.  Default: mm")
    e.add_argument("--export-grid", type=int, default=101,
                   help="Puntos de la rejilla por lado (impar, ≥ 5).  Default: 101")
    e.add_argument("--export-interp", choices=["linear", "cubic"], default="linear",
                   help="Interpolación nodos → rejilla.  Default: linear")
    e.add_argument("--export-nmax", type=int, default=10,
                   help="Orden radial máximo de los Zernike Standard/ANSI.  Default: 10 (66 términos)")
    c = parser.add_argument_group(
        "Combinación de casos (en lugar de FNAME)",
        "FICHERO admite «ruta::caso» para ficheros con varios casos apilados.")
    c.add_argument("--gravity", nargs=2, action="append", metavar=("FICHERO", "ANGULO"),
                   help="Caso de gravedad calculado al ángulo dado [°] (repetir: ≥2 casos, "
                        "≥3 con --constant).  u(θ) = cosθ·A + sinθ·B (+C)")
    c.add_argument("--constant", action="store_true",
                   help="Incluir término constante C (precargas, montaje)")
    c.add_argument("--elevation", type=float, default=None,
                   help="Ángulo al que se analiza la combinación de gravedad")
    c.add_argument("--ref-elevation", type=float, default=None,
                   help="Ángulo de referencia: se analiza u(θ) − u(θ_ref)")
    c.add_argument("--sweep", nargs=3, type=float, default=None,
                   metavar=("INI", "FIN", "PASO"),
                   help="Barrido de RMS/PV frente al ángulo")
    c.add_argument("--combine", nargs=2, action="append", metavar=("FICHERO", "COEF"),
                   help="Combinación lineal Σ cₖ·uₖ (repetir)")
    c.add_argument("--save-combined", default=None,
                   help="Guardar los desplazamientos combinados en un TXT")

    args = parser.parse_args()
    if args.units:
        args.units = normalize_units(args.units)
    if args.sweep is not None and not args.gravity:
        parser.error("--sweep necesita --gravity (barrido de elevación de la combinación de gravedad).")
    if (args.elevation is not None or args.ref_elevation is not None or args.constant) \
            and not args.gravity:
        parser.error("--elevation, --ref-elevation y --constant sólo se usan con --gravity.")

    basis = basis_key(args.aperture, args.convention)
    if basis in ORTHO_BASES:
        args.norm = 'rms'

    if args.list_terms:
        print_term_table(basis)
        sys.exit(0)
    combining = bool(args.gravity or args.combine)
    if args.gravity and args.combine:
        parser.error("Usa --gravity o --combine, no ambos.")
    if args.gravity and args.elevation is None and args.sweep is None:
        parser.error("Con --gravity indica --elevation y/o --sweep.")
    if args.fname is None and not combining:
        parser.error("Se requiere el nombre del fichero de datos FEM.")

    if args.nterms is not None and args.terms is not None:
        parser.error("Usa --terms o --nterms, no ambos.")
    if args.nterms is not None:
        if args.nterms <= 0:
            args.no_zernike = True
            args.terms = default_terms(basis, 1)
        else:
            args.terms = default_terms(basis, args.nterms)
    if args.terms is None:
        args.terms = default_terms(basis, 4)
    terms = sorted(set(args.terms))
    try:
        for t in terms:
            term_info(basis, t)
        if basis in ORTHO_BASES and max(terms) > ORTHO_MAX_TERMS:
            raise ValueError(f"Máximo {ORTHO_MAX_TERMS} términos en esta base.")
    except ValueError as e:
        parser.error(str(e))

    if args.units is None:
        src = args.fname if not combining else _split_case(
            (args.gravity or args.combine)[0][0])[0]
        try:
            hu = header_units(src) if src else None
        except ValueError as e:
            _fail(f"{e}  (opción --units)")
        args.units = hu or 'mm'
        units_msg = (f"  Unidades: {args.units}"
                     + (" (cabecera del fichero)" if hu
                        else " (por defecto; usa --units si no son mm)"))
    else:
        units_msg = f"  Unidades: {args.units}"


    # ── Carga ────────────────────────────────────────────────────────────────
    print(f"\n{'═'*60}\n  fem_mirror_analysis.py\n{'═'*60}")
    gbasis = None
    if combining:
        try:
            coor, disp, gbasis, desc = _cli_combination(args)
        except ValueError as e:
            _fail(e)
        print("\n".join("  " + d for d in desc))
        if args.save_combined and disp is not None:
            save_fem_txt(args.save_combined, coor, disp, "\n".join(desc), units=args.units)
            print(f"  Desplazamientos combinados guardados en: {args.save_combined}")
    else:
        print(f"\n  Leyendo: {args.fname}")
        try:
            _, coor, disp = load_fem_data(args.fname, args.case)
        except ValueError as e:
            _fail(e)
    if args.case is not None and not combining:
        print(f"  Caso de carga: {args.case:g}")
    print(units_msg)
    print(f"  Nodos leídos: {len(coor)}")
    for k, ax in enumerate("XYZ"):
        print(f"  {ax} ∈ [{coor[:, k].min():.4g}, {coor[:, k].max():.4g}]")
    ndup = check_duplicates(coor)
    if ndup:
        print(f"  ⚠  {ndup} nodos con XY repetidas: se excluyen del análisis "
              f"(quedan fuera de la triangulación).")

    # ── Sistema de referencia ────────────────────────────────────────────────
    nbf = compute_bestfit_normal(coor)
    tilt = math.degrees(math.acos(min(1.0, float(nbf[2]))))
    print(f"\n  Normal del plano best-fit: ({nbf[0]:+.5f}, {nbf[1]:+.5f}, "
          f"{nbf[2]:+.5f})  → {tilt:.4f}° respecto a Z")
    if args.frame == 'bestfit':
        coor0 = coor
        coor, disp, finfo = to_local_frame(coor, disp if disp is not None else np.zeros_like(coor))
        if gbasis is not None:
            Rm = finfo['R']
            gbasis = {k: (v @ Rm.T if isinstance(v, np.ndarray) and v.ndim == 2 else v)
                      for k, v in gbasis.items()}
        print("  Sistema: plano best-fit (coordenadas y desplazamientos girados; "
              "Tx..Rz en ese sistema).")
    else:
        print("  Sistema: global (Z del fichero = eje óptico).")
        if tilt > 1.0:
            print("  ⚠  La superficie está inclinada respecto a Z.  Si es plana o "
                  "Z no es el eje óptico, usa --frame bestfit.")

    rigid_flags = tuple(args.rigid)
    ap_kw = dict(radius=args.radius, width=args.width, height=args.height,
                 center=tuple(args.center) if args.center else None,
                 inner_radius=args.inner_radius,
                 hex_rotation=0.0 if args.hex_orientation == 'x' else 30.0)
    if args.sweep is not None:
        _cli_sweep(args, coor, gbasis, rigid_flags, basis, terms, ap_kw)
        if args.elevation is None:
            print(f"\n{'═'*60}\n")
            return

    # ── Sólido rígido ────────────────────────────────────────────────────────
    active_names = [n for n, f in zip(['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz'], rigid_flags) if f]
    print(f"\n  Eliminando sólido rígido: {active_names if active_names else 'ninguno'}")
    un, an, pos = extract_rigid(coor, disp, rigid_flags, args.area_threshold,
                                quantity=args.quantity)
    nbad = int(np.sum(~np.isfinite(un)))
    if nbad:
        print(f"  ⚠  {nbad} nodos sin área en la triangulación (excluidos).")
    print_rigid_body_results(pos, rigid_flags)

    qname = ("cambio de sag Δz" if args.quantity == 'sag' else "desplazamiento normal u·n̂")
    print(f"\n  ── Error de superficie: {qname} (toda la superficie) ──")
    print(f"  RMS (pond. por área):        {rms_area_weighted(un, an):.6g}")
    print(f"  RMS resp. media (std):       {std_area_weighted(un, an):.6g}")
    print(f"  Pico a valle (P-V):          {peak_to_valley(un):.6g}")

    # ── Ajuste polinómico ────────────────────────────────────────────────────
    mask = np.zeros(len(coor), dtype=bool)
    residual = np.array([])
    geom = coords = None
    if not (args.no_zernike and args.no_optics) or args.export:
        try:
            mask, coords, geom = apply_aperture(coor[:, :2], un, an, args.aperture, **ap_kw)
        except ValueError as e:
            _fail(e)
    if not args.no_zernike:
        fam = BASIS_FAMILY_ES[basis]
        print(f"\n  ── Ajuste {fam} — apertura {args.aperture} ──")
        print(f"  Centro de la apertura ({'usuario' if args.center else 'centroide de área'}): "
              f"({geom['center'][0]:.4g}, {geom['center'][1]:.4g})")
        print("  " + describe_geometry(geom))
        print(f"  Nodos en apertura: {mask.sum()} / {len(mask)}")
        cov = mesh_coverage(coor[:, :2], an, geom)
        if cov is not None and cov < 0.82:
            print(f"  ⚠  La malla cubre sólo ~{cov*100:.0f}% de la apertura: parece un "
                  f"modelo parcial (simetría).  Revisa el centro (--center) y el radio.")
        if mask.sum() < len(terms):
            _fail(f"La apertura sólo contiene {int(mask.sum())} nodos y se piden "
                  f"{len(terms)} términos: reduce --nterms/--terms o revisa la apertura.")

        un_ap = un[mask]
        an_ap = an[mask] / an[mask].sum()
        coeffs, residual, _ = fit_surface(
            un_ap, coords, basis, terms, args.norm,
            weights=None if args.no_wls else an_ap)
        print(f"  Método: {'LS ordinario (--no-wls)' if args.no_wls else 'WLS ponderado por área'}"
              f" · normalización '{args.norm}'\n")
        contrib = term_contributions(un_ap, build_design_matrix(basis, terms, coords, args.norm),
                                     np.ones_like(an_ap) if args.no_wls else an_ap)
        print("\n".join(format_fit_table(basis, terms, coeffs, contrib)))

        rb, ra = rms_area_weighted(un_ap, an_ap), rms_area_weighted(residual, an_ap)
        print(f"\n  Dentro de la apertura — ANTES del ajuste:")
        print(f"    RMS = {rb:.6g}   (std = {std_area_weighted(un_ap, an_ap):.6g})")
        print(f"    P-V = {peak_to_valley(un_ap):.6g}")
        print(f"\n  Dentro de la apertura — RESIDUO tras el ajuste:")
        print(f"    RMS = {ra:.6g}   (std = {std_area_weighted(residual, an_ap):.6g})")
        print(f"    P-V = {peak_to_valley(residual):.6g}")
        if rb > 0:
            print(f"    Reducción de RMS: {(1.0 - ra / rb) * 100.0:.1f}%")

    if not args.no_optics and mask.any():
        un_normal = None
        if args.quantity != 'normal':
            un_normal, _, _ = extract_rigid(coor, disp, rigid_flags, args.area_threshold,
                                            quantity='normal')
        _cli_optics(args, coor, un, an, mask, coords, geom,
                    residual if (not args.no_zernike and residual.size) else None, un_normal)

    if args.export and mask.any():
        _cli_export(args, coor, un, an, mask, geom,
                    residual if (not args.no_zernike and residual.size) else None)

    print(f"\n{'═'*60}\n")

    if args.plot:
        if mask.any():
            plot_results(coor, un, mask, residual, args.aperture, args.plot_file)
        else:
            import matplotlib.pyplot as plt
            import matplotlib.tri as mtri
            ok = np.isfinite(un)
            fig, ax = plt.subplots(figsize=(8, 7))
            cf = ax.tricontourf(plot_triangulation(coor[ok, 0], coor[ok, 1]),
                                un[ok], levels=64, cmap=surface_cmap())
            plt.colorbar(cf, ax=ax, label='Error de superficie')
            ax.set_title('Error de superficie (tras quitar sólido rígido)')
            ax.set_aspect('equal')
            ax.set_xlabel('X'); ax.set_ylabel('Y')
            plt.tight_layout()
            plt.savefig(args.plot_file, dpi=150, bbox_inches='tight')
            print(f"\n  Gráfico guardado en: {args.plot_file}")
            plt.show()


def _fail(msg):
    """Error de datos en la línea de comandos: mensaje claro, sin el bloque
    de uso de argparse (reservado a errores de opciones)."""
    print(f"\n✗ Error: {msg}", file=sys.stderr)
    sys.exit(2)


def _cli_entry():
    """Punto de entrada de la línea de comandos: errores de datos o de
    opciones como mensaje claro, sin traza de Python."""
    try:
        main()
    except (ValueError, np.linalg.LinAlgError, OSError) as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    _cli_entry()
