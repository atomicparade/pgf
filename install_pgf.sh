#!/bin/sh

set -e # Exit if any command fails
set -o xtrace

adduser --system --no-create-home --disabled-login pgf

# Create directory for GPG
mkdir -p /var/lib/pgf
chmod 700 /var/lib/pgf
chown pgf: /var/lib/pgf

# Create log file
touch /var/log/pgf.log
chmod 600 /var/log/pgf.log
chown pgf: /var/log/pgf.log

# Copy program and configuration file
cp pgf.py /usr/local/bin/pgf
chmod 755 /usr/local/bin/pgf
cp pgf.conf /etc/pgf.conf

# Add pgf to postfix
cat >>/etc/postfix/master.cf <<'END_POSTFIX_MASTER_CF'

# ADDED_BY_PGF

# Note: Do not add additional configuration that is unrelated to pgf between
# ADDED_BY_PGF and END_ADDED_BY_PGF. These lines will be removed by the
# uninstallation script.
pgf       unix  -       n       n       -       10      pipe
    user=pgf argv=/usr/local/bin/pgf ${recipient}

localhost:10026 inet n  -       n       -       10      smtpd
    -o content_filter=
    -o receive_override_options=no_unknown_recipient_checks,no_header_body_checks,no_milters
    -o smtpd_helo_restrictions=
    -o smtpd_client_restrictions=
    -o smtpd_sender_restrictions=
    -o smtpd_recipient_restrictions=permit_mynetworks,reject
    -o mynetworks=127.0.0.0/8,[::1]/128
    -o smtpd_authorized_xforward_hosts=127.0.0.0/8,[::1]/128

# END_ADDED_BY_PGF
END_POSTFIX_MASTER_CF

cat >>/etc/postfix/main.cf <<'END_POSTFIX_MAIN_CF'

# ADDED_BY_PGF

# Note: Do not add additional configuration that is unrelated to pgf between
# ADDED_BY_PGF and END_ADDED_BY_PGF. These lines will be removed by the
# uninstallation script.
content_filter = pgf

# END_ADDED_BY_PGF
END_POSTFIX_MAIN_CF

set +o xtrace

echo "Installation complete."
echo "Please:"
echo "    1) Restart Postfix to load pgf as a content filter."
echo "    2) Install PGP keys for user pgf by running:"
echo "        sudo -u pgf gpg --homedir /var/lib/pgf --search-keys USER@DOMAIN.COM"
