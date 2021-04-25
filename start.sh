#!/bin/bash

nohup python telegram-bot.py &
uvicorn api.main:app --host "0.0.0.0" --port 8080
