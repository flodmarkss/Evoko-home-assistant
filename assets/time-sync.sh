#!/bin/sh
# Run inside the installed Alpine root; kernel time is shared with outer Linux.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
mkdir -p /run/naso /var/lib/naso
echo $$ > /run/naso/timekeeper.pid
now=$(date -u +%s)
if [ "$now" -lt 1577836800 ] && [ -r /var/lib/naso/last-good-utc ]; then
 saved=$(cat /var/lib/naso/last-good-utc)
 case "$saved" in ''|*[!0-9]*) ;; *)
  [ "$saved" -ge 1577836800 ] && date -u -s "@$saved"
 ;; esac
fi
while :; do
 /bin/busybox ntpd -n -S /usr/local/sbin/naso-time-event -p 0.se.pool.ntp.org -p 1.se.pool.ntp.org
 sleep 15
done
