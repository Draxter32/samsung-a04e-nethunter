#!/bin/bash
# Compila el modulo rtl8812au fuera de arbol, contra el kernel ya flasheado en el telefono.
set -e
BASE=/home/narcotic/proyectos/nethunter-a04
D=$BASE/driver_rtl8812au
K=$BASE/kernel
T=$K/toolchains

make -C "$D" ARCH=arm64 \
  CROSS_COMPILE="$T/arm-gnu-toolchain-14.2.rel1-x86_64-aarch64-none-linux-gnu/bin/aarch64-none-linux-gnu-" \
  CC="$T/clang-r383902/bin/clang" CLANG_TRIPLE=aarch64-linux-gnu- \
  KSRC="$K/out_clean" KVER=4.19.191-28581296-abA042MUBSDEYG1 \
  CONFIG_RTL8812AU=y CONFIG_RTW_DEBUG=y

ls -l "$D/8812au.ko" && echo DRIVER_BUILD_OK
