@echo off
echo ========================================
echo Reiniciando Servidor FastAPI
echo ========================================
echo.
echo Deteniendo procesos uvicorn existentes...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Limpiando cache de Python...
if exist app\__pycache__ rmdir /s /q app\__pycache__
if exist app\api\__pycache__ rmdir /s /q app\api\__pycache__
if exist app\api\v1\__pycache__ rmdir /s /q app\api\v1\__pycache__
if exist app\services\__pycache__ rmdir /s /q app\services\__pycache__
if exist app\infra\__pycache__ rmdir /s /q app\infra\__pycache__
if exist app\models\__pycache__ rmdir /s /q app\models\__pycache__
if exist app\domain\__pycache__ rmdir /s /q app\domain\__pycache__

echo.
echo Iniciando servidor en puerto 8000...
echo.
echo ========================================
echo Servidor disponible en:
echo   - Swagger UI: http://localhost:8000/docs
echo   - ReDoc: http://localhost:8000/redoc
echo   - OpenAPI JSON: http://localhost:8000/openapi.json
echo ========================================
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

.venv\Scripts\uvicorn.exe app.main:app --reload --port 8000 --host 0.0.0.0
