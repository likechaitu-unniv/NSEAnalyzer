"""
One-time setup script: store Angel Broking credentials in Windows Credential Manager.
Run this ONCE from the command line:

    python setup_secrets.py

Credentials are encrypted and stored by Windows — they survive reboots
and are tied to your Windows login account.
"""

import getpass

try:
    import keyring
except ImportError:
    print("ERROR: keyring not installed. Run:  pip install keyring")
    raise SystemExit(1)

SERVICE = 'angel_broking'

FIELDS = [
    ('api_key',     'Angel Broking API Key'),
    ('client_id',   'Client ID / User ID'),
    ('password',    'Login Password'),
    ('totp_secret', 'TOTP Secret (the base-32 key shown when setting up authenticator)'),
]

print("=" * 60)
print("  Angel Broking — Secure Credentials Setup")
print("  Stored in: Windows Credential Manager (encrypted)")
print("=" * 60)
print()

for key, label in FIELDS:
    current = keyring.get_password(SERVICE, key)
    status = " [already set — press Enter to keep]" if current else " [not set]"
    print(f"{label}{status}")
    value = getpass.getpass(f"  Enter value (hidden): ").strip()
    if value:
        keyring.set_password(SERVICE, key, value)
        print(f"  ✓ Saved '{key}'\n")
    elif current:
        print(f"  → Kept existing value for '{key}'\n")
    else:
        print(f"  ⚠ Skipped '{key}' (will be None at runtime)\n")

print("=" * 60)
print("Setup complete. Verify with:  python -c \"from secrets_config import get_all_secrets; print(get_all_secrets())\"")
print("Note: password values are masked in Credential Manager but NOT in Python output above.")
print("=" * 60)
