#!/bin/sh
set -e

exec uv run python -m app "$@"
