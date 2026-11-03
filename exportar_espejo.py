# -*- coding: utf-8 -*-
"""
exportar_espejo.py — Botón de usuario para ANSYS Mechanical (IronPython 2.7)

Exporta las coordenadas y los desplazamientos de los nodos de la(s) cara(s)
seleccionada(s) a un TXT que lee directamente mirror-surface-deformation.

Uso
---
1. Resuelve el análisis estructural.
2. Selecciona la(s) cara(s) del espejo en la vista gráfica (o selecciona en
   el árbol una Named Selection de caras o de nodos).
3. Pulsa el botón (Automation → User Buttons) o ejecuta este script desde
   Automation → Scripting.
4. Elige dónde guardar el TXT.

Formato de salida (comentarios con '#', ignorados por numpy.loadtxt):
    # unidades: mm            ← el programa las lee y las ajusta solo
    # casos: 1 (t = 1), 2 (t = 2) ...
    un caso      : nodo  X  Y  Z  UX  UY  UZ
    varios casos : caso  X  Y  Z  UX  UY  UZ    (bloques apilados, mismo orden de nodos)

Coordenadas sin deformar y desplazamientos en el sistema GLOBAL, leídos del
fichero de resultados (.rst) con DPF, en las unidades del solver; si son
cm, µm, in o ft se convierten a mm.

Escrito con la API pública de scripting de Mechanical (ExtAPI y DPF en
Mechanical) para 2022 R2 y posteriores.  ⚠ Pendiente de probar en ANSYS:
si algo falla, el mensaje de error indica la línea.
"""

import io
import os
import clr

import mech_dpf
import Ans.DataProcessing as dpf

TITULO = "Exportar espejo (mirror-surface-deformation)"
A_MM = {'m': 1000.0, 'cm': 10.0, 'mm': 1.0, 'um': 1e-3, 'µm': 1e-3,
        'micron': 1e-3, 'in': 25.4, 'ft': 304.8}


def _aviso(texto, error=False):
    """Mensaje al usuario (ventana si está disponible; si no, consola)."""
    try:
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
        icono = MessageBoxIcon.Error if error else MessageBoxIcon.Information
        MessageBox.Show(texto, TITULO, MessageBoxButtons.OK, icono)
    except Exception:
        print(texto)


def _pedir_fichero(carpeta, nombre):
    """Diálogo «Guardar como».  Devuelve la ruta o None si se cancela."""
    try:
        clr.AddReference("System.Windows.Forms")
        from System.Windows.Forms import SaveFileDialog, DialogResult
        dlg = SaveFileDialog()
        dlg.Title = TITULO
        dlg.Filter = "Texto (*.txt)|*.txt|Todos los ficheros (*.*)|*.*"
        dlg.InitialDirectory = carpeta
        dlg.FileName = nombre
        if dlg.ShowDialog() == DialogResult.OK:
            return dlg.FileName
        return None
    except Exception:
        # Sin diálogo: se guarda en la carpeta de trabajo del análisis
        return os.path.join(carpeta, nombre)


def _analisis_activo():
    """Análisis resuelto que contiene el objeto activo del árbol (o el único resuelto)."""
    resueltos = []
    for a in ExtAPI.DataModel.Project.Model.Analyses:
        rst = a.ResultFileName
        if rst and os.path.exists(rst):
            resueltos.append(a)
    if not resueltos:
        return None
    if len(resueltos) == 1:
        return resueltos[0]
    ids = set()
    obj = ExtAPI.DataModel.Tree.FirstActiveObject
    while obj is not None:
        try:
            ids.add(obj.ObjectId)
            obj = obj.Parent
        except Exception:
            break
    for a in resueltos:
        if a.ObjectId in ids:
            return a
    return resueltos[0]


def _nodos_seleccionados(mesh):
    """Ids de nodos de la selección actual o de la Named Selection activa."""
    sel = ExtAPI.SelectionManager.CurrentSelection
    origen = "selección actual"
    if sel is None or sel.Ids is None or len(sel.Ids) == 0:
        obj = ExtAPI.DataModel.Tree.FirstActiveObject
        sel = getattr(obj, 'Location', None)
        origen = "Named Selection «%s»" % getattr(obj, 'Name', '?')
    if sel is None or sel.Ids is None or len(sel.Ids) == 0:
        return [], origen
    ids = set()
    if sel.SelectionType == SelectionTypeEnum.GeometryEntities:
        for gid in sel.Ids:
            ids.update(mesh.MeshRegionById(gid).NodeIds)
    elif sel.SelectionType == SelectionTypeEnum.MeshNodes:
        ids.update(sel.Ids)
    else:
        return [], origen
    return sorted(ids), origen


def exportar():
    # 1. Análisis y nodos
    analisis = _analisis_activo()
    if analisis is None:
        _aviso("No hay ningún análisis resuelto (falta el fichero de resultados).", True)
        return
    mesh = ExtAPI.DataModel.MeshDataByName("Global")
    nodos, origen = _nodos_seleccionados(mesh)
    if not nodos:
        _aviso("Selecciona la(s) cara(s) del espejo en la vista gráfica, o una "
               "Named Selection de caras o nodos en el árbol, y vuelve a pulsar.", True)
        return

    # 2. DPF: fichero de resultados, malla y casos
    mech_dpf.setExtAPI(ExtAPI)
    ds = dpf.DataSources(analisis.ResultFileName)
    modelo = dpf.Model(ds)
    malla = modelo.Mesh
    tf = dpf.operators.metadata.time_freq_provider()
    tf.inputs.data_sources.Connect(ds)
    soporte = tf.outputs.time_freq_support.GetData()
    nsets = soporte.NumberSets
    tiempos = list(soporte.TimeFreqs.Data)

    escop = dpf.Scoping()
    escop.Ids = nodos
    escop.Location = 'Nodal'

    # 3. Desplazamientos por caso (sistema global)
    campos = []
    unidad = None
    for k in range(1, nsets + 1):
        tscop = dpf.Scoping()
        tscop.Ids = [k]
        op = dpf.operators.result.displacement()
        op.inputs.data_sources.Connect(ds)
        op.inputs.mesh_scoping.Connect(escop)
        op.inputs.time_scoping.Connect(tscop)
        try:
            op.inputs.bool_rotate_to_global.Connect(True)
        except Exception:
            pass                       # por defecto DPF ya gira a global
        campo = op.outputs.fields_container.GetData()[0]
        if unidad is None:
            try:
                unidad = str(campo.Unit).strip()
            except Exception:
                unidad = ''
        campos.append(campo)

    ids = [int(i) for i in campos[0].ScopingIds]
    perdidos = len(nodos) - len(ids)

    u = (unidad or '').lower()
    if u in ('m', 'mm'):
        f, unidad_txt = 1.0, u
    elif u in A_MM:
        f, unidad_txt = A_MM[u], 'mm'
    else:
        f, unidad_txt = 1.0, (unidad or 'desconocida')

    # 4. Fichero
    carpeta = analisis.WorkingDir or os.path.dirname(analisis.ResultFileName)
    nombre = "espejo_%s.txt" % analisis.Name.replace(' ', '_')
    ruta = _pedir_fichero(carpeta, nombre)
    if not ruta:
        return

    coords = {}
    for nid in ids:
        n = malla.NodeById(nid)
        coords[nid] = (n.X * f, n.Y * f, n.Z * f)

    with io.open(ruta, 'w', encoding='utf-8') as fo:
        fo.write("# mirror-surface-deformation: exportado desde ANSYS Mechanical\n")
        fo.write("# analisis: %s\n" % analisis.Name)
        fo.write("# resultados: %s\n" % analisis.ResultFileName)
        fo.write("# origen: %s (%d nodos)\n" % (origen, len(ids)))
        fo.write("# unidades: %s\n" % unidad_txt)
        fo.write("# sistema: global; coordenadas sin deformar\n")
        fo.write("# casos: %s\n" % ", ".join(
            "%d (t = %g)" % (k + 1, tiempos[k]) for k in range(nsets)))
        if nsets == 1:
            fo.write("# columnas: nodo X Y Z UX UY UZ\n")
        else:
            fo.write("# columnas: caso X Y Z UX UY UZ\n")
        for k, campo in enumerate(campos):
            for nid in ids:
                d = campo.GetEntityDataById(nid)
                x, y, z = coords[nid]
                pref = nid if nsets == 1 else k + 1
                fo.write("%d %.10e %.10e %.10e %.10e %.10e %.10e\n"
                         % (pref, x, y, z, d[0] * f, d[1] * f, d[2] * f))
    try:
        modelo.ReleaseStreams()
    except Exception:
        pass

    msg = ("Exportados %d nodos y %d caso(s) de carga de «%s».\n"
           "Unidades: %s\n\n%s" % (len(ids), nsets, analisis.Name, unidad_txt, ruta))
    if perdidos > 0:
        msg += ("\n\n⚠ %d nodos de la selección no tienen resultados en el .rst "
                "(p. ej. nodos de contacto o de otros cuerpos)." % perdidos)
    if unidad_txt == 'desconocida':
        msg += "\n\n⚠ No se pudo leer la unidad: indícala en el programa."
    _aviso(msg)


try:
    exportar()
except Exception as e:
    import traceback
    _aviso("Error al exportar:\n%s\n\n%s" % (e, traceback.format_exc()), True)
