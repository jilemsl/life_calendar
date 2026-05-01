"""
Double-click this file to start Life Calendar and open it in your browser.
No console window. Requires Python + dependencies already installed (run run.bat first).
"""
import subprocess, os, sys, time, webbrowser, urllib.request

here = os.path.dirname(os.path.abspath(__file__))
os.chdir(here)

proc = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", "app.py", "--server.headless", "true"],
    cwd=here,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Poll until Streamlit accepts connections (up to 20 s)
for _ in range(20):
    try:
        urllib.request.urlopen("http://localhost:8501", timeout=1)
        break
    except Exception:
        time.sleep(1)

webbrowser.open("http://localhost:8501")
proc.wait()
