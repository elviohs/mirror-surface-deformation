#!/usr/bin/env python3
"""
build_exe.py — Construye el ejecutable de Windows de la GUI (un único .exe)
con PyInstaller, para usar el programa sin instalar Python.

    python -m pip install -r requirements.txt pyinstaller pillow
    python build_exe.py

Resultado: dist/FEM_Mirror_Analysis_<versión>.exe

Comprobación sin ventana del ejecutable (escribe el resultado en un TXT y
devuelve 0 si todo va bien):

    dist\\FEM_Mirror_Analysis_<versión>.exe --selftest resultado.txt

El ejecutable se construye para el sistema en el que se ejecuta este script:
para obtener un .exe hay que construirlo en Windows (lo hace la acción de
GitHub .github/workflows/build-exe.yml al publicar una versión).
"""
import base64
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def version():
    src = open(os.path.join(HERE, 'fem_mirror_analysis.py'), encoding='utf-8').read()
    return re.search(r'^__version__ = "([^"]+)"', src, re.M).group(1)


def make_icon(path):
    """Icono .ico a partir del logo embebido en la GUI (centrado en un cuadrado)."""
    from PIL import Image
    src = open(os.path.join(HERE, 'gui_fem_mirror.py'), encoding='utf-8').read()
    i0 = src.index('_LOGO_B64 = (')
    b64 = ''.join(re.findall(r'"([A-Za-z0-9+/=]+)"', src[i0:src.index(')', i0)]))
    img = Image.open(io.BytesIO(base64.b64decode(b64))).convert('RGBA')
    side = max(img.size)
    square = Image.new('RGBA', (side, side), (255, 255, 255, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    square = square.resize((256, 256), Image.LANCZOS)
    square.save(path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64),
                             (128, 128), (256, 256)])


def main():
    import PyInstaller.__main__
    os.chdir(HERE)
    os.makedirs('build', exist_ok=True)
    icon = os.path.join(HERE, 'build', 'fem_mirror.ico')
    args = []
    try:
        make_icon(icon)
        args += ['--icon', icon]
    except Exception as e:                      # sin Pillow: ejecutable sin icono
        print(f"Aviso: no se pudo crear el icono ({e}); se continúa sin él.")
    # python-docx abre sus plantillas con rutas «docx/parts/../templates/…»:
    # la carpeta docx/parts tiene que existir dentro del ejecutable aunque sus
    # módulos vayan comprimidos; se añade un fichero suyo como dato.
    import docx
    parts = os.path.join(os.path.dirname(docx.__file__), 'parts', '__init__.py')
    args += ['--add-data', f"{parts}{os.pathsep}docx/parts"]
    name = f"FEM_Mirror_Analysis_{version()}"
    PyInstaller.__main__.run([
        os.path.join(HERE, 'gui_fem_mirror.py'),
        '--name', name,
        '--onefile', '--windowed',
        '--noconfirm', '--clean',
        '--paths', HERE,
        '--hidden-import', 'fem_mirror_analysis',
        '--hidden-import', 'report_fem_mirror',
        '--hidden-import', 'mpl_toolkits.mplot3d',
        '--collect-data', 'docx',               # plantilla Word de python-docx
        # Módulos grandes que el programa no usa
        '--exclude-module', 'IPython',
        '--exclude-module', 'pandas',
        '--exclude-module', 'PyQt5',
        '--exclude-module', 'PyQt6',
        '--exclude-module', 'PySide2',
        '--exclude-module', 'PySide6',
        *args,
    ])
    exe = os.path.join(HERE, 'dist', name + ('.exe' if sys.platform.startswith('win') else ''))
    print(f"\nEjecutable: {exe}")


if __name__ == '__main__':
    main()
