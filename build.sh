#!/bin/bash
# Compila el kernel NetHunter del A04e. Uso: bash build.sh
set -e
BASE=/home/narcotic/proyectos/nethunter-a04
K=$BASE/kernel
T=$K/toolchains
OUT=${OUT:-$K/out}
mkdir -p "$OUT"
ARGS=(-C "$K" O="$OUT" ARCH=arm64 -j"$(nproc)"
  CROSS_COMPILE="$T/arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-"
  CC="$T/clang-r383902/bin/clang" CLANG_TRIPLE=aarch64-linux-gnu-
  KCFLAGS=-w CONFIG_SECTION_MISMATCH_WARN_ONLY=y)

echo "== defconfig"; make "${ARGS[@]}" a04e_defconfig
echo "== fragmento NetHunter"
cd "$K"
KCONFIG_CONFIG="$OUT/.config" ARCH=arm64 scripts/kconfig/merge_config.sh -m -O "$OUT" "$OUT/.config" "$BASE/nethunter.config"
make "${ARGS[@]}" olddefconfig
grep -E "^CONFIG_(KSU|SYSVIPC|BINFMT_MISC|USB_CONFIGFS_F_HID|ATH9K_HTC|RT2800USB|RTL8XXXU|LOCALVERSION)=" "$OUT/.config"
echo "== compilando"; make "${ARGS[@]}"
python3 -I "$BASE/verify_crc.py" "$OUT/Module.symvers" "$BASE"/vendor_ko/*.ko
ls -l "$OUT/arch/arm64/boot/Image.gz" && echo BUILD_OK
