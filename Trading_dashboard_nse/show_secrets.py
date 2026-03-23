"""
Show stored Angel Broking secrets in a masked form for local testing.

Usage:
    python scripts/show_secrets.py

This script will attempt to read from Windows Credential Manager (via keyring)
first, then from environment variables / .env fallback. It only prints masked
values (so you can verify values are present without exposing them in clear).
"""

from __future__ import annotations
import os
from secrets_config import get_all_secrets

try:
    import keyring
    _KEYRING_AVAILABLE = True
except Exception:
    _KEYRING_AVAILABLE = False

SERVICE = 'angel_broking'

KEYS = ['api_key', 'client_id', 'password', 'totp_secret']


def _mask(val: str | None) -> str:
    if val is None:
        return '<NOT SET>'
    s = str(val)
    if len(s) <= 6:
        return s[0] + '***' if len(s) > 1 else '***'
    return s[:3] + '*' * max(3, len(s) - 6) + s[-3:]


def _source_for(key: str) -> tuple[str, str | None]:
    """Return (source, value)
    source: 'keyring' | 'env' | 'none'
    value: retrieved value or None
    """
    # Try keyring first (if available).
    if _KEYRING_AVAILABLE:
        try:
            v = keyring.get_password(SERVICE, key)
            if v:
                return ('keyring', v)
        except Exception:
            pass
    # Then check env vars
    envname = {
        'api_key': 'ANGEL_API_KEY',
        'client_id': 'ANGEL_CLIENT_ID',
        'password': 'ANGEL_PASSWORD',
        'totp_secret': 'ANGEL_TOTP_SECRET'
    }.get(key, f'ANGEL_{key.upper()}')
    v = os.environ.get(envname)
    if v:
        return ('env', v)
    # Fallback: use secrets_config's loader (which already tries keyring+env)
    sc = get_all_secrets().get(key)
    if sc:
        return ('fallback', sc)
    return ('none', None)


def main():
    print('\nAngel Broking Secrets — masked (for testing)')
    print('Service:', SERVICE)
    print('Keyring available:', _KEYRING_AVAILABLE)
    print('-' * 60)
    print(f"{'KEY':<14} {'SOURCE':<10} {'VALUE (masked)'}")
    print('-' * 60)
    for k in KEYS:
        src, val = _source_for(k)
        print(f"{k:<14} {src:<10} {_mask(val)}")
    print('-' * 60)
    missing = [k for k in KEYS if _source_for(k)[0] == 'none']
    if missing:
        print('WARNING: The following keys are not configured:', ', '.join(missing))
        print('Run: python setup_secrets.py  (to store securely in Windows Credential Manager)')
    else:
        print('All keys found (some may come from .env). Consider running setup_secrets.py to store them in OS vault.')

if __name__ == '__main__':
    main()
