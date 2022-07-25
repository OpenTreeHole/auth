#!/bin/sh
aerich upgrade
uvicorn --host 0.0.0.0 main:app --no-access-log