#!/bin/sh
# Local Wi-Fi service. Does not associate until a profile is saved from wpa_gui.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
umask 077
mkdir -p /run/naso /run/naso/wpa /etc/wpa_supplicant
existing=$(cat /run/naso/wifi-service.pid 2>/dev/null)
if [ -n "$existing" ] && kill -0 "$existing" 2>/dev/null && grep -q naso-wifi-service /proc/$existing/cmdline 2>/dev/null; then exit 0; fi
echo $$ >/run/naso/wifi-service.pid
FW=/proc/1/root/lib/firmware/rtw88
mkdir -p "$FW"
if ! cmp -s /lib/firmware/rtw88/rtw8723d_fw.bin "$FW/rtw8723d_fw.bin"; then cp /lib/firmware/rtw88/rtw8723d_fw.bin "$FW/rtw8723d_fw.bin" || exit 1; fi
for m in rtw_core rtw_usb rtw_8723d rtw_8723du; do
 if [ ! -d /sys/module/$m ]; then insmod /lib/modules/6.1.60/extra/$m.ko || exit 1; fi
done
while [ ! -d /sys/class/net/wlan0 ]; do sleep 1; done
CONF=/etc/wpa_supplicant/naso.conf
if [ ! -e "$CONF" ]; then
 printf 'ctrl_interface=/run/naso/wpa\nupdate_config=1\nap_scan=1\n' >"$CONF"
fi
chmod 700 /etc/wpa_supplicant /run/naso/wpa
chmod 600 "$CONF"
# Prefer the panel's own OEM MAC, rather than the driver's generated fallback.
if ! wpa_cli -p /run/naso/wpa -i wlan0 ping 2>/dev/null | grep -q PONG; then
 mac=
 for item in $(cat /proc/cmdline); do case "$item" in androidboot.wifimacaddr=*) mac=${item#*=};; esac; done
 if printf '%s\n' "$mac" | grep -qE '^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$'; then
  ip link set wlan0 down
  ip link set dev wlan0 address "$mac" || exit 1
 fi
fi
ip link set wlan0 up
# Kernel route selection then skips dead Ethernet routes when the cable is removed.
for dev in eth0 wlan0; do
 p=/proc/sys/net/ipv4/conf/$dev/ignore_routes_with_linkdown
 [ ! -w "$p" ] || echo 1 >"$p"
done
dns_wifi=0
while :; do
 if ! wpa_cli -p /run/naso/wpa -i wlan0 ping 2>/dev/null | grep -q PONG; then
  wpa_supplicant -B -D nl80211 -i wlan0 -c "$CONF" -P /run/naso/wpa.pid >>/run/naso/wpa.log 2>&1
 fi
 dp=$(cat /run/naso/wifi-dhcp.pid 2>/dev/null)
 if [ -z "$dp" ] || ! kill -0 "$dp" 2>/dev/null || ! grep -q udhcpc /proc/$dp/cmdline 2>/dev/null; then
  /bin/busybox udhcpc -f -i wlan0 -t 4 -T 3 -A 10 -s /usr/local/sbin/naso-wifi-dhcp -p /run/naso/wifi-dhcp.pid >>/run/naso/wifi-dhcp.log 2>&1 &
 fi
 eth=$(cat /sys/class/net/eth0/carrier 2>/dev/null)
 if [ "$eth" = 1 ]; then
  if [ "$dns_wifi" = 1 ] && [ -s /run/naso/ethernet-resolv.conf ]; then cp /run/naso/ethernet-resolv.conf /etc/resolv.conf; dns_wifi=0; fi
  cp /etc/resolv.conf /run/naso/ethernet-resolv.conf
 elif [ -s /run/naso/wifi-resolv.conf ]; then
  if ! cmp -s /run/naso/wifi-resolv.conf /etc/resolv.conf; then cp /run/naso/wifi-resolv.conf /etc/resolv.conf; fi
  dns_wifi=1
 fi
 if [ -d /proc/1/root/etc ] && ! cmp -s /etc/resolv.conf /proc/1/root/etc/resolv.conf; then cp /etc/resolv.conf /proc/1/root/etc/resolv.conf; fi
 sleep 3
done
