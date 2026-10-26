@echo off
setlocal EnableDelayedExpansion
set "ROOT=%~dp0"
set "HOST=127.0.0.1"
set "PORT=8080"
set "WEBPORT=8765"
set "CTX=8192"
set "NGL=999"

where python >nul 2>&1
if errorlevel 1 (
  echo [launch] Python was not found on your PATH. Install Python 3 and try again.
  exit /b 1
)

set "MODELSDIR="
if /I not "%~1"=="--models-dir" goto :noModelsDirArg
if not "%~2"=="" set "MODELSDIR=%~2"
shift
shift
:noModelsDirArg

set "FORCECLI="
if /I "%~1"=="--cli" set "FORCECLI=1"

set "CFGMODEL="
set "CFGCTX="
set "CFGNGL="
set "CFGMODELSDIR="
for /f "usebackq tokens=1-4 delims=|" %%A in (`python -c "import json,pathlib;p=pathlib.Path(r'%ROOT%web/web_config.json');d=(json.loads(p.read_text('utf-8')).get('llama',{}) if p.exists() else {});print('X'+str(d.get('model',''))+'|X'+str(d.get('context_size',''))+'|X'+str(d.get('gpu_layers',''))+'|X'+str(d.get('models_dir','')))" 2^>nul`) do (
  set "CFGMODEL=%%A"
  set "CFGCTX=%%B"
  set "CFGNGL=%%C"
  set "CFGMODELSDIR=%%D"
)
if defined CFGMODEL set "CFGMODEL=%CFGMODEL:~1%"
if defined CFGCTX set "CFGCTX=%CFGCTX:~1%"
if defined CFGNGL set "CFGNGL=%CFGNGL:~1%"
if defined CFGMODELSDIR set "CFGMODELSDIR=%CFGMODELSDIR:~1%"
if defined CFGCTX if not "%CFGCTX%"=="" set "CTX=%CFGCTX%"
if defined CFGNGL if not "%CFGNGL%"=="" set "NGL=%CFGNGL%"

if not defined MODELSDIR if defined CFGMODELSDIR if not "%CFGMODELSDIR%"=="" set "MODELSDIR=%CFGMODELSDIR%"
if not defined MODELSDIR set "MODELSDIR=%ROOT%llm\models"

set "MODEL=%~1"
if "%MODEL:~0,2%"=="--" set "MODEL="
if "%MODEL%"=="" if defined CFGMODEL if not "%CFGMODEL%"=="" set "MODEL=%CFGMODEL%"
if "%MODEL%"=="" (
  for %%F in ("%MODELSDIR%\*.gguf") do if not defined MODEL set "MODEL=%%~nxF"
)
if "%MODEL%"=="" (
  echo [launch] No .gguf model found in "%MODELSDIR%".
  echo          Drop a .gguf there ^(or pass --models-dir "C:\path"^); for now the no-model narrator runs.
  goto :nomodel
)
set "MODELPATH=%MODELSDIR%\%MODEL%"

set "SERVER=%ROOT%llm\llama-server.exe"
if not exist "%SERVER%" set "SERVER=llama-server.exe"

set "SERVERARG="
if not exist "%MODELPATH%" (
  echo [launch] No model found at %MODELPATH%
  echo          The interface will use the built-in no-model narrator.
  goto :nomodel
)

echo [launch] Starting llama-server with "%MODEL%" on %HOST%:%PORT% ...
start "llama-server (%MODEL%)" /min "%SERVER%" -m "%MODELPATH%" --host %HOST% --port %PORT% -c %CTX% -ngl %NGL%
echo [launch] Waiting for the model to load ...
set /a TRIES=0
:wait
python -c "import socket,http.client,sys; s=socket.socket(); s.settimeout(2); rc=s.connect_ex(('%HOST%',%PORT%)); s.close(); rc and sys.exit(1); c=http.client.HTTPConnection('%HOST%',%PORT%,timeout=3); c.request('GET','/health'); r=c.getresponse(); sys.exit(0 if r.status==200 else 1)" >nul 2>&1
if errorlevel 1 (
  set /a TRIES+=1
  if !TRIES! GTR 600 ( echo [launch] Model did not come up after 10 min; continuing with the no-model narrator. & goto :nomodel )
  set /a "MOD=TRIES %% 15"
  if !MOD!==0 echo [launch]   ...still loading the model, !TRIES! s elapsed
  timeout /t 1 /nobreak >nul
  goto wait
)
set "SERVERARG=--server http://%HOST%:%PORT%/completion"
echo [launch] Model is up.

:nomodel

if defined FORCECLI goto :cli

echo [launch] Starting the web interface on http://%HOST%:%WEBPORT%/ ...
python "%ROOT%run_web.py" --host %HOST% --port %WEBPORT% %SERVERARG%
if errorlevel 1 (
  echo [launch] Web interface could not start -- falling back to the command line.
  goto :cli
)
goto :done

:cli
echo [launch] Starting the command-line interface ...
if defined SERVERARG (
  python "%ROOT%run.py" %SERVERARG% %2 %3 %4 %5 %6
) else (
  python "%ROOT%run.py" --fake %2 %3 %4 %5 %6
)

:done
echo.
echo [launch] Game exited. If a llama-server window is open, close it to free the model.
endlocal
