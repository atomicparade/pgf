#!/bin/sh

set -e # Exit if any command fails
set -o xtrace

deluser pgf
rm -r /var/lib/pgf

echo "TODO: Remove PGF lines from master.cf, main.cf"

rm /usr/local/bin/pgf

set +o xtrace

echo "pgf removed. Please restart Postfix."
echo "Optional additional post-installation tasks:"
echo "    rm /etc/pgf.conf"
echo "    rm /var/log/pgf.log"
