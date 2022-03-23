#!/bin/sh
aerich migrate
aerich upgrade
python app.py
