@echo off
setlocal

pushd "%~dp0..\.." >nul
python tests\llm_unpacked_vs_disconnected\run_unpacked_vs_disconnected.py %*
set EXIT_CODE=%ERRORLEVEL%
popd >nul

exit /b %EXIT_CODE%
