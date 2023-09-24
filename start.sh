#!/bin/bash

# Start the FastAPI application
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start hiker_competition.py
python hiker_competition.py &

# Keep script running
wait