#!/usr/bin/env bash
set -e
uvicorn app.main:app --reload --port 8000
