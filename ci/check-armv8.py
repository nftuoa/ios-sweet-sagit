#!/usr/bin/env python3
"""Fail the build when the SAGIT kernel contains instructions Kryo 280 lacks.

Mi 6 (MSM8998) is an ARMv8.0 core: LSE atomics (ARMv8.1), RCpc/LDAPR (ARMv8.3),
PAN and UAO are undefined instructions there.  KDK-provided __hib_text
(hibernation, unsupported on this port and never executed) is skipped.

  check-armv8.py KERNEL
"""
import re
import subprocess
import sys

BAD = [
    ('LSE atomic', re.compile(r'\b(ldadd|ldclr|ldeor|ldset|ldsmax|ldsmin|ldumax|ldumin|swp|cas)[a-z]*\s')),
    ('RCpc/LDAPR', re.compile(r'\b(ldapr|stlur|ldapur|stpur)[a-z]*\s')),
    ('PAN/UAO', re.compile(r'\bmsr\s+(pan|uao)\b', re.I)),
]
EXPECTED_BASE = 0xfffffff000000000


def hib_range(kernel):
    out = subprocess.run(['otool', '-l', kernel], capture_output=True, text=True).stdout
    lines = out.splitlines()
    for i, line in enumerate(lines):
        if '__hib_text' in line:
            addr = size = None
            for follow in lines[i:i + 12]:
                m = re.search(r'^\s*addr (0x[0-9a-f]+)', follow)
                if m and addr is None:
                    addr = int(m.group(1), 16)
                m = re.search(r'^\s*size (0x[0-9a-f]+)', follow)
                if m and size is None:
                    size = int(m.group(1), 16)
            if addr is not None and size is not None:
                return addr, addr + size
    return None


def first_segment_base(kernel):
    out = subprocess.run(['otool', '-l', kernel], capture_output=True, text=True).stdout
    m = re.search(r'LC_SEGMENT_64.*?vmaddr (0x[0-9a-f]+)', out, re.S)
    return int(m.group(1), 16) if m else None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    kernel = sys.argv[1]
    dis = subprocess.run(['otool', '-tvV', kernel], capture_output=True, text=True).stdout
    skip = hib_range(kernel)
    hits = {name: [] for name, _ in BAD}
    total = 0
    for line in dis.splitlines():
        # otool prints "<addr>\t<encoding>\t<mnemonic> <operands>"; newer builds
        # pad the address with spaces and may prefix arm64e pointers with '+'.
        m = re.match(r'^\s*\+?([0-9a-fA-F]{8,16})\s', line)
        if not m:
            continue
        total += 1
        addr = int(m.group(1), 16)
        if skip and skip[0] <= addr < skip[1]:
            continue
        for name, pattern in BAD:
            if pattern.search(line):
                hits[name].append(line.strip())
    if total == 0:
        print('error: could not parse the disassembly (otool format changed?)')
        return 1
    print(f'scanned {total} instructions; hibernation range: '
          f'{hex(skip[0]) + "-" + hex(skip[1]) if skip else "none"}')
    base = first_segment_base(kernel)
    ok = True
    for name, found in hits.items():
        print(f'{name}: {len(found)}')
        if found:
            ok = False
            for line in found[:5]:
                print(f'  {line}')
    print(f'first segment vmaddr: {hex(base) if base is not None else "unknown"}')
    if base is None or (base & 0xffffffff00000000) != EXPECTED_BASE:
        print('error: kernel is not linked for the 4 KiB layout (patches 0101/0103 missing?)')
        ok = False
    if not ok:
        print('error: kernel is not ARMv8.0 clean; a sagit patch may have been skipped')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
