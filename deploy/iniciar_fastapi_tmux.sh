#!/bin/bash
set -euo pipefail

PROYECTO=/opt/pccomponentes-ml-analysis
ARCHIVO_ENV=/etc/pccomponentes/api.env
SESION=fastapi

# La instancia es pequeña. Este swap temporal ayuda durante las instalaciones.
if ! swapon --show=NAME --noheadings | grep -q "/swapfile"; then
    if [ ! -f /swapfile ]; then
        dd if=/dev/zero of=/swapfile bs=1M count=1024
    fi
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
fi

dnf install -y tmux

# El usuario de EC2 necesita leer las variables para iniciar FastAPI.
chown root:ec2-user "$ARCHIVO_ENV"
chmod 640 "$ARCHIVO_ENV"

# Evita que systemd y tmux intenten usar el puerto 8000 a la vez.
systemctl disable --now pccomponentes-api 2>/dev/null || true

if sudo -u ec2-user tmux has-session -t "$SESION" 2>/dev/null; then
    sudo -u ec2-user tmux kill-session -t "$SESION"
fi

sudo -u ec2-user tmux new-session -d -s "$SESION" \
    "cd $PROYECTO && set -a && . $ARCHIVO_ENV && set +a && exec .venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload"

echo "FastAPI iniciado en la sesion tmux: $SESION"
echo "Para verla: tmux attach -t $SESION"
