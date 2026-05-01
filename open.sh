#!/bin/bash
cd "$(dirname "$0")"

streamlit run app.py --server.headless true &

# Wait until the server is up (max 20 s)
for i in $(seq 1 20); do
    curl -s http://localhost:8501 > /dev/null 2>&1 && break
    sleep 1
done

# Open browser (macOS: open, Linux: xdg-open)
if command -v open &> /dev/null; then
    open http://localhost:8501
else
    xdg-open http://localhost:8501
fi

wait
