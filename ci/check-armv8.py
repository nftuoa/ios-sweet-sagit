#!/usr/bin/env python3
"""Fail the build when the SAGIT kernel contains instructions Kryo 280 lacks.

Mi 6 (MSM8998) is ARMv8.0: LSE atomics (ARMv8.1), RCpc/LDAPR (ARMv8.3), PAN and
UAO are undefined instructions there.  KDK-provided __hib_text (hibernation,
unsupported on this port and never executed) is skipped.  Also verifies that
the 4 KiB machine layout is in effect.

  check-armv8.py KERNEL
"""
import os
import re
import shutil
import subprocess
import sys

BAD = [
    ('LSE atomic', re.compile(r'\b(ldadd|ldclr|ldeor|ldset|ldsmax|ldsmin|ldumax|ldumin|swp|cas)[a-z]*\s')),
    ('RCpc/LDAPR', re.compile(r'\b(ldapr|stlur|ldapur|stpur)[a-z]*\s')),
    ('PAN/UAO', re.compile(r'\bmsr\s+(pan|uao)\b', re.I)),
]
FOURK_LAYOUT_MIN = 0xfffffff000000000


def find_objdump():
    candidates = [shutil.which('llvm-objdump')]
    brew = shutil.which('brew')
    if brew:
        prefix = subprocess.run([brew, '--prefix', 'llvm'], capture_output=True, text=True)
        if prefix.returncode == 0:
            candidates.append(os.path.join(prefix.stdout.strip(), 'bin', 'llvm-objdump'))
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None


def hib_range(objdump, kernel):
    out = subprocess.run([objdump, '--macho', '--section-headers', kernel],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[1] == '__hib_text':
            vma = int(parts[3], 16)
            size = int(parts[2], 16)
            return vma, vma + size
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    kernel = sys.argv[1]
    objdump = find_objdump()
    if not objdump:
        print('error: no llvm-objdump available (brew install llvm)')
        return 1
    dis = subprocess.run([objdump, '-d', kernel], capture_output=True, text=True).stdout
    skip = hib_range(objdump, kernel)
    hits = {name: [] for name, _ in BAD}
    total = 0
    lowest = None
    for line in dis.splitlines():
        m = re.match(r'^\s*([0-9a-fA-F]{8,16}):', line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        total += 1
        if lowest is None or addr < lowest:
            lowest = addr
        if skip and skip[0] <= addr < skip[1]:
            continue
        for name, pattern in BAD:
            if pattern.search(line):
                hits[name].append(line.strip())
    if total == 0:
        print('error: could not parse the disassembly')
        return 1
    print(f'scanned {total} instructions; hibernation range: '
          f'{hex(skip[0]) + "-" + hex(skip[1]) if skip else "none"}')
    ok = True
    for name, found in hits.items():
        print(f'{name}: {len(found)}')
        if found:
            ok = False
            for line in found[:5]:
                print(f'  {line}')
    print(f'lowest text address: {hex(lowest)}')
    if lowest < FOURK_LAYOUT_MIN:
        print('error: kernel is not linked for the 4 KiB layout (patches 0101/0103 missing?)')
        ok = False
    if not ok:
        print('error: kernel is not ARMv8.0 clean; a sagit patch may have been skipped')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
