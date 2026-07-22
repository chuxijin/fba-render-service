@echo off
setlocal
pushd "%~dp0"

if "%~1"=="" goto :help
if /i "%~1"=="run" goto :run
if /i "%~1"=="help" goto :help
if /i "%~1"=="-h" goto :help
if /i "%~1"=="--help" goto :help

echo Unknown command: %~1
echo.
goto :help

:run
if not exist ".venv\Scripts\python.exe" (
  echo .venv not found.
  echo Create it with:
  echo   python -m venv .venv
  echo   .venv\Scripts\pip install -r render_service\requirements.txt
  popd
  exit /b 1
)

set RENDER_SERVICE_HOST=%RENDER_SERVICE_HOST%
if "%RENDER_SERVICE_HOST%"=="" set RENDER_SERVICE_HOST=0.0.0.0
set RENDER_SERVICE_PORT=%RENDER_SERVICE_PORT%
if "%RENDER_SERVICE_PORT%"=="" set RENDER_SERVICE_PORT=9000
if "%RENDER_SERVICE_TEMPLATES_ROOT%"=="" if exist "..\fba\backend\plugin\render_book\templates" set RENDER_SERVICE_TEMPLATES_ROOT=%~dp0..\fba\backend\plugin\render_book\templates
if "%RENDER_SERVICE_TEMPLATES_ROOT%"=="" (
  echo Template directory not found. Set RENDER_SERVICE_TEMPLATES_ROOT.
  popd
  exit /b 1
)

echo Starting render service on http://%RENDER_SERVICE_HOST%:%RENDER_SERVICE_PORT% ...
.venv\Scripts\python.exe -m uvicorn render_service.app.main:app --host %RENDER_SERVICE_HOST% --port %RENDER_SERVICE_PORT% --reload
popd
goto :eof

:help
echo Usage: gen ^<command^>
echo.
echo Commands:
echo   run    Start the FastAPI render service (uvicorn --reload, default 0.0.0.0:9000)
echo   help   Show this help
echo.
echo Env overrides:
echo   RENDER_SERVICE_HOST   override bind host
echo   RENDER_SERVICE_PORT   override port
echo   RENDER_SERVICE_TEMPLATES_ROOT   versioned template release directory
popd
goto :eof
