#!/system/bin/sh
# Monta y entra al chroot de Kali (ejecutar como root)
R=/data/local/nhsystem/kali-arm64
BB=/data/adb/magisk/busybox
m() { $BB mountpoint -q $R/$1 || $BB mount $2 $3 $R/$1; }
m proc "-t proc" proc
m sys "-t sysfs" sysfs
m dev "--bind" /dev
m dev/pts "-t devpts" devpts
m sdcard "--bind" /sdcard
$BB mkdir -p $R/dev/shm $R/tmp
m dev/shm "-t tmpfs" tmpfs
[ -f $R/etc/resolv.conf ] || true
echo "nameserver 1.1.1.1" > $R/etc/resolv.conf
echo "127.0.0.1 localhost kali" > $R/etc/hosts
# red de Android: permitir sockets a grupos de red
echo "aid_inet:x:3003:root" >> $R/etc/group 2>/dev/null
exec $BB chroot $R /usr/bin/env -i HOME=/root TERM=xterm-256color PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin /bin/bash -l "$@"
