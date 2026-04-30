# Life Calendar

A local app to track daily activities, write a diary, and visualize your life over time.

## How to run

(python is mandatory)
open powershell (win+X -> powershell/terminal)

if git is installed : 
type git clone https://github.com/jilemsl/life_calendar
then type cd C:\Users\yourname\life_calendar

if git isn't installed : 
click the 'code' button on the browser github page of the project. download the .zip and extract it 
then type cd C:\Users\yourname\Downloads\life_calendar

then type (always in powershell) : 

```
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser.

To re open the app : open powershell (win+X) , cd C:\... (the path to life calendar), streamlit run app.py (no need to re install requirements)

## Features

- **Dashboard** — calendar heatmap (red → green), streak, stats, recent entries
- **Add Entry** — log activity scores (−10 to 10), durations, and a diary note per day
- **Charts** — interactive time series for daily score and individual activities
- **Arcs** — name periods of your life (e.g. "Exam season", "Summer 2026") and see them overlaid on charts
- **Settings** — add/remove tracked activities, export your profile as a zip to share with friends, import a friend's profile
