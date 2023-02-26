#!/usr/bin/env python3

"""Postfix content filter for encrypting outgoing messages with GPG."""

import configparser
import copy
import email.policy
import logging
import subprocess
import sys
from email.message import EmailMessage
from email.parser import Parser
from smtplib import SMTP
from typing import Optional


CONFIG_FILE = "/etc/pgf.conf"
EXIT_BAD_CONFIG = 1
EXIT_MISSING_RECIPIENTS = 2


class Pgf:
    """Postfix content filter for encrypting outgoing messages with GPG."""

    host: str = "localhost"
    port: int = 10026
    use_starttls: bool = False
    log_file: str = "/var/log/pgf.log"
    gpg_homedir: str = "/var/lib/pgf"
    recipient_override: Optional[str] = None
    logger: logging.Logger = logging.getLogger(__name__)

    def init_logger(self) -> None:
        """Initialize logging."""
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)-8s] %(message)s", datefmt="%Y-%m-%dT%H:%M:%S%z"
        )

        handler = logging.FileHandler(self.log_file)
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)

    def read_config(self) -> None:
        """Read the configuration file and initialize logging."""
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        if "log_file" in config["pgf"]:
            self.log_file = config["pgf"]["log_file"]

        self.init_logger()

        for str_key in ["host", "gpg_homedir", "recipient_override"]:
            if str_key in config["pgf"]:
                setattr(self, str_key, config["pgf"][str_key])

        if "port" in config["pgf"]:
            try:
                self.port = int(config["pgf"]["port"])
            except ValueError:
                self.logger.error(
                    "Bad configuration: Invalid port '%s'", config["pgf"]["port"]
                )
                sys.exit(EXIT_BAD_CONFIG)

        if "use_starttls" in config["pgf"]:
            self.use_starttls = config.getboolean("pgf", "use_starttls")

    def attempt_gpg_encryption(self, message: str, recipient: str) -> Optional[str]:
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
                    self.gpg_homedir,
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
            self.logger.warning("Unable to execute gpg: %s", err)

        return encrypted_message

    def send_mail(self, mail: EmailMessage, payload: str, recipient: str) -> None:
        """Send an mail with the body encrypted, if possible."""
        recipient_mail = copy.deepcopy(mail)

        recipient_mail.replace_header("To", recipient)

        encrypted_payload = self.attempt_gpg_encryption(payload, recipient)

        if encrypted_payload:
            recipient_mail.set_content(encrypted_payload)
            self.logger.info("Sending GPG-encrypted message to (%s).", recipient)
        else:
            recipient_mail.set_content(payload)
            self.logger.info("Sending plaintext message to (%s).", recipient)

        try:
            with SMTP(self.host, self.port) as smtp:
                if self.use_starttls:
                    smtp.starttls()
                smtp.send_message(recipient_mail)
                smtp.quit()
        except ConnectionRefusedError:
            self.logger.error(
                "Unable to connect to SMTP server at %s:%i.", self.host, self.port
            )

    def main(self) -> None:
        """Called when the program is started."""
        self.read_config()

        if len(sys.argv) < 2:
            self.logger.warning("Unable to send mail - missing email recipients.")
            sys.exit(EXIT_MISSING_RECIPIENTS)

        content = sys.stdin.read()

        message = Parser(policy=email.policy.SMTP).parsestr(content)

        mail = EmailMessage()

        for header, value in message.items():
            mail[header] = value

        payload = message.get_payload()

        recipients = sys.argv[1:]

        if (self.recipient_override is not None) and (self.recipient_override != ""):
            original_recipients = ", ".join(recipients)

            original_recipients_note = (
                f"Original recipients ({original_recipients}) "
                f"overridden to ({self.recipient_override})."
            )

            self.logger.info("%s", original_recipients_note)

            payload = f"{original_recipients_note}\n\n" f"{payload}"

            self.send_mail(mail, payload, self.recipient_override)
        else:
            for recipient in recipients:
                self.send_mail(mail, payload, recipient)

        sys.exit(0)


if __name__ == "__main__":
    pgf = Pgf()
    pgf.main()
