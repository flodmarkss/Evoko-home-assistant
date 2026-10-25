#!/bin/sh
export PATH=/bin
B=/bin/busybox
case "$1" in
 deconfig) $B ifconfig "$interface" 0.0.0.0;;
 bound|renew)
  $B ifconfig "$interface" "$ip" netmask "${subnet:-255.255.255.0}" up
  $B route del default dev "$interface" 2>/dev/null
  for gw in $router; do $B route add default gw "$gw" dev "$interface"; break; done
  $B mkdir -p /etc
  : >/etc/resolv.conf
  for ns in $dns; do echo "nameserver $ns" >>/etc/resolv.conf; done
  R=/mnt/naso-data/naso-linux/root
  [ -d "$R/run/naso" ] && $B cp /etc/resolv.conf "$R/etc/resolv.conf"
  echo "LEASE interface=$interface ip=$ip subnet=$subnet router=$router"
  ;;
esac
exit 0
