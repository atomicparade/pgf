#!/usr/bin/env python3

"""Postfix content filter for encrypting outgoing messages with GPG."""

import copy
import email.policy
import logging
import subprocess
import sys
from email.message import EmailMessage
from email.parser import Parser
from smtplib import SMTP
from typing import Optional

HOST: str = "localhost"
PORT: int = 10026
USE_STARTTLS: bool = True
LOG_FILE: str = "/var/log/pgf.log"
GPG_HOMEDIR: str = "/var/lib/pgf"
RECIPIENT_OVERRIDE: str = ""

logging.basicConfig(filename=LOG_FILE, encoding="utf-8", level=logging.INFO)
logger = logging.getLogger(__name__)

# TODO: Set logger format
# TODO: Read config from /etc/pgf.conf


def attempt_gpg_encryption(message: str, recipient: str) -> Optional[str]:
    """Encrypt a message and return the encrypted message."""
    encrypted_message = None

    try:
        with subprocess.Popen(
            [
                "gpg",
                "-ea",
                "--no-auto-key-locate",  # Do not search key servers
                "--always-trust",  # Trust already-installed keys
                "--homedir",
                GPG_HOMEDIR,
                "-r",
                recipient,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ) as gpg_process:
            output_text, error_text = gpg_process.communicate(message)
            if "No public key" not in error_text:
                encrypted_message = output_text
    except OSError as err:
        logger.warning("Unable to execute gpg: %s", err)

    return encrypted_message


def send_mail(mail: EmailMessage, payload: str, recipient: str) -> None:
    """Send an mail with the body encrypted, if possible."""
    recipient_mail = copy.deepcopy(mail)

    recipient_mail.replace_header("To", recipient)

    encrypted_payload = attempt_gpg_encryption(payload, recipient)

    if encrypted_payload:
        recipient_mail.set_content(encrypted_payload)
        logger.info("Sending GPG-encrypted message to (%s).", recipient)
    else:
        recipient_mail.set_content(payload)
        logger.info("Sending plaintext message to (%s).", recipient)

    with SMTP(HOST, PORT) as smtp:
        if USE_STARTTLS:
            smtp.starttls()
        smtp.send_message(recipient_mail)
        smtp.quit()


def main() -> None:
    """Called when the program is started."""
    if len(sys.argv) < 2:
        logger.warning("Missing email recipients.")
        sys.exit(1)

    content = sys.stdin.read()

    message = Parser(policy=email.policy.SMTP).parsestr(content)

    mail = EmailMessage()

    for header, value in message.items():
        mail[header] = value

    payload = message.get_payload()

    recipients = sys.argv[1:]

    if (RECIPIENT_OVERRIDE is not None) and (RECIPIENT_OVERRIDE != ""):
        logger.info(
            "Overriding recipients (%s) with (%s).",
            ", ".join(recipients),
            RECIPIENT_OVERRIDE,
        )
        send_mail(mail, payload, RECIPIENT_OVERRIDE)
    else:
        for recipient in recipients:
            send_mail(mail, payload, recipient)

    sys.exit(0)


if __name__ == "__main__":
    main()
