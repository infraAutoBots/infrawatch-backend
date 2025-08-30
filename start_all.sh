#!/bin/bash

tmux new-session -d -s infrawatch 'python api/app.py'
tmux split-window -v -t infrawatch 'sudo /home/ubuntu/Code/infrawatch/infrawatch-backend/venv/bin/python3 monitor/monitor.py'
tmux split-window -v -t infrawatch 'cd ../infrawatch-frontend/ && npm run dev'
tmux select-layout -t infrawatch even-vertical
tmux attach -t infrawatch
