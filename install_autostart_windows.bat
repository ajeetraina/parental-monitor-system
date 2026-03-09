@echo off
:: Creates a startup task so monitor runs when Windows boots
echo Installing ParentWatch autostart...
set SCRIPT_PATH=%~dp0monitor_agent.py
schtasks /create /tn "ParentWatch" /tr "pythonw \"%SCRIPT_PATH%\"" /sc onlogon /rl highest /f
echo.
echo Done! ParentWatch will start automatically on login.
echo To remove: schtasks /delete /tn "ParentWatch" /f
pause
