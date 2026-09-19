#!/usr/bin/env bash
set -euo pipefail

uv sync
uv run fastapi dev main.py
