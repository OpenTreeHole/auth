#!/bin/sh
python migrate.py
uvicorn --host 0.0.0.0 main:app --no-access-log