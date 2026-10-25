#!/bin/sh
export PATH=/usr/sbin:/usr/bin:/sbin:/bin DISPLAY=:0
export QT_QPA_PLATFORM=xcb QT_XCB_GL_INTEGRATION=none QT_STYLE_OVERRIDE=Fusion
export XDG_RUNTIME_DIR=/tmp/runtime-root
umask 077
mkdir -p /run/naso /tmp/runtime-root
pid=$(cat /run/naso/wifi-ui.pid 2>/dev/null)
if [ "$1" = --close ]; then
 if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
  case "$(readlink /proc/$pid/exe)" in */wpa_gui) kill "$pid";; esac
 fi
 exit 0
fi
if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
 case "$(readlink /proc/$pid/exe)" in */wpa_gui)
  for w in $(xdotool search --class wpa_gui 2>/dev/null); do xdotool windowmap "$w" windowraise "$w" windowfocus "$w"; done
  exit 0
 ;; esac
fi
wpa_gui -i wlan0 -p /run/naso/wpa -stylesheet /etc/naso-wifi.qss >/run/naso/wifi-ui.log 2>&1 </dev/null &
pid=$!
echo "$pid" >/run/naso/wifi-ui.pid
# No desktop window manager is used; fit the main window above the keyboard.
n=0
while kill -0 "$pid" 2>/dev/null && [ "$n" -lt 30 ]; do
 for w in $(xdotool search --onlyvisible --pid "$pid" --name wpa_gui 2>/dev/null); do
  xdotool windowmove "$w" 0 0 windowsize "$w" 1024 508 windowraise "$w" windowfocus "$w"
  exit 0
 done
 n=$((n+1))
 sleep 0.3
done
