#!/bin/sh
#
# termux-tasker installer
#
# Downloads and installs termux-tasker in your Termux home directory.
#
# Usage:
#   curl -sL https://kpliuta.github.io/termux-tasker/install.sh | sh
#

set -eu

REPO_URL="https://github.com/kpliuta/termux-tasker.git"
INSTALL_DIR="$HOME/termux-tasker"

info() {
    printf '\033[1;34m%s\033[0m\n' "$1"
}

success() {
    printf '\033[1;32m%s\033[0m\n' "$1"
}

die() {
    printf '\033[1;31m%s\033[0m\n' "$1" >&2
    exit 1
}

# ── Ensure git is available ───────────────────────────────────────────────────

if ! command -v git >/dev/null 2>&1; then
    info "Installing git..."
    pkg install -y git >/dev/null 2>&1 || die "Failed to install git."
fi

# ── Clone or update ──────────────────────────────────────────────────────────

if [ -d "$INSTALL_DIR/.git" ]; then
    info "Updating existing installation..."
    cd "$INSTALL_DIR"
    git fetch --tags --quiet 2>/dev/null || true
else
    info "Cloning termux-tasker..."
    git clone --quiet "$REPO_URL" "$INSTALL_DIR" \
        || die "Failed to clone repository."
    cd "$INSTALL_DIR"
fi

# ── Collect version tags ─────────────────────────────────────────────────────

TAGS=$(git tag -l '[0-9]*.[0-9]*.[0-9]*' 2>/dev/null | sort -V -r || true)

# ── Version selection ─────────────────────────────────────────────────────────

printf '\n'
info "Select a version to install:"
printf '\n  \033[1m1)\033[0m main (default)\n'

IDX=2
TAG_LIST=""
for TAG in $TAGS; do
    printf '  \033[1m%d)\033[0m %s\n' "$IDX" "$TAG"
    TAG_LIST="$TAG_LIST $TAG"
    IDX=$((IDX + 1))
done

printf '\n  Enter choice [1]: '
read -r CHOICE </dev/tty

CHOICE=${CHOICE:-1}

SELECTED_TAG=""
if [ "$CHOICE" = "1" ]; then
    SELECTED_TAG="main"
else
    COUNT=1
    for TAG in $TAGS; do
        COUNT=$((COUNT + 1))
        if [ "$COUNT" = "$CHOICE" ]; then
            SELECTED_TAG="$TAG"
            break
        fi
    done
fi

[ -n "$SELECTED_TAG" ] || die "Invalid choice: $CHOICE"

# ── Checkout ──────────────────────────────────────────────────────────────────

info "Checking out $SELECTED_TAG..."
git checkout --quiet "$SELECTED_TAG" \
    || die "Failed to checkout $SELECTED_TAG."

success "Installed termux-tasker ($SELECTED_TAG)"

# ── Launch prompt ─────────────────────────────────────────────────────────────

printf '\n  Launch termux-tasker now? [Y/n]: '
read -r LAUNCH </dev/tty

LAUNCH=${LAUNCH:-Y}
case "$LAUNCH" in
    [Yy]*)
        info "Starting termux-tasker..."
        exec ./run.sh </dev/tty >/dev/tty 2>&1
        ;;
    *)
        printf '\n  To launch later, run:\n\n'
        printf '    cd ~/termux-tasker && ./run.sh\n\n'
        ;;
esac
