#!/usr/bin/env python3
"""Compara los CRC que piden los .ko del vendor con los de Module.symvers/vmlinux del kernel nuevo.
Uso: python3 -I verify_crc.py Module.symvers modulo1.ko modulo2.ko ..."""
import struct, sys

def versions(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'\x7fELF' and d[4] == 2, 'se espera ELF64'
    shoff, = struct.unpack('<Q', d[0x28:0x30])
    shentsize, shnum, shstrndx = struct.unpack('<HHH', d[0x3A:0x40])
    secs = []
    for i in range(shnum):
        o = shoff + i * shentsize
        name, typ, flags, addr, off, size = struct.unpack('<IIQQQQ', d[o:o + 40])
        secs.append((name, off, size))
    stroff = secs[shstrndx][1]
    out = {}
    for name, off, size in secs:
        n = d[stroff + name:d.index(b'\0', stroff + name)].decode()
        if n == '__versions':
            for p in range(off, off + size, 64):
                crc, = struct.unpack('<Q', d[p:p + 8])
                sym = d[p + 8:p + 64].split(b'\0')[0].decode()
                out[sym] = crc & 0xFFFFFFFF
    return out

symvers = {}
for line in open(sys.argv[1]):
    f = line.split()
    if len(f) >= 2:
        symvers[f[1]] = int(f[0], 16)

bad = 0
for ko in sys.argv[2:]:
    v = versions(ko)
    miss = [s for s in v if s not in symvers]
    diff = [s for s in v if s in symvers and symvers[s] != v[s]]
    print(f'{ko.split("/")[-1]}: {len(v)} simbolos, {len(diff)} con CRC distinto, {len(miss)} no exportados')
    for s in diff[:10]:
        print(f'   CRC distinto: {s} modulo={v[s]:08x} kernel={symvers[s]:08x}')
    for s in miss[:10]:
        print(f'   falta: {s}')
    bad += len(diff) + len(miss)
print('RESULTADO:', 'COMPATIBLE' if bad == 0 else f'{bad} problemas')
