#!/usr/bin/env bash
if [ -d "venv" ]; then
    ./venv/bin/python3 -m maxmusic
else
    python3 -m maxmusic
fi
