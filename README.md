# pgf: Postfix GPG filter

This is a Postfix filter that encrypts outgoing mail with GPG if the recipient's
key is known. (Note: `pgf` does not search key servers.)

You can redirect all emails to a single address by setting `RECIPIENT_OVERRIDE`
in the configuration file.



## Requirements
- Python 3
- gpg



## Installation
```bash
git clone https://github.com/atomicparade/pgf.git
cd pgf
sudo ./install.sh
sudo service postfix restart  # (or the equivalent on your platform)

# Install the recipients' SSH keys for pgf
sudo -u pgf gpg --homedir /var/lib/pgf --search-keys USER@DOMAIN.COM
```

This script:

1. Creates a system user named `pgf`
2. Creates a directory at `/var/lib/pgf` for storing GPG keys
3. Creates a log file at `/var/log/pgf.log`
4. Copies `pgf.py` to `/usr/local/bin/pgf`
5. Copies `pgf.conf` to `/etc/pgf.conf`
6. Adds configuration for pgf to `/etc/postfix/master.cf` and `/etc/postfix/main.cf`



## Configuration
Configuration is stored at `/etc/pgf.conf`.

Key                     | Default               | Notes
------------------------|-----------------------|-------------------------------
`LOG_FILE`              | `/var/log/pgf.log`    | Where `pgf` should log to
`HOST`                  | `localhost`           | Where to direct outgoing emails
`PORT`                  | `10026`               | The port where Postfix is listening for already-filtered mail
`USE_STARTTLS`          | `FALSE`               | Whether or not to use STARTTLS (set to `TRUE` to enable)
`GPG_HOMEDIR`           | `/var/lib/pgf`        | Where GPG keys are stored for `pgf`
`RECIPIENT_OVERRIDE`    | (none)                | If set, all emails will be redirected to `RECIPIENT_OVERRIDE` and will NOT be sent to the original recipients



## Removal
The uninstallation script will undo everything that the installation script does
except remove `/etc/pgf.conf` and `/var/log/pgf.log`.

```bash
sudo ./uninstall_pgf.sh
sudo service postfix restart  # (or the equivalent on your platform)
```
