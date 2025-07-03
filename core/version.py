import subprocess
import os

def get_version(force_file=False):
    if not force_file:
        try:
            return subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.DEVNULL
            ).decode().strip()
        except Exception:
            pass
    # fallback para arquivo
    try:
        with open("core/version.txt") as f:
            return f.read().strip()
    except Exception:
        return "versao-desconhecida"


