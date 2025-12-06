@echo off
REM Script para ejecutar Hotel Management System en Windows

echo ========================================
echo   Hotel Management System
echo ========================================
echo.

REM Verificar si existe el entorno virtual
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Instalar dependencias
echo.
echo Verificando dependencias...
pip install -r requirements.txt -q

REM Verificar si la BD existe
if not exist "hotel.db" (
    echo.
    echo Inicializando base de datos...
    python init_db.py
)

REM Ejecutar la aplicación
echo.
echo ========================================
echo   Iniciando aplicación...
echo ========================================
echo.
echo URL: http://localhost:5000
echo.
echo Usuario Demo: admin
echo Contraseña: admin123
echo.
echo Presione Ctrl+C para detener el servidor
echo.

python app.py
pause
