# Installation: Evoko Naso → fristående Linux/HA

Detta är en teknisk installationsguide för ägare av en kompatibel panel. Den fungerande referenslösningen använder original U-Boot, Linux 6.1.60, liten RAM-init och Alpine/Firefox på eMMC. Den publika byggvägen nedan bygger en **ny** rot och startbild; den behöver verifieras i RAM på målpanelen. Den är inte en färdig universalflash.

## 1. Inventera och samla material

- Bekräfta fysisk modell/kortrevision, SoC, RAM, LCD och touch. Referensen är Naso ENX1001, i.MX6 DualLite, ARMv7, 512 MB, 1024×768, FT5x06. En Liso är inte samma mål.
- Python 3, Zig 0.14.1, Android platform-tools/Fastboot, USB och stabil PoE samt LAN. På Windows används PowerShell. Ha plats för panelens hela eMMC-backup och flera GB byggfiler.
- Docker buildx med `linux/arm/v7`-stöd eller motsvarande ARMv7-byggmaskin. Windows Docker Desktop kräver normalt Linux-containers/WSL2.
- Skaffa firmware **144 / `92.zip`** lokalt från leverantören. [Biamp dokumenterar nedladdningsadressen](https://support.biamp.com/Evoko/z_Evoko_Workplace/Server-Migration_Follow-Up_Guide/Step_6_-_Updating_a_Configured_Naso_Device_from_v1_0_to_v2_0): `https://downloads.evoko.se/naso/firmware/92.zip`. Hämta filen på datorn; använd **inte** panelens Update/Install-knapp. Leverantören kan ersätta filen, därför accepterar verktyget enbart följande historiskt granskade SHA256:

```text
f87e902138850f8ac2fcaef5bc8f3534ddfbfcda8f758833f336ef628a4e15a1
```

Om digesten skiljer: stoppa och analysera den nya filen, stäng inte av kontrollen. Firmwarepaketets återställningsskript kan kasta hela eMMC, formatera och byta bootloader. Inget sådant får köras för den här installationen.

Klona/ladda ned detta repo till en egen mapp. Alla `private-build/`- och `vendor/`-filer stannar lokalt och är gitignorerade. Platshållarna i exemplen ska ersättas med dina värden; de är inte direkt körbara adresser.

## 2. Extrahera och bygg privat RAM-räddningsbild

```powershell
python tools/extract_firmware.py --firmware C:/Downloads/92.zip --out vendor/fw144 --seven-zip "C:/Program Files/7-Zip/7z.exe"
python tools/build_images.py --zig C:/Tools/zig/zig.exe --base-image vendor/fw144/recovery.img --out private-build --mode rescue --ha-ip YOUR_HA_IPV4
```

7-Zip behövs för Wi-Fi-filerna i SquashFS. Utan `--seven-zip` extraheras bara grundmaterialet; komplettera Wi-Fi senare. Kontrollera att 7-Zip stöder SquashFS. Firmwareverktyget skriver endast i den **nya lokala utmappen** och kör inga leverantörsskript.

Byggaren skapar en slumpad `control-key.txt`, statisk ARM-kontrollserver och `ha-proxy-arm` för **din** HA IPv4-adress, TCP 8123. Behåll nyckeln i samma privata utmapp vid senare `installed`-bygge. Dela aldrig genererade bilder: de innehåller kontrollnyckeln.

Den historiskt testade V6-grundbilden accepteras också om den redan finns privat från tidigare projektöverlämning. Den är inte med i det här repot. Den nya leverantörsbaserade vägen behåller samma verifierade kärna/DTB men använder firmware-recoveryns komprimerade initramfs med nytt `/init`-överlägg. Leverantörens init körs inte; rescue-init monterar inga eMMC-partitioner. Det är en **ny RAM-variant**, inte bevisat identisk med tidigare V6. Kontrollera ny initmarkör och verklig start innan du går vidare.

## 3. Fastboot och RAM-test

På referenskortet ger **SW600** vid återanslutning av PoE, med USB anslutet, Fastboot. SW601 gav ett annat ROM/SDP-läge. Förväxla inte detta med en generell fabriksåterställning. Kontrollera korrekt fysisk knapp för ditt kort och avbryt vid osäkerhet; använd inga reset/update-menyer på chans.

```powershell
fastboot devices
fastboot -s YOUR_SERIAL getvar product
fastboot -s YOUR_SERIAL getvar version-bootloader
fastboot -s YOUR_SERIAL getvar secure
fastboot -s YOUR_SERIAL getvar unlocked
fastboot -s YOUR_SERIAL boot private-build/naso-rescue.img
```

`boot` laddar till RAM. Kör inte `flash`, `erase`, `unlock` eller updater här. `OKAY` bevisar överföring, inte start. Hitta panelens DHCP-adress i din router. Skriv ett LF-skript `private-build/probe.sh`:

```sh
B=/bin/busybox
$B uname -a
$B cat /proc/cmdline /run/naso-boot-marker /proc/sys/kernel/random/boot_id
$B cat /proc/partitions /proc/mounts
$B ip addr
$B ip route
for p in /sys/block/mmcblk*; do
 echo "$p"; $B cat "$p/size" "$p/device/cid" 2>/dev/null
done
echo PROBE_COMPLETE
```

```powershell
python tools/control_client.py --host YOUR_PANEL_IPV4 --key-file private-build/control-key.txt --script private-build/probe.sh
```

Kräv korrekt serienummer/CID, `NASO_RESCUE_RAM_ONLY_V1`, kärna, ny boot-id och slutmarkör. Kontrollkanalen är autentiserad men okrypterad root-HTTP på TCP 8089, endast för betrott LAN. HTTP 200 är inte samma sak som lyckat skalkommando. Om panelen inte svarar: spara resultat och analysera USB/start, upprepa inte oförändrade tester blint.

## 4. Originalbackup före varje beständig installation

Ingen originalpartition ska vara monterad skrivbart. Identifiera rätt eMMC och dess separata boot0/boot1, storlek i 512-bytessektorer, CID och partitionskarta från **den egna panelen**. Spara hela användarområdet och boot0/boot1 privat, samt separata original-boot/recoverypartitioner. Det är inte tillräckligt att kopiera projektägarens backup.

`tools/backup.py` inventerar vald eMMC, vägrar om någon av dess partitioner är monterad, läser användarområde/boot0/boot1 och jämför käll-SHA256 före/efter mot lokal digest:

```powershell
python tools/backup.py --host YOUR_PANEL_IPV4 --key-file private-build/control-key.txt --serial YOUR_SERIAL --cid YOUR_CID --device YOUR_MMC_BASENAME --out private-build/original-backup
```

Exempel på basnamn är `mmcblk2`; det är **inte** en universell konstant. Verktyget skriver inga panelpartitioner och vägrar en redan befintlig utmapp. Detta generiska backupverktyg är offline-testat, inte kört mot din panel. Verifiera dess rapport själv och spara en extra kopia innan du fortsätter. Hämta partitionskartan med ett lämpligt läsverktyg och dokumentera startsektor/storlek; backupverktygets sysfs-inventering ersätter inte en tolkad MBR/GPT-karta.

## 5. Bygg en ren ARMv7-användarmiljö

Från repots rot på en dator med fungerande buildx/ARMv7-emulering:

```powershell
docker buildx build --platform linux/arm/v7 --output type=local,dest=private-build/rootfs -f Dockerfile .
python tools/prepare_root.py --root private-build/rootfs --build private-build --wifi-files vendor/fw144/wifi
```

Utelämna `--wifi-files` för en Ethernet-installation; den lokala Wi-Fi-tjänsten parkeras då. Dockerfilen hämtar signerade Alpine-paket, bygger knappar/dimningsdaemon och komprimerar Firefox-resurser. Den kopierar **inte** en befintlig webbläsarprofil. Endast `user.js` skapas i `/var/lib/naso/firefox`. `prepare_root.py` vägrar annan befintlig profilstate. Första HA-besöket ger den nya ägarens inloggning. Dela inga inloggningsfiler mellan paneler.

Alpine 3.24 är referensgrenen. Paketversioner kan ändras och den rena publika Docker-roten är inte bitidentisk med historiska roten. Om ett paket försvinner/byter namn: granska Alpine-recepten, kringgå inte signaturkontroll. GUI/Touch/fullskärm/HA måste provas från den faktiska nya roten.

Standardtidszon Stockholm kan bytas till din zon innan arkivering. Dimkonfigurationen är 5%/60 sekunder, med referensens 14/11-trösklar; kalibrera sensorn på nytt exemplar.

Arkivera med ett Linux-tar som bevarar symlänkar och Unix-moder (WSL/Linux), **inte** Windows ZIP. Gör detta i en offline byggrot, aldrig genom att exportera en redan inloggad panel:

```sh
tar -czf private-build/rootfs.tar.gz -C private-build/rootfs .
sha256sum private-build/rootfs.tar.gz
```

Windows-utmatning via `>` kan i äldre PowerShell koda om binärer; använd WSL/Linux för arkivöverföring eller ett binärt filkopieringsverktyg. Behåll mode 755 på `/usr/local/sbin/naso-*`, 700 på profilkatalogen, 1777 på `/tmp`.

## 6. Lägg roten i en ny mapp på befintlig datapartition

Det här steget skriver beständigt på panelen. Fortsätt först efter verifierad egen backup, rätt mål och lyckad RAM-start. Välj och kontrollera en befintlig ext4-datapartition med ledigt utrymme. Montera först läsande med `ro,noload` för inventering; kör eventuell `e2fsck -fn` enbart omonterat och reparera inte automatiskt.

Referensen hade data på p4, boot på p1 (16 MiB) och recovery på p2. Dessa värden är exempel, inte instruktioner att använda utan inventering. Ingen formatering eller ompartitionering behövs.

För den verifierade datapartitionen, efter uttryckligt installationsbeslut:

1. Montera på `/mnt/naso-data` med `rw,noatime,nosuid,nodev`.
2. Kräv att `/mnt/naso-data/naso-linux` **inte finns**. Skapa ny katalog mode 700 och dess `root`.
3. Överför det rena rootarkivet, jämför panelens SHA256 med datorns, extrahera med fullständigt `tar`/`gzip` i den nya roten. Använd inte ett beskuret BusyBox-tar utan att kontrollera stöd. `tools/upload_ram_file.py` kan överföra små bootstrap-hjälpfiler till `/tmp/naso-bootstrap`, aldrig direkt till eMMC. Du kan exportera Alpine BusyBox och dess musl-loader från din rena rot för en RAM-bootstrap; använd inte främmande arkitektur/ABI.
4. Kontrollera kritiska binärers hash och att profilen fortfarande bara innehåller `user.js` före första körningen. **Kopiera ingen gammal profilsession.**
5. Bindmontera `/dev`, montera `proc` och skrivskyddat `sysfs` i roten. Montera tmpfs på rotens `/tmp` (32 MiB, mode 1777) och `/run` (8 MiB). Kopiera aktuell DNS till rotens `/etc/resolv.conf`. Sätt `lo` UP.
6. Starta `busybox chroot /mnt/naso-data/naso-linux/root /usr/local/sbin/naso-kiosk` från RAM-miljön. Se `assets/init.sh` för exakt ordning. Kontrollera paketens ARMv7-loader och saknade bibliotek om start misslyckas.

Det här repot har avsiktligt ingen blind fjärrinstallerare eller diskformatterare. Anpassa transport och dessa lagringssteg till den inventerade panelen och verifiera kommandonas slutmarkörer. Låt en tekniskt kunnig operatör/AI läsa `AGENTS.md` och utföra planen; gissa inte blockmål.

## 7. Bevisa fristående drift från disk före bootändring

Logga in med **ditt eget HA-konto på din egen server**. Kontrollera fullskärm, dark mode, pekning, tangentbord, Wi-Fi-rutan, NTP och sensordimning. Byt flera dashboards och läs OOM-logg/`MemAvailable`; referensen klarade nio byten per testserie. Kontrollera att Firefox/biblioteken ligger på eMMC. Stoppa eventuell gammal PC-rendering; den ska inte behövas.

Prova automatisk Firefox-återstart. Prova verklig Wi-Fi-anslutning och DHCP med egna uppgifter om det ska användas; scanning och profil-lagring bevisar inte radioanslutning. Spara aldrig lösenord i publik diagnostik. Gå inte vidare om nya Docker-roten eller RAM-varianten ännu inte fungerar.

## 8. Normal start från vald bootpartition

Bygg `installed` med **samma privata nyckelutkatalog**, samma grundbild och din verifierade datapartition:

```powershell
python tools/build_images.py --zig C:/Tools/zig/zig.exe --base-image vendor/fw144/recovery.img --out private-build --mode installed --data-partition YOUR_DATA_PARTITION_BASENAME --ha-ip YOUR_HA_IPV4
```

Exempel på databasnamn är `mmcblk2p4`. RAM-boota den nya installed-bilden först och bekräfta samma diskroot/startkedja. Installerat läge monterar data rw, så detta är inte längre ett helt skrivfritt rescue-test.

Utred din faktiska bootloaders MMC-startväg och partitionsmappning. `secure:yes`, `unlocked:no` och fungerande RAM-boot räcker inte som bevis. Referensens original U-Boot accepterade normal start utan bootloaderbyte; det fastställer inte beteendet på andra builds.

Före varje skrivning till boot:

- Spara den egna original-bootpartitionen även i Linux-mappen för återställning.
- Bekräfta serienummer, CID, partitionens startsektor och exakta storlek samt **aktuell original-SHA256** direkt före skrivning.
- Kontrollera att bilden ryms; bestäm exakt utfyllnad till hela partitionens längd och beräkna dess SHA256 lokalt.
- Skriv **endast** den verifierade bootpartitionen. Skriv inte hela eMMC, recovery, MBR/GPT, boot0/boot1 eller U-Boot.
- Synka, läs tillbaka exakt hela målpartitionen och kräv SHA256 mot avsedd bild+utfyllnad. Kontrollera bevarade områden mot egna originalhashar.

Ett generellt `dd of=/dev/mmcblk...` ges inte här: fel mål är inte ett återställbart GUI-misstag. Dokumentera din exakta verifierade skrivplan och kör först när samtliga kontroller är uppfyllda. Referensens originalmål var p1 vid sektor 16384, 16 MiB; det är historisk information, inte en standardinställning.

## 9. Omstart, acceptans och återställning

Minimal init är inte systemd. Planera ett kontrollerat stopp av övervakare/Firefox, synka och avmontera data innan programstyrd omstart; övervakare kan annars starta om stoppade tjänster. Anta inte att ett generellt Linux shutdown-kommando gör detta på din init.

Kräv nytt boot-id, `NASO_NATIVE_DISK_INIT_V2`, samma verifierade diskrot och lokal kiosk utan ny USB/RAM-laddning eller PC-rendering. Testa dashboardbyten och services återstart igen. Prova fysisk PoE-kallstart separat med fysisk operatör; programstyrd omstart bevisar inte kallstart.

Om något går fel: inventera LAN/USB och RAM-boota din egna räddningsbild med egen nyckel. Återställ i första hand **din panels egen original-bootpartition**, med samma identitets-/storleks-/hashskydd och återläsning. Linux-mappen kan lämnas kvar. Återställ inte hela eMMC om bootåterställning räcker, och använd aldrig en annan panels boot0/boot1/fullbackup.

Slutrapportera vad som faktiskt provats: identitet, backupdigester, ändrade områden, byggmanifest, RAM/normalboot/kallstart, HA-login, dashboardstress, minnesmarginal, touch/keyboard/Wi-Fi och återställningsväg. Allt annat märks oprövat.
