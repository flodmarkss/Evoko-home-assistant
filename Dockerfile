# syntax=docker/dockerfile:1
# Build on ARMv7 or with Docker buildx/QEMU support. Never COPY a live panel root.
FROM alpine:3.24 AS runtime
RUN apk add --no-cache alpine-base firefox-esr xorg-server xf86-video-fbdev \
    xf86-input-evdev xdotool xwininfo font-dejavu matchbox-keyboard \
    wpa_supplicant wpa_gui qt6-qtbase-x11 tzdata iw
COPY assets /src/assets
COPY sources /src/sources
RUN apk add --no-cache --virtual .build gcc musl-dev libx11-dev python3 && \
    cc -Os -s /src/sources/keyboard-toggle.c -lX11 -o /usr/local/sbin/naso-keyboard-toggle && \
    cc -Os -s -static /src/sources/auto-dim.c -o /usr/local/sbin/naso-auto-dim && \
    mkdir -p /etc/X11 /opt/naso /var/lib/naso/firefox /run/naso && \
    cp /src/assets/kiosk.sh /usr/local/sbin/naso-kiosk && \
    cp /src/assets/xorg.conf /etc/X11/naso-xorg.conf && \
    cp /src/assets/ha-launcher.html /opt/naso/ha-launcher.html && \
    cp /src/assets/firefox-user.js /var/lib/naso/firefox/user.js && \
    cp /src/assets/dim.conf /etc/naso-dim.conf && \
    cp /src/assets/wifi.qss /etc/naso-wifi.qss && \
    for s in wifi-service wifi-dhcp wifi-open time-sync time-event; do cp /src/assets/$s.sh /usr/local/sbin/naso-$s; done && \
    chmod 755 /usr/local/sbin/naso-* && chmod 700 /var/lib/naso/firefox && \
    cp /usr/share/zoneinfo/Europe/Stockholm /etc/localtime && \
    echo Europe/Stockholm >/etc/timezone && \
    python3 -c 'import pathlib,zipfile,os; files=list(pathlib.Path("/usr/lib/firefox-esr").rglob("omni.ja")); [(None) for p in []]; exec("for p in files:\n q=p.with_suffix(\".compressed\")\n with zipfile.ZipFile(p) as src, zipfile.ZipFile(q,\"w\",zipfile.ZIP_DEFLATED,compresslevel=9) as dst:\n  for i in src.infolist(): dst.writestr(i.filename,src.read(i.filename))\n with zipfile.ZipFile(q) as z: assert z.testzip() is None\n os.replace(q,p)")' && \
    apk del .build && rm -r /src && \
    test "$(find /var/lib/naso/firefox -type f | wc -l)" = 1
FROM scratch
COPY --from=runtime / /
