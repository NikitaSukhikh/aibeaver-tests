@echo off
setlocal

pushd "%~dp0..\.." >nul
python tests\reasoning_questions\run_reasoning_eval.py %*
set EXIT_CODE=%ERRORLEVEL%
popd >nul

exit /b %EXIT_CODE%
