#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
# BusyBox ntpd exports stratum to its step/stratum/periodic callback.
case "${stratum:-}" in [1-9]|1[0-5]) ;; *) exit 0;; esac
epoch=$(date -u +%s)
[ "$epoch" -ge 1577836800 ] || exit 0
mkdir -p /run/naso /var/lib/naso
date -u '+%Y-%m-%dT%H:%M:%SZ' > /run/naso/time-synchronized
printf '%s\n' "$epoch" > /var/lib/naso/last-good-utc.new
mv /var/lib/naso/last-good-utc.new /var/lib/naso/last-good-utc
printf 'NTP event=%s stratum=%s UTC=%s\n' "$1" "$stratum" "$(cat /run/naso/time-synchronized)" >> /run/naso/time-events.log
