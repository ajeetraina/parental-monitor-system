@echo off
title ParentWatch - Running in background
cd /d "%~dp0"
python monitor_agent.py
pause
