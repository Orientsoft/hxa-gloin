#!/usr/bin/env bash
uvicorn --host=0.0.0.0 app.main:app --workers=1
