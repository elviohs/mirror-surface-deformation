@echo off
chcp 65001 >nul
echo Instalando dependencias para fem_mirror_analysis...
echo.

python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

echo.
echo Listo. Puedes cerrar esta ventana y ejecutar la GUI o el script de consola.
pause
