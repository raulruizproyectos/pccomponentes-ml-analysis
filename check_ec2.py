"""Comprueba que el despliegue EC2 no contiene secretos."""

from pathlib import Path

from aws.infra_ec2 import PARAMETRO_DATABASE_URL, _crear_user_data


script = _crear_user_data("eu-north-1")

assert "postgresql://" not in script
assert PARAMETRO_DATABASE_URL in script
assert "--with-decryption" in script
assert "python3.11 -m venv" in script
assert "iniciar_fastapi_tmux.sh" in script

script_tmux = (Path(__file__).parent / "deploy" / "iniciar_fastapi_tmux.sh").read_text(
    encoding="utf-8"
)
assert "/swapfile" in script_tmux
assert "tmux new-session" in script_tmux
assert "api.main:app" in script_tmux

print("EC2: comprobacion correcta")
