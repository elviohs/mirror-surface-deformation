#!/usr/bin/env python3
"""
Interfaz gráfica para fem_mirror_analysis.py
Requiere: tkinter (incluido en Python estándar), numpy, scipy, matplotlib
"""
import sys
import os
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox

# ── Añadir el directorio del script al path para importar fem_mirror_analysis ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# ── Logo del departamento (PNG 104×60, embebido como base64) ──────────
_LOGO_B64 = (
    "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"
)


# ═══════════════════════════════════════════════════════════════════
#  UTILIDADES DE VISUALIZACIÓN
# ═══════════════════════════════════════════════════════════════════

# Aperturas de la GUI → nombre interno en fem_mirror_analysis
APERTURE_KEYS = {'Circular': 'circular', 'Anular': 'annular',
                 'Hexagonal': 'hexagonal', 'Rectangular': 'rectangular',
                 'Elíptica': 'elliptical'}
APERTURES_ENABLED = tuple(APERTURE_KEYS)

BASIS_TEXT = {
    'Circular': ("Base: Zernike circular. Fringe 1-5 incluye astig. 0°; Noll 1-5 incluye "
                 "astig. 45°."),
    'Anular': ("Base: Zernike anulares de Mahajan (1981), ortonormales sobre el anillo; "
               "orden de Noll (A1 pistón, A2-A3 tilts, A4 desenfoque…)."),
    'Hexagonal': ("Base: ortonormales hexagonales de Mahajan–Dai (2006); orden de Noll "
                  "(H1 pistón, H2-H3 tilts, H4 desenfoque…)."),
    'Rectangular': ("Base: ortonormales rectangulares de Mahajan–Dai (2007); un cuadrado es "
                    "ancho = alto. Orden de Noll (R1 pistón, R2-R3 tilts, R4 desenfoque…)."),
    'Elíptica': ("Base: Zernike circular en coordenadas escaladas x/a, y/b (ISO/TR 14999-2, "
                 "6.8.3), p. ej. espejos plegados. Ejes de la elipse paralelos a X e Y."),
}


def _draw_aperture_boundary(ax, geom):
    """
    Dibuja el contorno de la apertura (línea negra discontinua) sobre 'ax'
    usando la geometría devuelta por fem_mirror_analysis.apply_aperture.
    """
    import fem_mirror_analysis as _m
    for xs, ys in _m.aperture_outline(geom):
        ax.plot(xs, ys, color='black', lw=1.5, ls='--', zorder=5)


# ═══════════════════════════════════════════════════════════════════
#  LÓGICA DE ANÁLISIS  (se ejecuta en hilo secundario)
# ═══════════════════════════════════════════════════════════════════

def run_analysis(params, log, schedule, embed_fig=None, result_store=None):
    """
    Ejecuta el análisis FEM completo.

    params       : dict con todos los parámetros de la GUI
    log          : función log(texto) para escribir en el widget de resultados
    schedule     : función schedule(ms, fn) para ejecutar fn en el hilo principal
    embed_fig    : función embed_fig(fig) para mostrar la figura en la GUI
                   (si es None se usa plt.show() en ventana externa)
    result_store : lista de un elemento [None] donde se guardan los datos
                   del análisis para la vista 3D posterior
    """
    try:
        import numpy as np
        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as plt
        import importlib

        # ── Importar el módulo de análisis ──────────────────────────────
        m = importlib.import_module('fem_mirror_analysis')

        # ── 1. Cargar datos ─────────────────────────────────────────────
        log("Cargando datos FEM…\n")
        _, coor, disp = m.load_fem_data(params['fname'], params.get('case'))
        if params.get('case') is not None:
            log(f"  Caso de carga: {params['case']:g}\n")
        log(f"  {len(coor):,} nodos leídos.\n")
        ndup = m.check_duplicates(coor)
        if ndup:
            log(f"  ⚠ {ndup:,} nodos con XY repetidas: quedan fuera de la "
                f"triangulación y se excluyen.\n")

        # ── 1b. Sistema de referencia ───────────────────────────────────
        import math as _m
        nbf = m.compute_bestfit_normal(coor)
        tilt = _m.degrees(_m.acos(min(1.0, float(nbf[2]))))
        log(f"  Normal plano best-fit: ({nbf[0]:+.5f}, {nbf[1]:+.5f}, {nbf[2]:+.5f})"
            f" → {tilt:.4f}° respecto a Z\n")
        if params['frame'] == 'bestfit':
            coor, disp, _ = m.to_local_frame(coor, disp)
            log("  Sistema: plano best-fit (datos girados; Tx..Rz en ese sistema).\n\n")
        else:
            log("  Sistema: global (Z = eje óptico).\n")
            if tilt > 1.0:
                log("  ⚠ La superficie está inclinada respecto a Z. Si es plana o Z no es "
                    "el eje óptico, usa 'Plano best-fit'.\n")
            log("\n")

        # ── 2. Extraer sólido rígido ─────────────────────────────────────
        rigid = params['rigid']
        active = [('Tx','Ty','Tz','Rx','Ry','Rz')[i] for i, v in enumerate(rigid) if v]
        if active:
            log(f"Eliminando modos de sólido rígido: {', '.join(active)}\n")
        else:
            log("No se eliminan modos de sólido rígido.\n")

        un, an, pos = m.extract_rigid(coor, disp, rigid, quantity=params['quantity'])
        log("  Error de superficie: " + ("cambio de sag Δz = (u·n̂)/n_z" if params['quantity'] == 'sag'
            else "desplazamiento normal u·n") + "\n")
        nbad = int(np.sum(~np.isfinite(un)))
        if nbad:
            log(f"  ⚠ {nbad:,} nodos sin área en la triangulación (excluidos).\n")

        labels = ['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']
        for i, lbl in enumerate(labels):
            if rigid[i]:
                log(f"  {lbl} = {pos[i]:+.6e}\n")

        rms_total = m.rms_area_weighted(un, an)
        pv_total  = m.peak_to_valley(un)
        log(f"\nRMS error de superficie   : {rms_total:.6e}\n")
        log(f"RMS resp. media (std)     : {m.std_area_weighted(un, an):.6e}\n")
        log(f"Peak-to-valley            : {pv_total:.6e}\n")

        # ── 3. Máscara de apertura ───────────────────────────────────────
        aperture = params['aperture']
        ap_key   = APERTURE_KEYS[aperture]
        xy = coor[:, :2]

        log(f"\nCalculando apertura '{aperture}'…\n")
        _f = lambda k: float(params[k]) if params.get(k) else None
        center = None
        if params.get('cx') and params.get('cy'):
            center = (float(params['cx']), float(params['cy']))
        mask, coords, geom = m.apply_aperture(
            xy, un, an, ap_key, radius=_f('radius'), width=_f('width'),
            height=_f('height'), center=center, inner_radius=_f('rin'),
            hex_rotation=0.0 if params.get('hexorient', 'x') == 'x' else 30.0)
        log(f"  Centro ({'usuario' if center else 'centroide de área'}): "
            f"({geom['center'][0]:.5g}, {geom['center'][1]:.5g})\n")
        log("  " + m.describe_geometry(geom) + "\n")
        log(f"  {mask.sum():,} nodos dentro de la apertura.\n")

        # ── 4. Ajuste polinómico ─────────────────────────────────────────
        nterms   = params['nterms']
        norm     = params['norm']
        basis    = m.basis_key(ap_key, params['convention'])
        fam      = m.BASIS_FAMILY_ES[basis]
        if basis in m.ORTHO_BASES:
            norm = 'rms'                     # bases ortonormales
        un_ap    = un[mask]
        an_ap    = an[mask]
        an_ap    = an_ap / an_ap.sum()
        residual = un_ap.copy()   # si no hay ajuste, residuo = señal

        if nterms > 0:
            metodo = 'WLS ponderado por área' if params['wls'] else 'LS ordinario'
            log(f"\nAjustando {nterms} términos {fam} ({metodo}, norma '{norm}')…\n")
            term_indices = m.default_terms(basis, nterms)
            coeffs, residual, _ = m.fit_surface(
                un_ap, coords, basis, term_indices, norm,
                weights=an_ap if params['wls'] else None)
            rms_res = m.rms_area_weighted(residual, an_ap)
            pv_res  = m.peak_to_valley(residual)
            log(f"  RMS residuo : {rms_res:.6e}\n")
            log(f"  std residuo : {m.std_area_weighted(residual, an_ap):.6e}\n")
            log(f"  PV  residuo : {pv_res:.6e}\n\n")
            contrib = m.term_contributions(
                un_ap, m.build_design_matrix(basis, term_indices, coords, norm), an_ap)
            log("\n".join(m.format_fit_table(basis, term_indices, coeffs, contrib)) + "\n")
        else:
            rms_res = m.rms_area_weighted(residual, an_ap)
            pv_res  = m.peak_to_valley(residual)

        # ── 4a. Calidad óptica e ISO 10110-5 ─────────────────────────────
        optics = None
        if params.get('optics', True):
            try:
                if params['quantity'] == 'normal':
                    un_iso = un_ap
                else:                      # ISO 14999-4:2015, 3.2.1: desviación normal
                    un_n, _, _ = m.extract_rigid(coor, disp, rigid, quantity='normal')
                    un_iso = un_n[mask]
                optics = m.optics_summary(
                    un_ap, an_ap, coords, geom, xy[mask], params['units'],
                    params['wavelength'], params['incidence'],
                    residual=residual if nterms > 0 else None,
                    iso_spec=params.get('iso_spec') or None,
                    x=coor[:, 0], y=coor[:, 1], z_ap=coor[mask, 2], iso_u=un_iso,
                    iso_form=params.get('iso_form', 'rot'),
                    axis_angle_deg=params.get('iso_axis', 0.0))
                log("\n" + "\n".join(optics['lines']) + "\n")
            except Exception as e:
                log(f"\n⚠ Calidad óptica / ISO 10110-5 no calculadas: {e}\n")
                optics = None

        # ── 4b. Datos para el informe Word ───────────────────────────────
        report_data = None
        try:
            import report_fem_mirror as rp
            if nterms > 0:
                report_data = rp.build_report_data(
                    params, coor, un, an, pos, rigid, mask, geom,
                    basis=basis, terms=term_indices, coeffs=coeffs,
                    residual=residual, wls=params['wls'], norm=norm,
                    ndup=ndup, tilt_deg=tilt, contrib=contrib,
                    quantity=params['quantity'], optics=optics)
            else:
                report_data = rp.build_report_data(
                    params, coor, un, an, pos, rigid, mask, geom,
                    ndup=ndup, tilt_deg=tilt, quantity=params['quantity'],
                    optics=optics)
        except Exception:
            log(f"\n⚠ No se pudieron preparar los datos del informe:\n"
                f"{traceback.format_exc()}\n")

        # ── 5. Figura ────────────────────────────────────────────────────
        log("\nGenerando figura…\n")

        def show_fig():
            try:
                x, y = coor[:, 0], coor[:, 1]
                import matplotlib.tri as mtri
                import numpy as np_local

                fig, axes = plt.subplots(1, 3, figsize=(17, 5))
                fig.suptitle('Análisis FEM – Superficie de espejo', fontsize=12)

                # Coordenadas centradas (para contorno de apertura)
                cx, cy       = float(x.mean()), float(y.mean())
                xc_all       = x - cx
                yc_all       = y - cy

                # Panel izquierdo: desplazamiento normal (todos los nodos válidos)
                valid_full = np_local.isfinite(un)
                if valid_full.sum() > 3:
                    tri_full = m.plot_triangulation(x[valid_full], y[valid_full])
                    cf1 = axes[0].tricontourf(tri_full, un[valid_full], levels=64, cmap=m.surface_cmap())
                    plt.colorbar(cf1, ax=axes[0], label='Error superficie')
                else:
                    axes[0].text(0.5, 0.5, 'Sin datos válidos', ha='center', va='center',
                                 transform=axes[0].transAxes)
                axes[0].set_title(
                    f'Error de superficie\n(tras extracción sólido rígido)\n'
                    f'RMS = {rms_total:.3e}   PV = {pv_total:.3e}',
                    fontsize=9)
                axes[0].set_aspect('equal')
                axes[0].set_xlabel('X')
                axes[0].set_ylabel('Y')

                # Interpolador para mostrar valor z al pasar el ratón (panel 0)
                if valid_full.sum() > 3:
                    _interp0 = mtri.LinearTriInterpolator(tri_full, un[valid_full])
                    def _fmt0(xm, ym, _i=_interp0):
                        zv = float(_i(xm, ym))
                        zs = f'{zv:.4e}' if np_local.isfinite(zv) else '—'
                        return f'X={xm:.4f}  Y={ym:.4f}  Error={zs}'
                    axes[0].format_coord = _fmt0

                # Panel derecho: residuo de Zernike solo en la apertura
                un_res_full = np_local.full(len(coor), np_local.nan)
                un_res_full[mask] = residual
                valid = ~np_local.isnan(un_res_full)
                if valid.sum() > 3:
                    tri_ap = m.plot_triangulation(x[valid], y[valid])
                    cf2 = axes[1].tricontourf(tri_ap, un_res_full[valid], levels=64, cmap=m.surface_cmap())
                    plt.colorbar(cf2, ax=axes[1], label='Residuo')

                    # Interpolador para mostrar valor z al pasar el ratón (panel 1)
                    _label1 = f'Residuo {fam}' if nterms > 0 else 'Error (apertura)'
                    _interp1 = mtri.LinearTriInterpolator(tri_ap, un_res_full[valid])
                    def _fmt1(xm, ym, _i=_interp1, _l=_label1):
                        zv = float(_i(xm, ym))
                        zs = f'{zv:.4e}' if np_local.isfinite(zv) else '—'
                        return f'X={xm:.4f}  Y={ym:.4f}  {_l}={zs}'
                    axes[1].format_coord = _fmt1

                title2 = (f'Residuo {fam} ({nterms} términos)\napertura {aperture}'
                          if nterms > 0 else f'Apertura {aperture}')
                axes[1].set_title(
                    f'{title2}\nRMS = {rms_res:.3e}   PV = {pv_res:.3e}',
                    fontsize=9)
                axes[1].set_aspect('equal')
                axes[1].set_xlabel('X')
                axes[1].set_ylabel('Y')

                # ── Panel derecho: PSF física (λ, incidencia) ────────────────
                psf = optics.get('psf') if optics else None
                if psf and 'psf' in psf:
                    psf_log = np_local.log10(np_local.maximum(psf['psf'], 1e-7))
                    ext = psf['extent']
                    im_psf = axes[2].imshow(psf_log, origin='lower', cmap='inferno',
                                            extent=ext, vmin=-6, vmax=0)
                    plt.colorbar(im_psf, ax=axes[2], label='log₁₀(PSF / pico ideal)')
                    on = 'residuo' if psf['on'] == 'residual' else 'superficie'
                    oq = optics['wfe_residual'] if psf['on'] == 'residual' else optics['wfe_surface']
                    axes[2].set_title(
                        f"PSF ({on}) · λ = {optics['wavelength']:g} nm\n"
                        f"Strehl FFT = {psf['strehl']:.4f} · Maréchal = {oq['strehl']:.4f}",
                        fontsize=9)
                    axes[2].set_xlabel('λ/D')
                    axes[2].set_ylabel('λ/D')
                    _pr, _pc = psf_log.shape
                    def _fmt2(xm, ym, _arr=psf_log, _r=_pr, _c=_pc, _e=ext):
                        col = int((_c - 1) * (xm - _e[0]) / (_e[1] - _e[0]) + 0.5)
                        row = int((_r - 1) * (ym - _e[2]) / (_e[3] - _e[2]) + 0.5)
                        zs = f'{_arr[row, col]:.3f}' if 0 <= row < _r and 0 <= col < _c else '—'
                        return f'x={xm:.2f} λ/D  y={ym:.2f} λ/D  log₁₀(PSF)={zs}'
                    axes[2].format_coord = _fmt2
                else:
                    axes[2].text(0.5, 0.5, 'PSF no disponible\n(revisa unidades y λ)',
                                 ha='center', va='center', transform=axes[2].transAxes)
                    axes[2].set_axis_off()

                # ── Casco convexo de los datos FEM reales (línea blanca) ──────
                from scipy.spatial import ConvexHull
                valid_pts = np_local.column_stack([x[valid_full], y[valid_full]])
                try:
                    hull = ConvexHull(valid_pts)
                    hv   = hull.vertices
                    hv   = np_local.append(hv, hv[0])          # cerrar el polígono
                    for ax in axes[:2]:
                        ax.plot(valid_pts[hv, 0], valid_pts[hv, 1],
                                'w-', lw=1.4, alpha=0.85, zorder=4,
                                label='Límite datos FEM')
                    # Fracción de la apertura teórica cubierta por los datos
                    cov = m.mesh_coverage(xy, an, geom)
                    if cov is not None:
                        pct = 100.0 * cov
                        schedule(0, lambda p=pct: log(
                            f"\n  ℹ Los datos FEM cubren ~{p:.0f}% del área de la apertura.\n"
                            + ("    Parece un modelo parcial (simetría): revisa el centro "
                               "y el tamaño de la apertura.\n" if p < 82 else "")))
                except Exception:
                    pass   # si hay < 3 puntos válidos, ConvexHull falla — ignorar

                # ── Contorno de apertura teórica (línea negra discontinua) ──
                _draw_aperture_boundary(axes[0], geom)
                _draw_aperture_boundary(axes[1], geom)

                # ── Leyenda (solo paneles de superficie) ─────────────────────
                import matplotlib.lines as mlines
                leg_data = mlines.Line2D([], [], color='white', lw=1.4, label='Límite datos FEM')
                leg_ap   = mlines.Line2D([], [], color='black', lw=1.5, ls='--',
                                          label=f'Apertura {aperture}')
                for ax in axes[:2]:
                    ax.legend(handles=[leg_data, leg_ap], loc='lower right',
                              fontsize=7, framealpha=0.6)

                plt.tight_layout()

                # Guardar datos para la vista 3D posterior
                if result_store is not None:
                    result_store[0] = {
                        'x':        x,
                        'y':        y,
                        'z_res':    un_res_full,
                        'valid':    valid,
                        'fam':      fam,
                        'rms_res':  rms_res,
                        'pv_res':   pv_res,
                        'nterms':   nterms,
                        'aperture': aperture,
                        'report':   report_data,
                        'export': {
                            'xy': xy[mask], 'un': un_ap,
                            'res': residual if nterms > 0 else None,
                            'w': an_ap, 'geom': geom, 'units': params['units'],
                            'quantity': params['quantity'], 'frame': params['frame'],
                            'fname': params.get('fname'), 'case': params.get('case'),
                        },
                    }

                # Mostrar en la GUI (embebida) o en ventana externa
                # Para guardar la imagen usa el botón 💾 de la barra de navegación inferior.
                if embed_fig is not None:
                    embed_fig(fig)
                else:
                    plt.show()

            except Exception:
                log(f"\n✗ Error al generar figura:\n{traceback.format_exc()}\n")

        # Mostrar la figura en el hilo principal de Tk
        schedule(0, show_fig)
        log("\n✓ Análisis completado.\n")

    except FileNotFoundError as e:
        log(f"\n✗ Archivo no encontrado: {e}\n")
    except Exception:
        log(f"\n✗ Error durante el análisis:\n{traceback.format_exc()}\n")


# ═══════════════════════════════════════════════════════════════════
#  INTERFAZ GRÁFICA
# ═══════════════════════════════════════════════════════════════════

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Análisis FEM – Superficie de espejo")
        self.resizable(True, True)
        self.minsize(700, 700)

        style = ttk.Style(self)
        style.theme_use('clam')

        self._result_store = [None]   # datos del último análisis para vista 3D

        self._build_ui()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)   # log se expande
        self.rowconfigure(7, weight=3)   # figura ocupa más espacio

    # ── Construcción de widgets ─────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=10, pady=5)

        # ── Archivo de datos ─────────────────────────────────────────
        frm_file = ttk.LabelFrame(self, text="Archivo de datos FEM")
        frm_file.grid(row=0, column=0, sticky='ew', **pad)
        frm_file.columnconfigure(0, weight=1)

        self.fname_var = tk.StringVar()
        ttk.Entry(frm_file, textvariable=self.fname_var, width=60).grid(
            row=0, column=0, padx=(6, 4), pady=6, sticky='ew')
        frm_fb = ttk.Frame(frm_file)
        frm_fb.grid(row=0, column=1, padx=(0, 6), pady=6)
        ttk.Button(frm_fb, text="Examinar…", command=self._browse).grid(row=0, column=0)
        ttk.Button(frm_fb, text="Combinar casos…", command=self._open_combine).grid(
            row=0, column=1, padx=(6, 0))

        # Logo del departamento (columna 2, rowspan=2)
        try:
            _logo_img = tk.PhotoImage(data=_LOGO_B64)
            _logo_lbl = ttk.Label(frm_file, image=_logo_img)
            _logo_lbl.image = _logo_img        # evitar que el GC destruya la imagen
            _logo_lbl.grid(row=0, column=2, rowspan=2, padx=(6, 10), pady=4, sticky='e')
        except Exception:
            pass   # si el entorno no soporta PhotoImage con data=, continúa sin logo

        # Caso de carga (ficheros con varios casos apilados)
        frm_case = ttk.Frame(frm_file)
        frm_case.grid(row=1, column=0, columnspan=2, padx=6, pady=(0, 4), sticky='w')
        ttk.Label(frm_case, text="Caso de carga:").grid(row=0, column=0, padx=(0, 4))
        self.case_var = tk.StringVar(value='')
        self.cb_case = ttk.Combobox(frm_case, textvariable=self.case_var,
                                    width=8, state='disabled', values=[])
        self.cb_case.grid(row=0, column=1)
        self.lbl_case = ttk.Label(frm_case, text="(fichero con un único caso)",
                                  foreground='gray')
        self.lbl_case.grid(row=0, column=2, padx=6)

        # Nota de formato del fichero TXT
        _fmt_text = (
            "Formato TXT: una línea por nodo  →  node_id   X   Y   Z   dX   dY   dZ  "
            "(o X Y Z dX dY dZ)\n"
            "Columnas separadas por espacios o tabuladores; se ignoran las líneas que "
            "empiecen por '#'. Si la 1ª columna se repite, se interpreta como nº de caso de carga.\n"
            "Exportar sólo los nodos de la superficie óptica. Por defecto la apertura se "
            "centra en el centroide de área de la malla."
        )
        ttk.Label(frm_file, text=_fmt_text, foreground='#555555',
                  wraplength=680, justify='left').grid(
            row=2, column=0, columnspan=2, padx=6, pady=(0, 6), sticky='w')

        # ── Sólido rígido y sistema de referencia ─────────────────────
        frm_rigid = ttk.LabelFrame(self, text="Modos de sólido rígido a eliminar")
        frm_rigid.grid(row=1, column=0, sticky='ew', **pad)

        self.rigid_vars = []
        defaults = [True, True, True, True, True, True]
        for i, lbl in enumerate(['Tx', 'Ty', 'Tz', 'Rx', 'Ry', 'Rz']):
            v = tk.BooleanVar(value=defaults[i])
            self.rigid_vars.append(v)
            ttk.Checkbutton(frm_rigid, text=lbl, variable=v).grid(
                row=0, column=i, padx=8, pady=6)

        ttk.Separator(frm_rigid, orient='vertical').grid(
            row=0, column=6, sticky='ns', padx=8, pady=4)
        ttk.Label(frm_rigid, text="Sistema:").grid(row=0, column=7, padx=(4, 2))
        self.frame_var = tk.StringVar(value='global')
        ttk.Radiobutton(frm_rigid, text='Global (Z = eje óptico)',
                        variable=self.frame_var, value='global').grid(row=0, column=8, padx=4)
        ttk.Radiobutton(frm_rigid, text='Plano best-fit',
                        variable=self.frame_var, value='bestfit').grid(row=0, column=9, padx=4)

        ttk.Label(frm_rigid, text="Error de superficie:").grid(
            row=1, column=0, columnspan=3, padx=8, pady=(0, 6), sticky='w')
        self.quantity_var = tk.StringVar(value='sag')
        ttk.Radiobutton(frm_rigid, text='Cambio de sag Δz (recomendado)',
                        variable=self.quantity_var, value='sag').grid(
            row=1, column=3, columnspan=4, padx=4, pady=(0, 6), sticky='w')
        ttk.Radiobutton(frm_rigid, text='Normal u·n',
                        variable=self.quantity_var, value='normal').grid(
            row=1, column=7, columnspan=3, padx=4, pady=(0, 6), sticky='w')

        # ── Apertura ─────────────────────────────────────────────────
        frm_ap = ttk.LabelFrame(self, text="Apertura del espejo")
        frm_ap.grid(row=2, column=0, sticky='ew', **pad)
        frm_ap.columnconfigure(5, weight=1)

        self.ap_var = tk.StringVar(value='Circular')
        apertures = ['Circular', 'Anular', 'Hexagonal', 'Rectangular', 'Elíptica']
        for i, name in enumerate(apertures):
            ttk.Radiobutton(frm_ap, text=name, variable=self.ap_var,
                            value=name, command=self._update_ap_fields).grid(
                row=0, column=i, padx=10, pady=6)

        # Sub-frame para parámetros opcionales de apertura
        self.frm_ap_extra = ttk.Frame(frm_ap)
        self.frm_ap_extra.grid(row=1, column=0, columnspan=6, sticky='ew', padx=6, pady=(0, 6))
        self._ap_extra_widgets = {}
        self._build_ap_extras()

        # ── Polinomios de ajuste ──────────────────────────────────────
        frm_zern = ttk.LabelFrame(self, text="Polinomios de ajuste")
        frm_zern.grid(row=3, column=0, sticky='ew', **pad)

        ttk.Label(frm_zern, text="Número de términos:").grid(row=0, column=0, padx=8, pady=6)
        self.nterms_var = tk.IntVar(value=3)
        sp = ttk.Spinbox(frm_zern, from_=0, to=200, textvariable=self.nterms_var, width=6)
        sp.grid(row=0, column=1, padx=4, pady=6)
        ttk.Label(frm_zern, text="  (0 = solo RMS, sin ajuste)").grid(
            row=0, column=2, padx=0, pady=6, sticky='w')

        ttk.Label(frm_zern, text="Normalización:").grid(row=0, column=3, padx=(20, 4), pady=6)
        self.norm_var = tk.StringVar(value='pico')
        self.rb_pico = ttk.Radiobutton(frm_zern, text='Pico', variable=self.norm_var, value='pico')
        self.rb_pico.grid(row=0, column=4, pady=6)
        self.rb_rms = ttk.Radiobutton(frm_zern, text='RMS', variable=self.norm_var, value='rms')
        self.rb_rms.grid(row=0, column=5, padx=4, pady=6)

        ttk.Label(frm_zern, text="Convención Zernike:").grid(row=1, column=0, padx=8, pady=(0, 6))
        self.conv_var = tk.StringVar(value='fringe')
        self.rb_fringe = ttk.Radiobutton(frm_zern, text='Fringe', variable=self.conv_var,
                                         value='fringe')
        self.rb_fringe.grid(row=1, column=1, pady=(0, 6), sticky='w')
        self.rb_noll = ttk.Radiobutton(frm_zern, text='Noll', variable=self.conv_var,
                                       value='noll')
        self.rb_noll.grid(row=1, column=2, pady=(0, 6), sticky='w')

        self.wls_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_zern, text='WLS (ponderado por área)',
                        variable=self.wls_var).grid(row=1, column=3, columnspan=3,
                                                     padx=(20, 4), pady=(0, 6), sticky='w')

        self.lbl_basis = ttk.Label(frm_zern, text='', foreground='#1f5fa8')
        self.lbl_basis.grid(row=2, column=0, columnspan=6, padx=8, pady=(0, 6), sticky='w')
        self._update_ap_fields()

        # ── Calidad óptica e ISO 10110-5 ──────────────────────────────
        frm_opt = ttk.LabelFrame(self, text="Calidad óptica e ISO 10110-5")
        frm_opt.grid(row=4, column=0, sticky='ew', **pad)
        frm_opt.columnconfigure(7, weight=1)
        ttk.Label(frm_opt, text="Unidades del fichero:").grid(row=0, column=0, padx=(8, 4), pady=6)
        self.units_var = tk.StringVar(value='mm')
        ttk.Combobox(frm_opt, textvariable=self.units_var, width=5, state='readonly',
                     values=['mm', 'm', 'µm', 'nm']).grid(row=0, column=1, padx=(0, 12))
        ttk.Label(frm_opt, text="λ [nm]:").grid(row=0, column=2, padx=(0, 4))
        self.lambda_var = tk.StringVar(value='632.8')
        ttk.Entry(frm_opt, textvariable=self.lambda_var, width=8).grid(row=0, column=3, padx=(0, 12))
        ttk.Label(frm_opt, text="Incidencia [°]:").grid(row=0, column=4, padx=(0, 4))
        self.incid_var = tk.StringVar(value='0')
        ttk.Entry(frm_opt, textvariable=self.incid_var, width=6).grid(row=0, column=5, padx=(0, 12))
        self.optics_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_opt, text='Calcular', variable=self.optics_var).grid(
            row=0, column=6, padx=(0, 8))
        ttk.Label(frm_opt, text="Tolerancia ISO (opcional):").grid(
            row=1, column=0, padx=(8, 4), pady=(0, 6), sticky='w')
        self.iso_spec_var = tk.StringVar(value='')
        ttk.Entry(frm_opt, textvariable=self.iso_spec_var, width=50).grid(
            row=1, column=1, columnspan=6, padx=(0, 8), pady=(0, 6), sticky='ew')
        ttk.Label(frm_opt, text="p. ej.  3/900 nm (250 nm/100 nm) RMSi < 30 nm   ·   "
                                "tórica: 3/10;2 (1/-;0,3) ΔS2-dim(5 µrad/5/1)",
                  foreground='gray').grid(row=1, column=7, padx=(0, 8), pady=(0, 6), sticky='w')
        ttk.Label(frm_opt, text="Descomposición ISO:").grid(
            row=2, column=0, padx=(8, 4), pady=(0, 6), sticky='w')
        frm_form = ttk.Frame(frm_opt)
        frm_form.grid(row=2, column=1, columnspan=7, sticky='w', pady=(0, 6))
        self.iso_form_var = tk.StringVar(value='rot')
        ttk.Radiobutton(frm_form, text="De revolución (A, B, C)", variable=self.iso_form_var,
                        value='rot').grid(row=0, column=0, padx=(0, 12))
        ttk.Radiobutton(frm_form, text="Cilíndrica / tórica (AX, AY, B, CX, CY)",
                        variable=self.iso_form_var, value='cyl').grid(row=0, column=1, padx=(0, 12))
        ttk.Label(frm_form, text="Giro de los ejes [°]:").grid(row=0, column=2, padx=(0, 4))
        self.iso_axis_var = tk.StringVar(value='0')
        ttk.Entry(frm_form, textvariable=self.iso_axis_var, width=6).grid(row=0, column=3)
        ttk.Label(frm_form, text="(valores normales a la superficie, ISO 14999-4:2015)",
                  foreground='gray').grid(row=0, column=4, padx=(12, 0))

        # ── Botón ejecutar ─────────────────────────────────────────────
        frm_btns = ttk.Frame(self)
        frm_btns.grid(row=5, column=0, pady=10)

        self.btn_run = ttk.Button(frm_btns, text="▶  Ejecutar análisis",
                                  command=self._run, style='Accent.TButton')
        self.btn_run.grid(row=0, column=0)

        # ── Log de resultados ─────────────────────────────────────────
        frm_log = ttk.LabelFrame(self, text="Resultados")
        frm_log.grid(row=6, column=0, sticky='nsew', **pad)
        frm_log.columnconfigure(0, weight=1)
        frm_log.rowconfigure(0, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            frm_log, wrap=tk.WORD, font=('Consolas', 9),
            state='disabled', height=12, background='#1e1e1e', foreground='#d4d4d4')
        self.log_text.grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        btn_clear = ttk.Button(frm_log, text="Limpiar", command=self._clear_log, width=8)
        btn_clear.grid(row=1, column=0, sticky='e', padx=4, pady=(0, 4))

        # ── Panel de figura embebida ──────────────────────────────────
        self.frm_fig = ttk.LabelFrame(self, text="Figura")
        self.frm_fig.grid(row=7, column=0, sticky='nsew', **pad)

        # ── Controles Vista 3D (debajo de la figura) ───────────────────
        frm_3d = ttk.Frame(self)
        frm_3d.grid(row=8, column=0, pady=(4, 6))

        ttk.Label(frm_3d, text="Escala Z:").grid(row=0, column=0, padx=(0, 4))
        self.scale3d_var = tk.StringVar(value='10E6')
        ttk.Entry(frm_3d, textvariable=self.scale3d_var, width=8).grid(
            row=0, column=1, padx=(0, 8))

        self.btn_3d = ttk.Button(frm_3d, text="🎨  Vista 3D",
                                 command=self._show_3d, state='disabled')
        self.btn_3d.grid(row=0, column=2)

        # ── Informe Word (junto a Vista 3D) ────────────────────────────
        ttk.Separator(frm_3d, orient='vertical').grid(
            row=0, column=3, sticky='ns', padx=14, pady=2)
        ttk.Label(frm_3d, text="Informe:").grid(row=0, column=4, padx=(0, 4))
        self.report_lang_var = tk.StringVar(value='Español')
        ttk.Combobox(frm_3d, textvariable=self.report_lang_var, width=8,
                     state='readonly', values=['Español', 'English']).grid(
            row=0, column=5, padx=(0, 8))
        self.btn_report = ttk.Button(frm_3d, text="📄  Generar informe",
                                     command=self._make_report, state='disabled')
        self.btn_report.grid(row=0, column=8)

        # ── Exportación a Zemax / QUADOA ───────────────────────────────
        ttk.Separator(frm_3d, orient='vertical').grid(
            row=0, column=9, sticky='ns', padx=14, pady=2)
        self.btn_export = ttk.Button(frm_3d, text="🔭  Exportar Zemax / QUADOA…",
                                     command=self._open_export, state='disabled')
        self.btn_export.grid(row=0, column=10)

        self.frm_fig.columnconfigure(0, weight=1)
        self.frm_fig.rowconfigure(0, weight=1)

        # Placeholder mientras no hay figura
        self._fig_placeholder = ttk.Label(
            self.frm_fig,
            text="La figura aparecerá aquí al completar el análisis.",
            foreground='gray')
        self._fig_placeholder.grid(row=0, column=0, padx=10, pady=40)

        self._canvas = None   # FigureCanvasTkAgg actual

    def _build_ap_extras(self):
        """Crea todos los sub-widgets de parámetros de apertura (ocultos por defecto)."""
        f = self.frm_ap_extra
        widgets = {}

        def row(key, label, default=''):
            lbl = ttk.Label(f, text=label)
            var = tk.StringVar(value=default)
            ent = ttk.Entry(f, textvariable=var, width=10)
            widgets[key] = (lbl, ent, var)

        row('radius',    'Radio (vacío = auto):')
        row('rin',       'Radio interior (vacío = auto):')
        row('width',     'Ancho X (vacío = auto):')
        row('height',    'Alto Y (vacío = auto):')
        row('cx',        'Centro X (vacío = auto):')
        row('cy',        'Centro Y:')

        # Orientación del hexágono
        lbl = ttk.Label(f, text='Vértices en:')
        var = tk.StringVar(value='±X')
        cb = ttk.Combobox(f, textvariable=var, width=4, state='readonly', values=['±X', '±Y'])
        widgets['hexorient'] = (lbl, cb, var)

        self._ap_extra_widgets = widgets

    def _update_ap_fields(self):
        """Muestra los campos de la apertura elegida y ajusta la base polinómica."""
        ap = self.ap_var.get()
        visible = {
            'Circular':    ['radius', 'cx', 'cy'],
            'Anular':      ['radius', 'rin', 'cx', 'cy'],
            'Hexagonal':   ['radius', 'hexorient', 'cx', 'cy'],
            'Rectangular': ['width', 'height', 'cx', 'cy'],
            'Elíptica':    ['width', 'height', 'cx', 'cy'],
        }.get(ap, [])
        self._ap_extra_widgets['width'][0].configure(
            text='Eje X (vacío = auto):' if ap == 'Elíptica' else 'Ancho X (vacío = auto):')
        self._ap_extra_widgets['height'][0].configure(
            text='Eje Y (vacío = auto):' if ap == 'Elíptica' else 'Alto Y (vacío = auto):')
        self._ap_extra_widgets['radius'][0].configure(
            text='Circunradio (vacío = auto):' if ap == 'Hexagonal' else
                 'Radio exterior (vacío = auto):' if ap == 'Anular' else
                 'Radio (vacío = auto):')

        # Ocultar todos
        for lbl, ent, _ in self._ap_extra_widgets.values():
            lbl.grid_forget(); ent.grid_forget()

        # Mostrar los relevantes
        for col, key in enumerate(visible):
            lbl, ent, _ = self._ap_extra_widgets[key]
            lbl.grid(row=0, column=col * 2,     padx=(0, 2))
            ent.grid(row=0, column=col * 2 + 1, padx=(0, 12))

        # Base polinómica según la apertura
        if not hasattr(self, 'lbl_basis'):
            return
        circ = ap in ('Circular', 'Elíptica')
        for rb in (self.rb_fringe, self.rb_noll, self.rb_pico, self.rb_rms):
            rb.state(['!disabled'] if circ else ['disabled'])
        if not circ:
            self.norm_var.set('rms')
        self.lbl_basis.configure(text=BASIS_TEXT.get(ap, ''))

    # ── Acciones ────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de datos FEM",
            filetypes=[("Archivos de texto", "*.txt *.dat *.csv"), ("Todos", "*.*")])
        if path:
            self.fname_var.set(path)
            self._cases_for_file(path)

    def _cases_for_file(self, path):
        """
        Detecta si el fichero contiene varios casos de carga apilados y
        rellena el desplegable.  Devuelve False si el fichero no se puede leer.
        """
        if getattr(self, '_cases_path', None) == path:
            return True
        try:
            import fem_mirror_analysis as m
            cases = m.list_load_cases(path)
        except Exception as e:
            messagebox.showerror("Error de lectura", f"No se pudo leer el fichero:\n{e}")
            return False
        self._cases_path = path
        self._cases = cases or []
        hu = m.header_units(path)
        if hu and hu != self.units_var.get():
            self.units_var.set(hu)
            self._log(f"Unidades del fichero leídas de la cabecera: {hu}\n")
        if self._cases:
            vals = [f"{c:g}" for c in self._cases]
            self.cb_case.configure(values=vals, state='readonly')
            self.case_var.set(vals[0])
            self.lbl_case.configure(
                text=f"⚠ el fichero contiene {len(vals)} casos apilados: elige uno",
                foreground='#b36b00')
        else:
            self.cb_case.configure(values=[], state='disabled')
            self.case_var.set('')
            self.lbl_case.configure(text="(fichero con un único caso)", foreground='gray')
        return True

    def _log(self, text):
        """Escribe en el widget de log (seguro desde cualquier hilo)."""
        def _write():
            self.log_text.configure(state='normal')
            self.log_text.insert(tk.END, text)
            self.log_text.see(tk.END)
            self.log_text.configure(state='disabled')
        self.after(0, _write)

    def _clear_log(self):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', tk.END)
        self.log_text.configure(state='disabled')

    def _embed_figure(self, fig):
        """Embebe una figura matplotlib en el panel inferior del GUI."""
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

        # Eliminar figura anterior si existe
        if self._canvas is not None:
            try:
                self._canvas.get_tk_widget().destroy()
            except Exception:
                pass
            self._canvas = None

        # Eliminar todos los widgets del frame (incluyendo toolbar anterior)
        for widget in self.frm_fig.winfo_children():
            widget.destroy()

        # Crear canvas embebido
        canvas = FigureCanvasTkAgg(fig, master=self.frm_fig)
        canvas.draw()

        # Barra de navegación (zoom, pan, guardar…)
        # pack_toolbar=False requiere matplotlib >= 3.3; fallback para versiones antiguas
        try:
            toolbar = NavigationToolbar2Tk(canvas, self.frm_fig, pack_toolbar=False)
            toolbar.update()
            toolbar.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 2))
        except TypeError:
            # matplotlib antiguo: la toolbar usa pack internamente, la metemos en un frame
            frm_tb = tk.Frame(self.frm_fig)
            frm_tb.grid(row=1, column=0, sticky='ew')
            toolbar = NavigationToolbar2Tk(canvas, frm_tb)
            toolbar.update()

        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        self._canvas = canvas

    def _run(self):
        params = self._collect_params()
        if params is None:
            return
        self._start(params)

    def _collect_params(self, require_file=True):
        """Lee y valida los parámetros de la GUI.  None si hay un error."""
        fname = self.fname_var.get().strip()
        if require_file:
            if not fname:
                messagebox.showwarning("Sin archivo", "Selecciona primero un archivo de datos.")
                return None
            if not os.path.isfile(fname):
                messagebox.showerror("Archivo no encontrado", f"No existe el archivo:\n{fname}")
                return None

        nterms = self.nterms_var.get()
        if nterms < 0:
            messagebox.showwarning("Parámetro inválido", "El número de términos no puede ser negativo.")
            return

        # Recoger parámetros de apertura opcionales
        def _val(key):
            _, _, var = self._ap_extra_widgets[key]
            s = var.get().strip()
            return s if s else None

        aperture = self.ap_var.get()
        if aperture not in APERTURES_ENABLED:
            messagebox.showinfo("No disponible",
                                f"La apertura '{aperture}' todavía no está implementada.")
            return
        conv = self.conv_var.get()
        if aperture == 'Circular' and conv == 'fringe' and nterms > 37:
            messagebox.showwarning("Parámetro inválido",
                                   "El conjunto Fringe estándar tiene 37 términos como máximo.")
            return
        if aperture != 'Circular' and nterms > 66:
            messagebox.showwarning("Parámetro inválido",
                                   "Máximo 66 términos (orden radial 10) en esta base.")
            return

        # Validar números
        for key in ('radius', 'rin', 'width', 'height', 'cx', 'cy'):
            s = _val(key)
            if s is not None:
                try:
                    float(s.replace(',', '.'))
                except ValueError:
                    messagebox.showwarning("Parámetro inválido",
                                           f"Valor no numérico en '{key}': {s}")
                    return
        if (_val('cx') is None) != (_val('cy') is None):
            messagebox.showwarning("Centro incompleto",
                                   "Indica Centro X y Centro Y, o deja ambos vacíos.")
            return
        _num = lambda k: _val(k).replace(',', '.') if _val(k) else None

        # Óptica e ISO
        try:
            lam = float(self.lambda_var.get().replace(',', '.'))
            inc = float(self.incid_var.get().replace(',', '.'))
            if lam <= 0 or not 0 <= inc < 90:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Parámetro inválido",
                                   "λ debe ser > 0 nm y la incidencia estar en [0, 90)°.")
            return
        try:
            iso_axis = float(self.iso_axis_var.get().replace(',', '.') or 0)
        except ValueError:
            messagebox.showwarning("Parámetro inválido", "El giro de los ejes debe ser un número [°].")
            return
        spec = self.iso_spec_var.get().strip()
        if spec and self.optics_var.get():
            import fem_mirror_analysis as _fm
            try:
                _fm.parse_iso10110(spec)
            except ValueError as e:
                messagebox.showwarning("Tolerancia ISO 10110-5", f"No se entiende la indicación:\n{e}")
                return

        # Caso de carga
        case = None
        if require_file and not self._cases_for_file(fname):
            return
        if require_file and self._cases:
            try:
                case = float(self.case_var.get())
            except ValueError:
                messagebox.showwarning("Caso de carga",
                                       "El fichero tiene varios casos: elige uno.")
                return

        params = {
            'fname':      fname,
            'case':       case,
            'rigid':      tuple(int(v.get()) for v in self.rigid_vars),
            'frame':      self.frame_var.get(),
            'quantity':   self.quantity_var.get(),
            'aperture':   aperture,
            'nterms':     nterms,
            'norm':       self.norm_var.get(),
            'convention': conv,
            'wls':        bool(self.wls_var.get()),
            'radius':     _num('radius'),
            'rin':        _num('rin'),
            'hexorient':  'x' if self._ap_extra_widgets['hexorient'][2].get() == '±X' else 'y',
            'width':      _num('width'),
            'height':     _num('height'),
            'cx':         _num('cx'),
            'cy':         _num('cy'),
            'units':      self.units_var.get(),
            'wavelength': lam,
            'incidence':  inc,
            'optics':     bool(self.optics_var.get()),
            'iso_spec':   spec,
            'iso_form':   self.iso_form_var.get(),
            'iso_axis':   iso_axis,
        }
        return params

    def _start(self, params):
        self.btn_run.configure(state='disabled', text="Ejecutando…")
        self.btn_3d.configure(state='disabled')
        self.btn_report.configure(state='disabled')
        self.btn_export.configure(state='disabled')
        self._clear_log()
        self._result_store[0] = None   # borrar resultado anterior

        def _done():
            self.btn_run.configure(state='normal', text="▶  Ejecutar análisis")
            if self._result_store[0] is not None:
                self.btn_3d.configure(state='normal')
                if self._result_store[0].get('report') is not None:
                    self.btn_report.configure(state='normal')
                if self._result_store[0].get('export') is not None:
                    self.btn_export.configure(state='normal')

        def _thread():
            run_analysis(params, self._log, self.after,
                         embed_fig=self._embed_figure,
                         result_store=self._result_store)
            self.after(0, _done)

        threading.Thread(target=_thread, daemon=True).start()

    def _open_export(self):
        data = self._result_store[0]
        if data is None or data.get('export') is None:
            messagebox.showinfo("Sin datos", "Ejecuta primero el análisis.")
            return
        if getattr(self, '_export_win', None) is not None and self._export_win.winfo_exists():
            self._export_win.destroy()
        self._export_win = ExportDialog(self, data['export'])

    def _open_combine(self):
        if getattr(self, '_combine_win', None) is not None and self._combine_win.winfo_exists():
            self._combine_win.lift()
            return
        self._combine_win = CombineDialog(self)

    def _make_report(self):
        """Genera el informe Word del último análisis."""
        import base64
        data = self._result_store[0]
        if data is None or data.get('report') is None:
            messagebox.showinfo("Sin datos", "Ejecuta primero el análisis.")
            return
        try:
            import docx  # noqa: F401
        except ImportError:
            messagebox.showerror(
                "Falta python-docx",
                "Para generar informes hace falta la librería python-docx.\n\n"
                "Ejecuta instalar_dependencias.bat o, en una consola:\n"
                "    python -m pip install python-docx")
            return
        import report_fem_mirror as rp

        lang = 'en' if self.report_lang_var.get() == 'English' else 'es'
        units = (data['report'].get('optics') or {}).get('units') or self.units_var.get() or 'mm'
        rep = data['report']
        base = os.path.splitext(os.path.basename(rep.get('fname') or 'analisis'))[0]
        if rep.get('case') is not None:
            base += f"_caso{rep['case']:g}"
        default = f"{'Report' if lang == 'en' else 'Informe'}_{base}.docx"
        path = filedialog.asksaveasfilename(
            title="Guardar informe Word", defaultextension=".docx",
            initialdir=os.path.dirname(rep.get('fname') or '') or None,
            initialfile=default, filetypes=[("Documento Word", "*.docx")])
        if not path:
            return

        self.configure(cursor='watch')
        self.btn_report.configure(state='disabled', text="Generando…")
        self.update_idletasks()
        try:
            rp.generate_report(rep, path, lang=lang, units=units,
                               logo_png=base64.b64decode(_LOGO_B64))
        except PermissionError:
            messagebox.showerror("No se pudo guardar",
                                 f"No se puede escribir en:\n{path}\n\n"
                                 "¿Está abierto en Word? Ciérralo e inténtalo de nuevo.")
            return
        except Exception:
            messagebox.showerror("Error al generar el informe", traceback.format_exc())
            return
        finally:
            self.configure(cursor='')
            self.btn_report.configure(state='normal', text="📄  Generar informe")

        self._log(f"\n📄 Informe guardado en: {path}\n")
        if messagebox.askyesno("Informe generado",
                               f"Informe guardado en:\n{path}\n\n¿Abrirlo ahora?"):
            try:
                if sys.platform.startswith('win'):
                    os.startfile(path)                     # noqa: S606
                elif sys.platform == 'darwin':
                    import subprocess; subprocess.Popen(['open', path])
                else:
                    import subprocess; subprocess.Popen(['xdg-open', path])
            except Exception as e:
                messagebox.showwarning("No se pudo abrir", str(e))

    def _show_3d(self):
        """Abre una ventana Toplevel con la superficie deformada en 3D."""
        data = self._result_store[0]
        if data is None:
            messagebox.showinfo("Sin datos", "Ejecuta primero el análisis.")
            return

        scale_str = self.scale3d_var.get().strip().replace(',', '.')
        try:
            scale = float(scale_str)
            if scale == 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Escala inválida",
                                   "Introduce un número distinto de cero (p.ej. 10E6).")
            return

        import matplotlib
        matplotlib.use('TkAgg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d import Axes3D          # noqa: F401
        import matplotlib.tri as mtri
        import numpy as _np
        from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                                        NavigationToolbar2Tk)

        x       = data['x']
        y       = data['y']
        z_res   = data['z_res']
        valid   = data['valid']
        rms_res = data['rms_res']
        pv_res  = data['pv_res']
        nterms  = data['nterms']
        aperture= data['aperture']

        xv = x[valid]
        yv = y[valid]
        zv = z_res[valid] * scale   # amplificado para que sea visible

        # ── Figura 3D ─────────────────────────────────────────────────
        fig = plt.figure(figsize=(9, 7))
        ax  = fig.add_subplot(111, projection='3d')

        import fem_mirror_analysis as _fm
        tri  = _fm.plot_triangulation(xv, yv)
        import fem_mirror_analysis as _fma
        surf = ax.plot_trisurf(tri, zv, cmap=_fma.surface_cmap(),
                               linewidth=0, antialiased=True, alpha=0.92)

        cb = fig.colorbar(surf, ax=ax, shrink=0.55, pad=0.1)
        cb.set_label(f'Despl. normal × {scale:g}', fontsize=8)
        # Reescalar etiquetas del colorbar a valores reales
        import matplotlib.ticker as mticker
        cb.formatter = mticker.FuncFormatter(lambda v, _: f'{v/scale:.2e}')
        cb.update_ticks()

        title2 = (f"Residuo {data.get('fam', 'Zernike')} ({nterms} términos) — apertura {aperture}"
                  if nterms > 0 else f'Apertura {aperture}')
        ax.set_title(
            f'Vista 3D — {title2}\n'
            f'RMS = {rms_res:.3e}   PV = {pv_res:.3e}   (escala Z × {scale:g})',
            fontsize=9)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel(f'Despl. × {scale:g}')

        # Relación de aspecto: X e Y a escala real; Z amplificado
        x_range = xv.max() - xv.min()
        y_range = yv.max() - yv.min()
        z_range = zv.max() - zv.min() if (zv.max() - zv.min()) > 0 else 1.0
        ax.set_box_aspect([x_range, y_range, z_range * 0.3])  # Z más comprimido visualmente

        plt.tight_layout()

        # ── Embeber en un Toplevel Tk para no bloquear la GUI ─────────
        top = tk.Toplevel(self)
        top.title(f"Vista 3D — escala Z × {scale:g}")
        top.geometry("920x720")
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)

        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()

        try:
            toolbar = NavigationToolbar2Tk(canvas, top, pack_toolbar=False)
            toolbar.update()
            toolbar.grid(row=1, column=0, sticky='ew', padx=4, pady=(0, 2))
        except TypeError:
            frm_tb = tk.Frame(top)
            frm_tb.grid(row=1, column=0, sticky='ew')
            toolbar = NavigationToolbar2Tk(canvas, frm_tb)
            toolbar.update()

        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew', padx=4, pady=4)

        # Nota: rotar arrastrando con el botón izquierdo del ratón
        ttk.Label(top, text="Arrastra para rotar · Rueda para zoom · Botón derecho para desplazar",
                  foreground='gray').grid(row=2, column=0, pady=(0, 4))


# ═══════════════════════════════════════════════════════════════════
#  COMBINACIÓN DE CASOS DE CARGA
# ═══════════════════════════════════════════════════════════════════

class ExportDialog(tk.Toplevel):
    """
    Exporta la superficie del último análisis a Zemax OpticStudio (Grid Sag
    .DAT) y QUADOA (CSV x, y, z), y los coeficientes de Zernike (Fringe,
    Standard/Noll y ANSI) en unidades de lente.
    """

    def __init__(self, app, exp):
        super().__init__(app)
        self.app, self.exp = app, exp
        self.title("Exportar a Zemax / QUADOA")
        self.resizable(False, False)
        pad = dict(padx=8, pady=4)

        frm_s = ttk.LabelFrame(self, text="Superficie a exportar")
        frm_s.grid(row=0, column=0, sticky='ew', **pad)
        self.surf_var = tk.StringVar(value='sin_rigido')
        ttk.Radiobutton(frm_s, text="Sin sólido rígido (recomendado)", variable=self.surf_var,
                        value='sin_rigido').grid(row=0, column=0, sticky='w', padx=6, pady=2)
        rb = ttk.Radiobutton(frm_s, text="Residuo tras el ajuste polinómico",
                             variable=self.surf_var, value='residuo')
        rb.grid(row=1, column=0, sticky='w', padx=6, pady=2)
        if exp.get('res') is None:
            rb.configure(state='disabled')
            ttk.Label(frm_s, text="(sin ajuste: términos = 0)", foreground='gray').grid(
                row=1, column=1, sticky='w')

        frm_o = ttk.LabelFrame(self, text="Opciones")
        frm_o.grid(row=1, column=0, sticky='ew', **pad)
        ttk.Label(frm_o, text="Unidades de lente:").grid(row=0, column=0, sticky='w', padx=6, pady=3)
        self.lu_var = tk.StringVar(value='mm')
        ttk.Combobox(frm_o, textvariable=self.lu_var, width=6, state='readonly',
                     values=['mm', 'm', 'cm', 'in']).grid(row=0, column=1, sticky='w')
        ttk.Label(frm_o, text=f"(fichero FEM en {exp['units']})", foreground='gray').grid(
            row=0, column=2, sticky='w', padx=6)
        ttk.Label(frm_o, text="Puntos de rejilla por lado:").grid(row=1, column=0, sticky='w',
                                                                   padx=6, pady=3)
        self.n_var = tk.StringVar(value='101')
        ttk.Entry(frm_o, textvariable=self.n_var, width=7).grid(row=1, column=1, sticky='w')
        ttk.Label(frm_o, text="(impar, ≥ 5)", foreground='gray').grid(row=1, column=2, sticky='w',
                                                                      padx=6)
        ttk.Label(frm_o, text="Interpolación:").grid(row=2, column=0, sticky='w', padx=6, pady=3)
        self.interp_var = tk.StringVar(value='lineal')
        ttk.Combobox(frm_o, textvariable=self.interp_var, width=8, state='readonly',
                     values=['lineal', 'cúbica']).grid(row=2, column=1, sticky='w')
        ttk.Label(frm_o, text="Orden radial máx. Zernike\nStandard / ANSI:").grid(
            row=3, column=0, sticky='w', padx=6, pady=3)
        self.nmax_var = tk.StringVar(value='10')
        ttk.Entry(frm_o, textvariable=self.nmax_var, width=7).grid(row=3, column=1, sticky='w')
        ttk.Label(frm_o, text="(Fringe: siempre Z1–Z37)", foreground='gray').grid(
            row=3, column=2, sticky='w', padx=6)

        info = ("Se generan: rejilla Zemax Grid Sag (.dat), nube x,y,z para QUADOA (.csv),\n"
                "coeficientes Zernike Fringe, Standard/Noll y ANSI (.txt) y un LEEME con\n"
                "los convenios y cómo importarlos.")
        ttk.Label(self, text=info, foreground='gray', justify='left').grid(
            row=2, column=0, sticky='w', padx=10, pady=(2, 4))
        if exp.get('quantity') != 'sag':
            ttk.Label(self, text="⚠ Magnitud «normal u·n»: Zemax y QUADOA suman la deformación a la\n"
                                 "sagita (eje z); en superficies curvas usa «cambio de sag».",
                      foreground='#b06000', justify='left').grid(row=3, column=0, sticky='w',
                                                                 padx=10, pady=(0, 4))

        frm_b = ttk.Frame(self)
        frm_b.grid(row=4, column=0, pady=8)
        ttk.Button(frm_b, text="💾  Exportar…", command=self._export).grid(row=0, column=0, padx=4)
        ttk.Button(frm_b, text="Cerrar", command=self.destroy).grid(row=0, column=1, padx=4)

    def _export(self):
        import fem_mirror_analysis as m
        exp = self.exp
        try:
            n = int(self.n_var.get())
            nmax = int(self.nmax_var.get())
            if n < 5 or not 1 <= nmax <= 20:
                raise ValueError
        except ValueError:
            messagebox.showerror("Valor no válido",
                                 "Puntos de rejilla: entero ≥ 5.\nOrden radial: entero 1–20.",
                                 parent=self)
            return
        surf = self.surf_var.get()
        values = exp['res'] if (surf == 'residuo' and exp.get('res') is not None) else exp['un']
        fname = exp.get('fname') or 'superficie'
        base = os.path.splitext(os.path.basename(fname))[0]
        if exp.get('case') is not None:
            base += f"_caso{exp['case']:g}"
        base += '_residuo' if surf == 'residuo' else ''
        path = filedialog.asksaveasfilename(
            parent=self, title="Ruta base de los ficheros exportados",
            initialdir=os.path.dirname(fname) or None, initialfile=base,
            filetypes=[("Todos los ficheros", "*.*")])
        if not path:
            return
        path = os.path.splitext(path)[0] if os.path.splitext(path)[1].lower() in (
            '.dat', '.csv', '.txt') else path
        self.configure(cursor='watch')
        self.update_idletasks()
        try:
            out = m.export_optical(
                exp['xy'], values, exp['w'], exp['geom'], path, units=exp['units'],
                lens_units=self.lu_var.get(), n_grid=n,
                interp='cubic' if self.interp_var.get() == 'cúbica' else 'linear',
                n_max=nmax, surface=surf, quantity=exp['quantity'],
                source=os.path.basename(fname) + (f" · caso {exp['case']:g}"
                                                  if exp.get('case') is not None else ''),
                frame=exp['frame'])
        except Exception:
            messagebox.showerror("Error al exportar", traceback.format_exc(), parent=self)
            return
        finally:
            self.configure(cursor='')
        log = self.app._log
        log(f"\n🔭 Exportación a Zemax / QUADOA ({m.EXPORT_SURFACES[surf]}):\n")
        for ln in out['lines']:
            log(f"  {ln}\n")
        for p in out['files']:
            log(f"  → {p}\n")
        messagebox.showinfo("Exportación completada",
                            f"{len(out['files'])} ficheros guardados en:\n{os.path.dirname(path)}\n\n"
                            "Lee el fichero *_LEEME_exportacion.txt antes de importarlos.",
                            parent=self)


class CombineDialog(tk.Toplevel):
    """
    Combina casos FEM calculados con la misma malla:
      · Gravedad a distintos ángulos:  u(θ) = cosθ·A + sinθ·B (+ C)
      · Combinación lineal:            Σ cₖ·uₖ
    Genera un TXT combinado y lo analiza con los ajustes de la ventana principal.
    """

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Combinar casos de carga")
        self.resizable(True, True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.items = []                     # (ruta, caso, valor)
        self._new_cases = []
        pad = dict(padx=8, pady=4)

        frm_mode = ttk.LabelFrame(self, text="Tipo de combinación")
        frm_mode.grid(row=0, column=0, sticky='ew', **pad)
        self.mode_var = tk.StringVar(value='gravity')
        ttk.Radiobutton(frm_mode, text="Gravedad a distintos ángulos  u(θ) = cosθ·A + sinθ·B (+C)",
                        variable=self.mode_var, value='gravity',
                        command=self._update_mode).grid(row=0, column=0, sticky='w', padx=6, pady=2)
        ttk.Radiobutton(frm_mode, text="Combinación lineal  Σ cₖ·uₖ",
                        variable=self.mode_var, value='linear',
                        command=self._update_mode).grid(row=1, column=0, sticky='w', padx=6, pady=2)

        frm_list = ttk.LabelFrame(self, text="Casos (misma malla)")
        frm_list.grid(row=1, column=0, sticky='nsew', **pad)
        frm_list.columnconfigure(0, weight=1)
        frm_list.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(frm_list, columns=('file', 'case', 'val'), show='headings',
                                 height=5)
        self.tree.heading('file', text='Fichero')
        self.tree.heading('case', text='Caso')
        self.tree.heading('val', text='Ángulo [°]')
        self.tree.column('file', width=380)
        self.tree.column('case', width=60, anchor='center')
        self.tree.column('val', width=90, anchor='center')
        self.tree.grid(row=0, column=0, columnspan=6, sticky='nsew', padx=4, pady=4)

        self.new_file = tk.StringVar()
        ttk.Entry(frm_list, textvariable=self.new_file, width=46).grid(
            row=1, column=0, sticky='ew', padx=4)
        ttk.Button(frm_list, text="…", width=3, command=self._pick).grid(row=1, column=1)
        ttk.Label(frm_list, text="Caso:").grid(row=1, column=2, padx=(8, 2))
        self.new_case = tk.StringVar()
        self.cb_new_case = ttk.Combobox(frm_list, textvariable=self.new_case, width=6,
                                        state='disabled')
        self.cb_new_case.grid(row=1, column=3)
        self.lbl_val = ttk.Label(frm_list, text="Ángulo [°]:")
        self.lbl_val.grid(row=1, column=4, padx=(8, 2))
        self.new_val = tk.StringVar()
        ttk.Entry(frm_list, textvariable=self.new_val, width=8).grid(row=1, column=5, padx=(0, 4))
        frm_lb = ttk.Frame(frm_list)
        frm_lb.grid(row=2, column=0, columnspan=6, sticky='e', pady=4)
        ttk.Button(frm_lb, text="Añadir", command=self._add).grid(row=0, column=0, padx=4)
        ttk.Button(frm_lb, text="Quitar seleccionado", command=self._remove).grid(row=0, column=1)

        self.frm_grav = ttk.LabelFrame(self, text="Gravedad")
        self.frm_grav.grid(row=2, column=0, sticky='ew', **pad)
        self.const_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.frm_grav, text="Término constante C (precargas, montaje; ≥ 3 casos)",
                        variable=self.const_var).grid(row=0, column=0, columnspan=6,
                                                      sticky='w', padx=6, pady=2)
        ttk.Label(self.frm_grav, text="Ángulo a analizar [°]:").grid(row=1, column=0, padx=(6, 2))
        self.target_var = tk.StringVar(value='60')
        ttk.Entry(self.frm_grav, textvariable=self.target_var, width=7).grid(row=1, column=1)
        ttk.Label(self.frm_grav, text="Referencia [°] (vacío = absoluto):").grid(
            row=1, column=2, padx=(12, 2))
        self.ref_var = tk.StringVar(value='')
        ttk.Entry(self.frm_grav, textvariable=self.ref_var, width=7).grid(row=1, column=3)
        ttk.Label(self.frm_grav, text="Barrido de:").grid(row=2, column=0, padx=(6, 2), pady=4)
        self.sw0, self.sw1, self.swd = (tk.StringVar(value=v) for v in ('0', '90', '5'))
        ttk.Entry(self.frm_grav, textvariable=self.sw0, width=7).grid(row=2, column=1)
        ttk.Label(self.frm_grav, text="a").grid(row=2, column=2, sticky='e', padx=2)
        ttk.Entry(self.frm_grav, textvariable=self.sw1, width=7).grid(row=2, column=3, sticky='w')
        ttk.Label(self.frm_grav, text="paso").grid(row=2, column=4, padx=2)
        ttk.Entry(self.frm_grav, textvariable=self.swd, width=6).grid(row=2, column=5)
        ttk.Button(self.frm_grav, text="📈  Barrido", command=self._sweep).grid(
            row=2, column=6, padx=8)
        ttk.Label(self.frm_grav, foreground='gray', wraplength=620, justify='left',
                  text=("El convenio de ángulos es libre (p. ej. elevación) pero debe ser el mismo "
                        "en todos los casos y la gravedad debe girar en un plano. Con más casos "
                        "que incógnitas se comprueba la linealidad.")).grid(
            row=3, column=0, columnspan=7, sticky='w', padx=6, pady=(0, 4))

        frm_b = ttk.Frame(self)
        frm_b.grid(row=3, column=0, sticky='ew', **pad)
        frm_b.columnconfigure(0, weight=1)
        self.lbl_status = ttk.Label(frm_b, text="", foreground='#1f5fa8', wraplength=520,
                                    justify='left')
        self.lbl_status.grid(row=0, column=0, sticky='w')
        ttk.Button(frm_b, text="▶  Generar y analizar", command=self._generate).grid(
            row=0, column=1, padx=4)
        ttk.Button(frm_b, text="Cerrar", command=self.destroy).grid(row=0, column=2)
        self._update_mode()

    # ── utilidades ──────────────────────────────────────────────────
    def _update_mode(self):
        grav = self.mode_var.get() == 'gravity'
        txt = 'Ángulo [°]' if grav else 'Coeficiente'
        self.tree.heading('val', text=txt)
        self.lbl_val.configure(text=txt + ':')
        if grav:
            self.frm_grav.grid()
        else:
            self.frm_grav.grid_remove()

    def _pick(self):
        path = filedialog.askopenfilename(
            parent=self, title="Seleccionar caso FEM",
            filetypes=[("Archivos de texto", "*.txt *.dat *.csv"), ("Todos", "*.*")])
        if not path:
            return
        self.new_file.set(path)
        try:
            import fem_mirror_analysis as m
            cases = m.list_load_cases(path) or []
        except Exception as e:
            messagebox.showerror("Error de lectura", str(e), parent=self)
            return
        if cases:
            vals = [f"{c:g}" for c in cases]
            self.cb_new_case.configure(values=vals, state='readonly')
            self.new_case.set(vals[0])
        else:
            self.cb_new_case.configure(values=[], state='disabled')
            self.new_case.set('')

    def _add(self):
        path = self.new_file.get().strip()
        if not os.path.isfile(path):
            messagebox.showwarning("Fichero", "Elige un fichero existente.", parent=self)
            return
        try:
            val = float(self.new_val.get().replace(',', '.'))
        except ValueError:
            messagebox.showwarning("Valor", "Introduce un número.", parent=self)
            return
        case = float(self.new_case.get()) if self.new_case.get() else None
        self.items.append((path, case, val))
        self.tree.insert('', 'end', values=(os.path.basename(path),
                                            '' if case is None else f"{case:g}", f"{val:g}"))
        self.new_val.set('')

    def _remove(self):
        sel = self.tree.selection()
        if not sel:
            return
        idx = self.tree.index(sel[0])
        self.tree.delete(sel[0])
        del self.items[idx]

    def _floats(self, *vars_, allow_empty=()):
        out = []
        for k, v in enumerate(vars_):
            t = v.get().strip().replace(',', '.')
            if not t and k in allow_empty:
                out.append(None)
                continue
            out.append(float(t))
        return out

    def _load(self):
        """Lee los casos alineados con la malla del primero."""
        import fem_mirror_analysis as m
        if len(self.items) < 2 and self.mode_var.get() == 'gravity':
            raise ValueError("Añade al menos 2 casos (3 con término constante).")
        if not self.items:
            raise ValueError("Añade al menos un caso.")
        coor, disps = None, []
        for path, case, _ in self.items:
            c, d = m.load_case_aligned(path, case, coor)
            coor = c if coor is None else coor
            disps.append(d)
        return coor, disps

    def _gravity_basis(self, coor, disps):
        import fem_mirror_analysis as m
        angles = [v for _, _, v in self.items]
        gb = m.fit_gravity_basis(disps, angles, constant=self.const_var.get())
        if gb['dof'] > 0:
            mis = ", ".join(f"{a:g}°: {e*100:.2f}%" for a, e in zip(angles, gb['misfit']))
            worst = max(gb['misfit'])
            msg = f"Linealidad (desajuste por caso): {mis}"
            if worst > 0.02:
                msg += "  ⚠ > 2 %: revisa que los casos sean sólo gravedad o añade C."
        else:
            msg = "Sin casos redundantes: la linealidad no se puede comprobar."
        return gb, msg

    def _desc(self):
        mode = self.mode_var.get()
        parts = [f"{os.path.basename(p)}{'' if c is None else f'::{c:g}'}"
                 for p, c, _ in self.items]
        if mode == 'gravity':
            return ("Gravedad: " + ", ".join(f"{n} @ {v:g}°" for n, (_, _, v)
                                            in zip(parts, self.items))
                    + (" + C" if self.const_var.get() else ""))
        return "Combinación lineal: " + " + ".join(f"{v:g}·[{n}]" for n, (_, _, v)
                                                     in zip(parts, self.items))

    # ── acciones ────────────────────────────────────────────────────
    def _generate(self):
        import fem_mirror_analysis as m
        params = self.app._collect_params(require_file=False)
        if params is None:
            return
        try:
            coor, disps = self._load()
            desc = [self._desc()]
            if self.mode_var.get() == 'gravity':
                tgt, ref = self._floats(self.target_var, self.ref_var, allow_empty=(1,))
                gb, msg = self._gravity_basis(coor, disps)
                disp = m.gravity_combination(gb, tgt, ref)
                desc += [msg, f"Ángulo {tgt:g}°" + (f" respecto a {ref:g}°" if ref is not None else "")]
                tag = f"{tgt:g}deg" + (f"_ref{ref:g}" if ref is not None else "")
            else:
                disp = m.linear_combination(disps, [v for _, _, v in self.items])
                tag = "lineal"
        except ValueError as e:
            messagebox.showerror("Combinación de casos", str(e), parent=self)
            return
        self.lbl_status.configure(text="\n".join(desc[1:]) or desc[0])
        first = self.items[0][0]
        path = filedialog.asksaveasfilename(
            parent=self, title="Guardar caso combinado", defaultextension=".txt",
            initialdir=os.path.dirname(first),
            initialfile=f"COMBINADO_{tag}.txt".replace('-', 'm'),
            filetypes=[("Texto", "*.txt")])
        if not path:
            return
        try:
            m.save_fem_txt(path, coor, disp, "\n".join(desc), units=self.app.units_var.get())
        except OSError as e:
            messagebox.showerror("No se pudo guardar", str(e), parent=self)
            return
        self.app.fname_var.set(path)
        self.app._cases_path = None
        self.app._cases_for_file(path)
        params = self.app._collect_params()
        if params is None:
            return
        params['combo_desc'] = desc
        self.app._start(params)
        self.app._log("Caso combinado: " + " · ".join(desc) + f"\n  → {path}\n\n")

    def _sweep(self):
        import numpy as np
        import fem_mirror_analysis as m
        params = self.app._collect_params(require_file=False)
        if params is None:
            return
        try:
            a0, a1, da = self._floats(self.sw0, self.sw1, self.swd)
            ref, = self._floats(self.ref_var, allow_empty=(0,))
            if da <= 0 or a1 < a0:
                raise ValueError("Barrido: paso > 0 y fin ≥ inicio.")
            coor, disps = self._load()
            gb, msg = self._gravity_basis(coor, disps)
        except ValueError as e:
            messagebox.showerror("Barrido", str(e), parent=self)
            return
        self.lbl_status.configure(text=msg)
        if params['frame'] == 'bestfit':
            coor_r, _, info = m.to_local_frame(coor, np.zeros_like(coor))
            R = info['R']
            gb = {k: (v @ R.T if isinstance(v, np.ndarray) and v.ndim == 2 else v)
                  for k, v in gb.items()}
            coor = coor_r
        ap_key = APERTURE_KEYS[params['aperture']]
        basis = m.basis_key(ap_key, params['convention'])
        norm = 'rms' if basis in m.ORTHO_BASES else params['norm']
        f = lambda k: float(params[k]) if params.get(k) else None
        center = (float(params['cx']), float(params['cy'])) if params.get('cx') else None
        ap_kw = dict(radius=f('radius'), width=f('width'), height=f('height'), center=center,
                     inner_radius=f('rin'),
                     hex_rotation=0.0 if params.get('hexorient', 'x') == 'x' else 30.0)
        terms = m.default_terms(basis, params['nterms']) if params['nterms'] > 0 else None
        angles = list(np.arange(a0, a1 + 0.5 * da, da))
        self.configure(cursor='watch'); self.update_idletasks()
        try:
            rows = m.elevation_sweep(coor, gb, angles, ref, rigid=params['rigid'],
                                     quantity=params['quantity'], aperture=ap_key,
                                     aperture_kw=ap_kw, basis=basis, terms=terms,
                                     norm=norm, wls=params['wls'])
        except Exception:
            messagebox.showerror("Barrido", traceback.format_exc(), parent=self)
            return
        finally:
            self.configure(cursor='')
        self._plot_sweep(rows, params, ref, terms is not None, basis)

    def _plot_sweep(self, rows, params, ref, has_fit, basis):
        import fem_mirror_analysis as m
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
        try:
            k = m.unit_factor_nm(params['units'])
            ulab = 'nm'
        except KeyError:
            k, ulab = 1.0, params['units']
        ang = [r['angle'] for r in rows]
        fig = Figure(figsize=(9, 4.2), dpi=100)
        ax1, ax2 = fig.add_subplot(121), fig.add_subplot(122)
        ax1.plot(ang, [r['rms'] * k for r in rows], 'o-', label='Sin sólido rígido')
        ax2.plot(ang, [r['pv'] * k for r in rows], 'o-', label='Sin sólido rígido')
        if has_fit:
            lab = f"Residuo ({params['nterms']} términos)"
            ax1.plot(ang, [r['rms_res'] * k for r in rows], 's--', label=lab)
            ax2.plot(ang, [r['pv_res'] * k for r in rows], 's--', label=lab)
        for ax, t in ((ax1, 'RMS'), (ax2, 'PV')):
            ax.set_xlabel('Ángulo [°]')
            ax.set_ylabel(f'{t} [{ulab}]')
            ax.grid(alpha=0.3)
            ax.legend(fontsize=8)
        fig.suptitle("Barrido de ángulo" + (f" (respecto a {ref:g}°)" if ref is not None else ""),
                     fontsize=10)
        fig.tight_layout()
        top = tk.Toplevel(self)
        top.title("Barrido de ángulo")
        top.columnconfigure(0, weight=1); top.rowconfigure(0, weight=1)
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        try:
            tb = NavigationToolbar2Tk(canvas, top, pack_toolbar=False)
            tb.update(); tb.grid(row=1, column=0, sticky='ew')
        except TypeError:
            pass
        txt = scrolledtext.ScrolledText(top, height=8, font=('Consolas', 9))
        hdr = f"{'Ángulo':>8} {'RMS':>12} {'PV':>12}" + (f" {'RMS res.':>12} {'PV res.':>12}"
                                                          if has_fit else "")
        lines = [f"Valores en {ulab}", hdr]
        for r in rows:
            ln = f"{r['angle']:8.2f} {r['rms']*k:12.4f} {r['pv']*k:12.4f}"
            if has_fit:
                ln += f" {r['rms_res']*k:12.4f} {r['pv_res']*k:12.4f}"
            lines.append(ln)
        txt.insert('1.0', "\n".join(lines))
        txt.grid(row=2, column=0, sticky='ew', padx=4, pady=4)


# ═══════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ═══════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app = App()
    app.mainloop()
