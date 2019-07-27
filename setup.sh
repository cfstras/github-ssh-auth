#!/bin/bash
set -euo pipefail

SERVICE_PATH=$HOME/.config/systemd/user/
SERVICE=github-ssh-auth.service
TIMER=github-ssh-auth.timer
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

ENV=.env
PIP=$ENV/bin/pip

make_venv() {
    echo "### Making virtualenv"
    [[ -x $PIP ]] || python3 -m venv $ENV
    $PIP install -r requirements.txt
}

install_service() {
    echo "### Installing systemd timer"
    mkdir -p "$SERVICE_PATH"

    sed "s#DIR#${DIR}#g" "$SERVICE" > "$SERVICE_PATH/$SERVICE"
    sed "s#DIR#${DIR}#g" "$TIMER" > "$SERVICE_PATH/$TIMER"

    echo "### Enabling systemd timer"
    systemctl --user daemon-reload
    systemctl --user enable "$TIMER"
    systemctl --user start "$TIMER"

    echo "### Starting service once"
    systemctl --user start "$SERVICE" || journalctl -xe
    echo "### Please edit config.yml to your liking."
}

check_linger() {
    if loginctl show-user "$USER" | grep Linger=no >/dev/null 2>&1; then
        echo "Enabling loginctl linger"
        sudo loginctl enable-linger "$USER"
    fi
}

make_venv
check_linger
install_service
