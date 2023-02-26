#!/bin/sh

set -o xtrace

deluser pgf
rm -r /var/lib/pgf

cp /etc/postfix/master.cf /etc/postfix/master.cf.bak
cp /etc/postfix/main.cf /etc/postfix/main.cf.bak

perl -0777 -pe 's/# ADDED_BY_PGF.+# END_ADDED_BY_PGF//s' </etc/postfix/master.cf.bak >/etc/postfix/master.cf
perl -0777 -pe 's/# ADDED_BY_PGF.+# END_ADDED_BY_PGF//s' </etc/postfix/main.cf.bak >/etc/postfix/main.cf

rm /usr/local/bin/pgf

set +o xtrace

cat <<'DONE_TEXT'
pgf removed.

Please inspect these files:
    /etc/postfix/master.cf    (original saved to: /etc/postfix/master.cf.bak)
    /etc/postfix/main.cf      (original saved to: /etc/postfix/main.cf.bak)
and then restart Postfix.

Optional additional post-installation tasks:
    rm /etc/pgf.conf
    rm /var/log/pgf.log
DONE_TEXT
