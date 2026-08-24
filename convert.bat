@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0convert.ps1" %*
exit /b %ERRORLEVEL%
