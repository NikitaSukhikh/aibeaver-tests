@echo off
setlocal

pushd "%~dp0..\.." >nul
python tests\multihiertt_mini\run_multihiertt_eval.py --modes all --providers openai --questions 10 %*
set EXIT_CODE=%ERRORLEVEL%
popd >nul

exit /b %EXIT_CODE%
