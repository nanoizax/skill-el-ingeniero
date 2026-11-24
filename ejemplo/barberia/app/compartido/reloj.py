"""Reloj real. Los casos de uso reciben un reloj para poder probar el paso del tiempo."""
from datetime import datetime, timezone


def reloj_real():
    return datetime.now(timezone.utc)
