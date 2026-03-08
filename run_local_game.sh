#!/bin/bash
./battlesnake play -W 11 -H 11 \
  --name "Food Bot" --url "http://localhost:8000/food" \
  --name "Aggressive Bot" --url "http://localhost:8000/aggressive" \
  --name "Avoidant Bot" --url "http://localhost:8000/avoidant" \
  --name "Dynamic Bot" --url "http://localhost:8000/dynamic" \
  --name "Dynamic2 Bot" --url "http://localhost:8000/dynamic2" \
  --name "Dynamic3 Bot" --url "http://localhost:8000/dynamic3" \
  --browser
