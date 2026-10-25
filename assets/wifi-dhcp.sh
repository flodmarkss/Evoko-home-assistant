#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
[ "$interface" = wlan0 ] || exit 1
mkdir -p /run/naso
case "$1" in
 deconfig)
  ip -4 addr flush dev wlan0 scope global
  rm -f /run/naso/wifi-resolv.conf /run/naso/wifi-lease
 ;;
 bound|renew)
  ifconfig wlan0 "$ip" netmask "${subnet:-255.255.255.0}" up || exit 1
  gw=
  for item in $router; do gw=$item; break; done
  if [ -n "$gw" ]; then ip route replace default via "$gw" dev wlan0 metric 600; fi
  : >/run/naso/wifi-resolv.conf
  for ns in $dns; do printf 'nameserver %s\n' "$ns" >>/run/naso/wifi-resolv.conf; done
  printf 'IPv4=%s\n' "$ip" >/run/naso/wifi-lease
 ;;
esac
exit 0
