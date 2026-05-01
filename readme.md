# Life Calendar

A local app to track daily activities, write a diary, and visualize your life over time.

## Requirements

- Python 3.9 or later — download from https://python.org

## First launch

**Windows** — double-click `run.bat`.  
It installs all dependencies and starts the app. The browser opens automatically.

**Mac / Linux** — open a terminal in the project folder and run:
```
pip install -r requirements.txt
streamlit run app.py
```

If you downloaded a zip from GitHub instead of using git, extract it first, then open a terminal inside the extracted folder.

## Subsequent launches

**Windows** — double-click `open.pyw`.  
No console window, no reinstall. It starts the server and opens your browser.

**Mac / Linux** — run `./open.sh` in the project folder (first time: `chmod +x open.sh`).

## Features

- **Dashboard** — calendar heatmap (red → green), streak, stats, recent entries
- **Add Entry** — log activity scores (−10 to 10), durations, and a diary note per day
- **Review** — browse past days with scores and diary, pick a date or hit Random
- **Charts** — interactive time series for daily score and individual activities
- **Arcs** — name periods of your life (e.g. "Exam season", "Summer 2026") and see them overlaid on charts
- **Settings** — add/remove tracked activities, export your profile as a zip to share with friends, import a friend's profile
