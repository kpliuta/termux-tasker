#!/usr/bin/env bash
#
# termux-tasker — Entry point
#
# Usage:
#   ./run.sh [--skip-android-init] [--help]
#
# Options:
#   --skip-android-init  Skip Android-specific environment checks (for local dev)
#   --help               Show this help message
#
# When run on Android/Termux, this script installs Python and Poetry if
# needed, installs project dependencies, and launches the app.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKIP_ANDROID_INIT=""

show_help() {
    sed -n '3,13p' "$0"
    exit 0
}

# ── Parse arguments ────────────────────────────────────────────────────────────

for arg in "$@"; do
    case "$arg" in
        --help|-h)
            show_help
            ;;
        --skip-android-init)
            SKIP_ANDROID_INIT="--skip-android-init"
            ;;
        *)
            echo "Unknown argument: $arg"
            echo "Use --help for usage."
            exit 1
            ;;
    esac
done

# ── Detect Termux environment ──────────────────────────────────────────────────

if [ -n "${TERMUX_VERSION:-}" ]; then
    echo "Detected Termux environment."

    # Install Python if missing
    if ! command -v python &>/dev/null; then
        echo "Installing Python..."
        pkg install -y python
    fi

    # Install Poetry if missing
    if ! command -v poetry &>/dev/null; then
        echo "Installing Poetry..."
        pip install poetry
    fi
fi

# ── Ensure Poetry is available ─────────────────────────────────────────────────

if ! command -v poetry &>/dev/null; then
    echo "Error: Poetry is required. Install it with:"
    echo "  pip install poetry"
    exit 1
fi

# ── Install project dependencies ───────────────────────────────────────────────

echo "Installing project dependencies..."
cd "$PROJECT_ROOT"
poetry install --no-interaction

# ── Launch the app ─────────────────────────────────────────────────────────────

echo "Starting termux-tasker..."
exec poetry run python -m termux_tasker.app ${SKIP_ANDROID_INIT:+"$SKIP_ANDROID_INIT"}
