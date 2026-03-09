##  ParentWatch - Parental Monitor Tool

```
FILES:
  monitor_agent.py          - Main monitor (runs on laptop)
  dashboard.html            - Web dashboard (auto-served)
  START_MONITOR.bat         - Windows: double-click to start
  start_monitor.sh          - Mac/Linux: run in terminal
  install_autostart_windows.bat - Auto-start on Windows boot
```


SETUP (One-time):
  1. Install Python 3: https://python.org
  2. Copy ALL files to son's laptop (same folder)
  3. Double-click START_MONITOR.bat (Windows)
     OR run: python3 monitor_agent.py (Mac/Linux)
  4. Note the IP address shown (e.g. 192.168.1.42)

VIEWING ON SMART TV:
  1. Open TV browser
  2. Go to: http://[IP_ADDRESS]:8765
  Example: http://192.168.1.42:8765
  
  Both laptop and TV must be on the SAME WiFi network!

AUTO-START ON BOOT (Windows):
  Run install_autostart_windows.bat as Administrator

OPTIONAL (Linux only):
  Install xdotool for better window detection:
  sudo apt install xdotool

CATEGORIES:
  ✅ Green  = Educational/Productive (coding, docs, study sites)
  ⚠️ Yellow = Neutral (general browsing, communication)
  🔴 Red    = Distraction (games, social media, entertainment)

PRIVACY NOTE:
  This tool only reads active window titles - no screenshots,
  no keylogging, no file access. Works over your home WiFi.
