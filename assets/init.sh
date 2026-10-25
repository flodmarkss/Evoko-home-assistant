#!/bin/sh
# Evoko Naso reference: local disk kiosk, independent of the development PC.
export PATH=/bin
B=/bin/busybox
$B mount -t devtmpfs devtmpfs /dev 2>/dev/null
$B mount -t proc proc /proc 2>/dev/null
$B mount -t sysfs sysfs /sys 2>/dev/null
$B mkdir -p /tmp /run /mnt/naso-data
$B ip link set lo up
exec >/dev/console 2>&1
echo NASO_NATIVE_DISK_INIT_V2
printf 'NASO_NATIVE_DISK_INIT_V2\n' >/run/naso-boot-marker
for p in /sys/class/backlight/*; do
 [ -f "$p/max_brightness" ] || continue
 max=$($B cat "$p/max_brightness")
 case "$max" in ''|*[!0-9]*) continue;; esac
 echo "$max" > "$p/brightness"
 [ -f "$p/bl_power" ] && echo 0 > "$p/bl_power"
done
/bin/naso_control &
control=$!
echo -900 >/proc/$control/oom_score_adj
for p in /sys/class/net/eth* /sys/class/net/en*; do
 [ -d "$p" ] || continue
 iface=${p##*/}
 $B ip link set "$iface" up
 $B udhcpc -f -t 4 -T 3 -A 10 -i "$iface" -s /dhcp-native.sh >>/tmp/dhcp.log 2>&1 &
done
R=/mnt/naso-data/naso-linux/root
while [ ! -b /dev/mmcblk2p4 ]; do $B sleep 1; done
if $B mount -t ext4 -o rw,noatime,nosuid,nodev /dev/mmcblk2p4 /mnt/naso-data; then
 if [ -x "$R/usr/local/sbin/naso-kiosk" ]; then
  $B mkdir -p "$R/dev" "$R/proc" "$R/sys" "$R/tmp" "$R/run"
  $B mount -o bind /dev "$R/dev"
  $B mount -t proc proc "$R/proc"
  $B mount -t sysfs -o ro sysfs "$R/sys"
  $B mount -t tmpfs -o size=32m,mode=1777 tmpfs "$R/tmp"
  $B mount -t tmpfs -o size=8m,mode=755 tmpfs "$R/run"
  [ -f /etc/resolv.conf ] && $B cp /etc/resolv.conf "$R/etc/resolv.conf"
  $B chroot "$R" /usr/local/sbin/naso-kiosk &
  kiosk=$!
  echo "LOCAL_KIOSK_SUPERVISOR=$kiosk"
 else echo 'ERROR: local kiosk files missing; control remains available'; fi
else echo 'ERROR: data mount failed; control remains available'; fi
while :; do
 if ! kill -0 "$control" 2>/dev/null; then /bin/naso_control & control=$!; echo -900 >/proc/$control/oom_score_adj; fi
 if [ -n "$kiosk" ] && ! kill -0 "$kiosk" 2>/dev/null; then $B chroot "$R" /usr/local/sbin/naso-kiosk & kiosk=$!; fi
 $B sleep 5
done
