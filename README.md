# Kali NetHunter en el Samsung Galaxy A04e (SM-A042M)

Guía y scripts para correr Kali NetHunter en el Galaxy A04e con [LineageOS 20 GSI ya instalado](https://github.com/Draxter32/samsung-a04e-lineageos-gsi). No existe imagen oficial de NetHunter para este modelo, así que se arma a mano: chroot de Kali + kernel propio con los drivers de NetHunter, conservando Magisk como root.

Probado en un SM-A042M real (región latam), kernel base `4.19.191-28581296-abA042MUBSDEYG1`.

## Qué incluye

- **Chroot de Kali** sobre el root de Magisk, sin tocar el sistema.
- **Kernel propio** compilado desde el código fuente de Samsung para este modelo, con los drivers que NetHunter necesita (USB gadget/HID, wifi USB externo), **sin romper los módulos de fábrica** (wifi/bluetooth/GPS del vendor, que exigen coincidencia exacta de versión y CRC).
- **App NetHunter + NetHunter Terminal** instaladas, con acceso directo a Kali desde un ícono.
- Verificación automática de que el kernel compilado no rompe los `.ko` del vendor, antes de flashear.

## Lo que NO funciona (limitaciones confirmadas, no son bugs a arreglar)

- **Metasploit sin base de datos persistente.** PostgreSQL necesita `SYSVIPC` del kernel, que tuvimos que desactivar porque cambia estructuras internas (`task_struct`) y rompe los módulos de wifi/bluetooth/GPS del vendor. Se probó forzar `shared_memory_type=mmap` en postgres: no alcanza, porque `PGSharedMemoryCreate()` en `sysv_shmem.c` siempre llama a `shmget()` para un segmento de control, sin importar la configuración. `msfconsole` funciona igual, solo no guarda hosts/workspaces entre sesiones.
- **Wifi en modo monitor:** el chip interno (MediaTek) no lo soporta. Se necesita un adaptador USB externo.
- **Adaptadores wifi USB de doble banda (RTL8812AU/RTL8821AU):** el puerto OTG del A04e no entrega suficiente corriente para el pico de encendido del chip. El driver carga bien (`insmod` ok, interfaz visible), pero falla al iniciar la radio (`_InitPowerOn_8812AU: run power on flow fail`). Hace falta un cable OTG con alimentación extra (cable en Y) o un hub USB alimentado. Con un adaptador de un solo radio (RTL8188/8192) es más probable que funcione sin alimentación extra.

## Estructura

```
nethunter.config          # fragmento de config del kernel con las opciones de NetHunter
build.sh                  # compila el kernel contra a04e_defconfig + nethunter.config
verify_crc.py             # verifica CRC de modulos del vendor contra el kernel compilado
repack_boot.py            # reemplaza solo el kernel dentro de un boot.img (header v0-v2), conserva ramdisk/dtb
chroot-launcher.sh         # monta /proc,/sys,/dev,/sdcard y entra al chroot de Kali
build_driver.sh            # compila el driver rtl8812au fuera de arbol contra el kernel ya flasheado
kernel-patches.diff        # cambios sobre el kernel fuente (quitar KernelSU, fix build con CUDA instalado)
rtl8812au-patches.diff     # cambios sobre el driver rtl8812au (VID:PID del adaptador, fixes de compilacion)
```

## Paso a paso

### 1. Kernel fuente

```bash
git clone --depth 1 -b a04e https://github.com/ravindu644/android_kernel_a042f kernel
cd kernel
git apply ../kernel-patches.diff
```

El patch quita KernelSU (el root sigue siendo Magisk) y arregla la compilación si tu PC tiene CUDA instalado (clang mete una línea extra en `compile.h` que rompe el build).

### 2. Toolchains

```bash
mkdir toolchains && cd toolchains
curl -LO https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/refs/heads/android11-release/clang-r383902.tar.gz
mkdir clang-r383902 && tar -xzf clang-r383902.tar.gz -C clang-r383902
curl -LO https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz
tar -xJf arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz
```

### 3. Compilar

```bash
bash build.sh
```

Genera `a04e_defconfig`, mezcla `nethunter.config`, compila, y verifica automáticamente los CRC contra los módulos del vendor (ponerlos antes en `vendor_ko/`, extraídos del propio teléfono con `adb pull` vía root).

**Importante:** cualquier opción nueva del kernel debe pasar `verify_crc.py` con 0 CRC distintos antes de flashear. Opciones descartadas por romper el ABI: `CONFIG_SYSVIPC`, `CONFIG_POSIX_MQUEUE`, `CONFIG_CFG80211_WEXT`, `CONFIG_MAC80211_MESH`.

### 4. Respaldar y flashear

```bash
adb shell su -c "dd if=/dev/block/by-name/boot of=/data/local/tmp/boot.img"
adb pull /data/local/tmp/boot.img backup-boot.img   # guardar, es la vuelta atrás

python3 repack_boot.py backup-boot.img kernel/out/arch/arm64/boot/Image.gz boot-nethunter.img
adb push boot-nethunter.img /data/local/tmp/
adb shell su -c "dd if=/data/local/tmp/boot-nethunter.img of=/dev/block/by-name/boot bs=1M conv=fsync"
adb reboot
```

Para revertir: el mismo `dd` con `backup-boot.img`.

### 5. Chroot de Kali

```bash
# en el PC
curl -LO https://kali.download/nethunter-images/current/rootfs/kali-nethunter-rootfs-minimal-arm64.tar.xz
adb push kali-nethunter-rootfs-minimal-arm64.tar.xz /data/local/tmp/kali.tar.xz
adb shell su -c "mkdir -p /data/local/nhsystem/kali-arm64 && cd /data/local/nhsystem/kali-arm64 && busybox tar -xJf /data/local/tmp/kali.tar.xz"
adb push chroot-launcher.sh /data/local/tmp/kali.sh
adb shell su -c "cp /data/local/tmp/kali.sh /data/local/nhsystem/kali && chmod 755 /data/local/nhsystem/kali"
```

Entrar: `adb shell su -c /data/local/nhsystem/kali`

Herramientas: `apt update && apt install -y kali-tools-top10` (dentro del chroot).

### 6. App NetHunter (opcional, interfaz gráfica)

Descargar e instalar desde el repositorio oficial (`store.nethunter.com/repo/index-v2.json`, paquetes `com.offsec.nethunter`, `com.offsec.nhterm`):

```bash
adb install com.offsec.nethunter_<version>.apk
adb install com.offsec.nhterm_<version>.apk
```

Dar permiso root a ambas apps desde Magisk (Superuser → permitir). `NetHunter Terminal` espera el chroot en `/data/local/nhsystem/kalifs`; si lo instalaste en otra ruta, hacer un symlink:

```bash
adb shell su -c "ln -s /data/local/nhsystem/kali-arm64 /data/local/nhsystem/kalifs"
```

### 7. Driver wifi USB externo (opcional)

Para adaptadores RTL8812AU (ver limitación de energía arriba):

```bash
git clone https://github.com/aircrack-ng/rtl8812au driver_rtl8812au
cd driver_rtl8812au
git apply ../rtl8812au-patches.diff   # agrega VID:PID y arregla compilacion con clang 11 / kernel 4.19
cd ..
bash build_driver.sh
```

El `.ko` resultante se verifica igual con `verify_crc.py` antes de cargarlo con `insmod`.

## Créditos

- **Kernel fuente:** [ravindu644/android_kernel_a042f](https://github.com/ravindu644/android_kernel_a042f) — [@ravindu644](https://github.com/ravindu644), [@ravindu755](https://github.com/ravindu755)
- **Driver wifi:** [aircrack-ng/rtl8812au](https://github.com/aircrack-ng/rtl8812au) — mantenido por [@kimocoder](https://github.com/kimocoder), con aportes de [@evilphish](https://github.com/evilphish), [@fariouche](https://github.com/fariouche), [@CGarces](https://github.com/CGarces), [@satmandu](https://github.com/satmandu) y el resto de [colaboradores](https://github.com/aircrack-ng/rtl8812au/graphs/contributors)
- **Rootfs y app:** [Kali NetHunter](https://www.kali.org/docs/nethunter/) (Offensive Security)
