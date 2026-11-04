#!/usr/bin/env python3
"""Sustituye solo el kernel de un boot.img (cabecera v0-v2), conservando ramdisk, dtb y cabecera.
Uso: python3 -I repack_boot.py boot_original.img kernel_nuevo boot_salida.img"""
import struct, sys

def pad(n, page):
    return (-n) % page

src, kern, dst = sys.argv[1:4]
d = open(src, 'rb').read()
assert d[:8] == b'ANDROID!', 'no es un boot.img'
(ksz, kaddr, rsz, raddr, ssz, saddr, tags, page, ver, osv) = struct.unpack('<10I', d[8:48])
print(f'header v{ver} page={page} kernel={ksz} ramdisk={rsz} second={ssz}')
rdtbo = 0
dtb = 0
if ver >= 1:
    rdtbo, = struct.unpack('<I', d[1632:1636])
if ver >= 2:
    dtb, = struct.unpack('<I', d[1648:1652])
print(f'recovery_dtbo={rdtbo} dtb={dtb}')

off = page
old_kernel = d[off:off + ksz]
print('kernel original empieza con', old_kernel[:4].hex(), '(1f8b08 = gzip)')
off += ksz + pad(ksz, page)
ramdisk = d[off:off + rsz]; off += rsz + pad(rsz, page)
second = d[off:off + ssz]; off += ssz + pad(ssz, page)
rd = d[off:off + rdtbo]; off += rdtbo + pad(rdtbo, page)
dtbdata = d[off:off + dtb]

new = open(kern, 'rb').read()
print('kernel nuevo empieza con', new[:4].hex(), 'tamano', len(new))
hdr = bytearray(d[:page])
hdr[8:12] = struct.pack('<I', len(new))
# el campo id (sha1) se deja a cero: el bootloader no lo comprueba
hdr[576:608] = b'\0' * 32

def blk(b):
    return b + b'\0' * pad(len(b), page)

out = bytes(hdr) + blk(new) + blk(ramdisk) + (blk(second) if ssz else b'') \
      + (blk(rd) if rdtbo else b'') + (blk(dtbdata) if dtb else b'')
open(dst, 'wb').write(out)
print('escrito', dst, len(out), 'bytes')
