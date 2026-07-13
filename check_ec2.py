"""Comprueba que el despliegue EC2 no contiene secretos."""

from aws.infra_ec2 import PARAMETRO_DATABASE_URL, _crear_user_data


script = _crear_user_data("eu-north-1")

assert "postgresql://" not in script
assert PARAMETRO_DATABASE_URL in script
assert "--with-decryption" in script
assert "pccomponentes-api.service" in script

print("EC2: comprobacion correcta")
