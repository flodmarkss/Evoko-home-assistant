# Daglig användning / daily use

## Tangentbord och Wi-Fi

Tryck **ABC** nere till höger för att visa tangentbordet. Då syns **Wi-Fi** bredvid knappen. Tryck Wi-Fi för att öppna den lokala inställningsrutan ovanför tangentbordet:

1. **Scan**; tryck Scan i sökfönstret igen vid behov.
2. Dubbeltryck ditt **2,4 GHz**-nätverk.
3. Skriv lösenordet i **PSK**, välj **Add** (eller **Change** för en befintlig profil).
4. Välj **Connect** om anslutningen inte sker automatiskt. Kontrollera status och IP.
5. **HA** tar dig tillbaka till dashboarden utan att stoppa Wi-Fi-tjänsten.

**Manage Networks** visar sparade profiler och låter dig ändra eller ta bort dem. Profiler sparas privat i panelens `/etc/wpa_supplicant/naso.conf` och kan användas efter omstart. Dela aldrig filen offentligt. Riktig anslutning, DHCP och kabelbyte måste provas med ditt eget nätverk. Ethernet behåller högre ruttprioritet när kabeln är ansluten.

Internal radio on the reference board is USB `0bda:d723` RTL8723DU, 2.4 GHz only. Modules must match the exact 6.1.60 kernel ABI; never force-load a module. If Wi-Fi files were omitted from the build, use Ethernet and rebuild with verified matching firmware/modules before using the settings button.

For operation without Ethernet power, use a **Naso-compatible 5 V DC adapter** with the correct connector, polarity and rating. This project did not verify the exact plug/polarity/current, so do not guess or substitute a 12 V supply. [Biamp product information](https://www.biamp.com/products/product-families/evoko/evoko-naso).

## Dimning

`/etc/naso-dim.conf` uses 60 seconds and 5% by default. Full brightness returns on proximity or touch. This never deliberately writes brightness zero. Thresholds 14/11 were physically calibrated on the reference device; calibrate another device against its own `/sys/bus/iio/devices/iio:device0/in_proximity_raw`. Driver name may say `vcnl4000`, while the sensor is VCNL4200 at I²C 2-0051. Sensor-read failure restores full brightness.

## Klocka

Default timezone is `Europe/Stockholm`; change `/etc/localtime` and `/etc/timezone` in the offline root for your location. BusyBox NTP starts automatically; allow NTP on your LAN. `/var/lib/naso/last-good-utc` is a fallback floor for a panel without a working RTC, not proof of synchronization. Confirm epoch, timezone and NTP status after first boot.

## Login and restart

The new owner logs in on first access. The panel may retain that owner's login afterward. Supervisor restarts Firefox and the peripheral services. A power cut can still interrupt an eMMC write; this minimal init is not systemd and has no complete shutdown manager. Stop/sync/unmount cleanly when performing maintenance, as described in the installation guide.
