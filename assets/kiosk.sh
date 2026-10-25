#!/bin/sh
# The complete local kiosk runs from the data partition, without a PC renderer.
export PATH=/usr/sbin:/usr/bin:/sbin:/bin
export HOME=/var/lib/naso DISPLAY=:0 GDK_BACKEND=x11 MOZ_ENABLE_WAYLAND=0
export MOZ_FORCE_DISABLE_E10S=1 MOZ_DISABLE_NONLOCAL_CONNECTIONS=1 NO_AT_BRIDGE=1
export MOZ_USE_XINPUT2=1 XDG_RUNTIME_DIR=/tmp/runtime-root
mkdir -p /run/naso /var/log/naso /tmp/runtime-root
chmod 700 /tmp/runtime-root
echo $$ > /run/naso/kiosk.pid
exec >>/var/log/naso/kiosk.log 2>&1
echo "NATIVE_KIOSK_START $(cat /proc/uptime)"
alive(){ [ -n "$1" ] && kill -0 "$1" 2>/dev/null; }
xpid=; kpid=; tpid=; bpid=; ppid=; wifipid=; dimpid=; timepid=
while :; do
 if ! alive "$timepid"; then
  timepid=$(cat /run/naso/timekeeper.pid 2>/dev/null)
  if ! alive "$timepid" || ! grep -q naso-time-sync /proc/$timepid/cmdline 2>/dev/null; then
   /usr/local/sbin/naso-time-sync >>/run/naso/time-client.log 2>&1 & timepid=$!
  fi
 fi
 if ! alive "$dimpid"; then
  dimpid=$(cat /run/naso/dim.pid 2>/dev/null)
  if ! alive "$dimpid" || ! grep -q naso-auto-dim /proc/$dimpid/cmdline 2>/dev/null; then
   /usr/local/sbin/naso-auto-dim >>/run/naso/dim.log 2>&1 & dimpid=$!
   echo "$dimpid" > /run/naso/dim.pid
  fi
 fi
 if ! alive "$wifipid"; then
  wifipid=$(cat /run/naso/wifi-service.pid 2>/dev/null)
  if ! alive "$wifipid" || ! grep -q naso-wifi-service /proc/$wifipid/cmdline 2>/dev/null; then
   /usr/local/sbin/naso-wifi-service >>/run/naso/wifi-service.log 2>&1 & wifipid=$!
  fi
 fi
 if ! alive "$ppid"; then
  /usr/local/sbin/naso-ha-proxy >>/var/log/naso/proxy.log 2>&1 & ppid=$!
 fi
 if ! alive "$xpid"; then
  /bin/sh -c 'echo -500 > /proc/$$/oom_score_adj; exec /usr/libexec/Xorg :0 vt1 -novtswitch -nolisten tcp -extension GLX -s 0 -dpms -config /etc/X11/naso-xorg.conf -logfile /var/log/naso/Xorg.0.log' >>/var/log/naso/xorg-console.log 2>&1 & xpid=$!
  sleep 3
 fi
 if [ -S /tmp/.X11-unix/X0 ]; then
  if ! alive "$kpid"; then /usr/bin/matchbox-keyboard >>/var/log/naso/keyboard.log 2>&1 & kpid=$!; fi
  if ! alive "$tpid"; then /usr/local/sbin/naso-keyboard-toggle >>/var/log/naso/toggle.log 2>&1 & tpid=$!; fi
  if ! alive "$bpid" && /bin/busybox wget -q -T 3 -t 1 -O /dev/null http://127.0.0.1:8123/; then
   /usr/bin/firefox-esr --no-remote --profile /var/lib/naso/firefox --chrome file:///opt/naso/ha-launcher.html >>/var/log/naso/firefox.log 2>&1 & bpid=$!
   echo "BROWSER_START $bpid $(cat /proc/uptime)"
  fi
  for w in $(xdotool search --onlyvisible --class firefox-esr 2>/dev/null); do
   big=$(xwininfo -id "$w" 2>/dev/null | awk '/Width:/ {w=$2} /Height:/ {h=$2} END {if(w>100 && h>50)print 1}')
   [ "$big" = 1 ] && xdotool windowmove "$w" 0 0 windowsize "$w" 1024 768
  done
 fi
 printf '%s %s %s %s %s\n' "$xpid" "$bpid" "$kpid" "$tpid" "$ppid" > /run/naso/service-pids
 sleep 5
done
