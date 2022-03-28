#!/bin/sh
aerich migrate
aerich upgrade
uvicorn --host 0.0.0.0 main:app