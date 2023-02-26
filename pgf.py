#!/usr/bin/env python3

"""Postfix content filter for encrypting outgoing messages with GPG."""

import email.policy
import logging
import sys
from email.message import EmailMessage
from email.parser import Parser
from smtplib import SMTP
from typing import Optional

import gnupg  # type: ignore

HOST = "localhost"
PORT = 10026
GPG_HOME = "/var/lib/pgf"
USE_STARTTLS = True
RECIPIENT_OVERRIDE = ""
LOG_FILE = "/var/log/pgf.log"

logging.basicConfig(filename=LOG_FILE, encoding="utf-8", level=logging.DEBUG)
logger = logging.getLogger(__name__)

# TODO: Only log for self, not for gnupg
# TODO: Add relevant logging items
# TODO: Read config from /etc/pgf.conf


gpg = gnupg.GPG(gnupghome=GPG_HOME)


def get_gpg_fingerprint(recipient: str) -> Optional[str]:
    """Search for the recipient's fingerprint. Returns the fingerprint or None."""
    for key in gpg.list_keys():
        for uid in key["uids"]:
            if recipient in uid:
                return str(key["fingerprint"])
    return None


def encrypt_with_gpg(message: str, fingerprint: str) -> str:
    """Encrypt a message and return the encrypted message."""
    return str(gpg.encrypt(message, fingerprint, always_trust=True))


def main() -> None:
    """Called when the program is started."""
    if len(sys.argv) < 2:
        raise RuntimeError("Missing email recipient.")

    recipient = sys.argv[1]
    content = sys.stdin.read()

    message = Parser(policy=email.policy.SMTP).parsestr(content)

    msg = EmailMessage()

    for header, value in message.items():
        msg[header] = value

    payload = message.get_payload()

    if RECIPIENT_OVERRIDE and RECIPIENT_OVERRIDE != "":
        payload = f"Original message recipient: {msg.get('To', '(none)')}\n\n{payload}"
        recipient = RECIPIENT_OVERRIDE
        msg.replace_header("To", RECIPIENT_OVERRIDE)

    fingerprint = get_gpg_fingerprint(recipient)

    if fingerprint:
        payload = encrypt_with_gpg(payload, fingerprint)

    msg.set_content(payload)

    with SMTP(HOST, PORT) as smtp:
        if USE_STARTTLS:
            smtp.starttls()
        smtp.send_message(msg)
        smtp.quit()

    sys.exit(0)


if __name__ == "__main__":
    main()
