@echo off
setlocal
cd /d "%~dp0\..\.."
python tests\llm_mcd\run_mcd_eval.py %*
