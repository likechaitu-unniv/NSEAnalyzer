"""
Secrets loader for Angel Broking credentials.

Priority order:
  1. Windows Credential Manager (via keyring) — most secure, encrypted by OS
  2. .env file in this directory           — plaintext fallback (never commit this)
  3. OS environment variables              — e.g. set in a start script

Usage:
    from secrets_config import get_secret, ANGEL_SECRETS

    api_key   = get_secret('api_key')
    client_id = get_secret('client_id')

Setup (one-time, stores in Windows Credential Manager):
    python setup_secrets.py
"""

import os
from dotenv import load_dotenv

# Load .env file as a plaintext fallback (if present)
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(_env_path)

# Keyring service name — all credentials are grouped under this
_SERVICE = 'angel_broking'

# Map of secret keys → environment variable names (used as fallback)
_ENV_MAP = {
    'api_key':     'ANGEL_API_KEY',
    'client_id':   'ANGEL_CLIENT_ID',
    'password':    'ANGEL_PASSWORD',
    'totp_secret': 'ANGEL_TOTP_SECRET',
}


def get_secret(key: str) -> str | None:
    """
    Retrieve a secret by key.

    Tries in order:
      1. Windows Credential Manager (keyring)
      2. .env file / environment variable
    Returns None if not found anywhere.
    """
    # 1. Try Windows Credential Manager
    try:
        import keyring
        value = keyring.get_password(_SERVICE, key)
        if value:
            return value
    except Exception:
        pass  # keyring not installed or unavailable — fall through

    # 2. Try environment variable (.env or system)
    env_name = _ENV_MAP.get(key, f'ANGEL_{key.upper()}')
    return os.environ.get(env_name)


def get_all_secrets() -> dict:
    """Return all Angel Broking secrets as a dict. Values may be None if not set."""
    return {key: get_secret(key) for key in _ENV_MAP}


def check_secrets() -> list[str]:
    """Return list of secret keys that are missing/not configured."""
    return [k for k, v in get_all_secrets().items() if not v]


# Convenience dict — populated at import time
ANGEL_SECRETS = get_all_secrets()
