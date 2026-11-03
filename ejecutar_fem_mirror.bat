@echo off
chcp 65001 >nul
REM Analisis FEM de superficie de espejo (modo consola)
REM El script debe estar en la misma carpeta que este .bat
REM Requiere Python 3.9+ con numpy, scipy y matplotlib instalados.

REM ── PARAMETROS A EDITAR ─────────────────────────────────────────────

REM Fichero de datos FEM (nodo X Y Z dX dY dZ  o  X Y Z dX dY dZ)
set DATOS="ruta\a\tu\fichero.TXT"

REM Modos de solido rigido a eliminar: Tx Ty Tz Rx Ry Rz  (0=no, 1=si)
set RIGID=0 0 1 0 0 0

REM Apertura: circular (Zernike), annular (Mahajan), hexagonal o rectangular (Mahajan-Dai),
REM o elliptical (espejos plegados; ejes con --width/--height)
set APERTURA=circular

REM Error de superficie: sag (recomendado) o normal
set MAGNITUD=sag

REM Convencion de Zernike (solo apertura circular): fringe o noll
REM (anular/hexagonal/rectangular usan siempre el orden de Noll)
set CONVENCION=fringe

REM Numero de terminos a ajustar (los N primeros de la base; 0 = solo RMS)
set NTERMS=3

REM Normalizacion: pico o rms
set NORM=pico

REM Sistema de referencia: global (Z = eje optico) o bestfit
set FRAME=global

REM Unidades de longitud del fichero: mm, m, um o nm
set UNIDADES=mm

REM Longitud de onda [nm] y angulo de incidencia [grados] para Strehl
set LAMBDA=632.8
set INCIDENCIA=0

REM Descomposicion ISO: rot (revolucion: A, B, C) o cyl (cilindrica/torica: AX, AY, B, CX, CY)
set FORMA_ISO=rot
REM Giro de los ejes del cilindro/toro respecto a X/Y [grados]
set GIRO_EJES=0

REM Tolerancia ISO 10110-5 a comprobar (vacio = no comprobar), p. ej.:
REM set "ISO=3/900 nm (250 nm/100 nm) RMSi < 30 nm"
set "ISO="

REM Exportacion a Zemax (Grid Sag .dat) y QUADOA (CSV x,y,z) + coeficientes Zernike.
REM Ruta base de los ficheros (vacio = no exportar), p. ej.:
REM set "EXPORTAR=resultados\espejo"
set "EXPORTAR="
REM Superficie a exportar: sin_rigido o residuo (tras el ajuste)
set EXP_SUPERFICIE=sin_rigido
REM Unidades de lente del fichero exportado: mm, cm, in o m
set EXP_UNIDADES=mm

REM Si el fichero tiene varios casos de carga apilados, anade:  --case N
REM Combinacion de casos de gravedad (en lugar de DATOS), p. ej.:
REM   --gravity g0.TXT 0 --gravity g45.TXT 45 --elevation 60 --sweep 0 90 15

REM ────────────────────────────────────────────────────────────────────

python "%~dp0fem_mirror_analysis.py" %DATOS% ^
    --rigid %RIGID% ^
    --aperture %APERTURA% ^
    --convention %CONVENCION% ^
    --nterms %NTERMS% ^
    --norm %NORM% ^
    --frame %FRAME% ^
    --quantity %MAGNITUD% ^
    --units %UNIDADES% ^
    --wavelength %LAMBDA% ^
    --incidence %INCIDENCIA% ^
    --iso-spec "%ISO%" ^
    --iso-form %FORMA_ISO% ^
    --iso-axis-angle %GIRO_EJES% ^
    --export "%EXPORTAR%" ^
    --export-surface %EXP_SUPERFICIE% ^
    --export-units %EXP_UNIDADES% ^
    --plot

pause
