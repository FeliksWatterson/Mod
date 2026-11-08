"""Independently decode critical ARM64 sites from ELF bytes with Capstone.

Does not load or execute native code. Addresses are ELF virtual addresses.
"""
import hashlib
import json
import pathlib
from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM
from elftools.elf.elffile import ELFFile

ROOT = pathlib.Path(__file__).resolve().parents[1]
path = ROOT / 'analysis/unpacked/split_config.arm64_v8a/lib/arm64-v8a/libapp.so'
sites = {0x7216BC: 0x7216EC, 0x721748: 0x721998, 0x744000: 0x744018,
         0x82E15C: 0x82E278, 0x7F0AA0: 0x743FAC, 0x7F0AC4: 0x743FAC,
         0x8B61A8: 0x8B6C54, 0x8B6520: 0x82DC00, 0x7213D8: 0x721434}
data = path.read_bytes()
with path.open('rb') as stream:
    elf = ELFFile(stream)
    segments = [dict(s.header) for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD']


def offset(address):
    for segment in segments:
        if segment['p_vaddr'] <= address < segment['p_vaddr'] + segment['p_filesz']:
            return segment['p_offset'] + address - segment['p_vaddr']
    raise ValueError(hex(address))


decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
results = []
for address, target in sites.items():
    pos = offset(address)
    instruction = next(decoder.disasm(data[pos:pos+4], address))
    assert instruction.mnemonic == 'bl' and int(instruction.op_str.removeprefix('#'), 16) == target
    results.append({'vaddr': hex(address), 'file_offset': hex(pos), 'bytes': data[pos:pos+4].hex(),
                    'instruction': f'{instruction.mnemonic} {instruction.op_str}', 'expected_target': hex(target)})
ranges = []
for address, size in [(0x721434, 0x54), (0x7213BC, 0x78), (0x721998, 0x13c), (0x7216EC, 0x104)]:
    pos = offset(address)
    ranges.append({'start': hex(address), 'file_offset': hex(pos),
                   'instructions': [f'{i.address:#x}: {i.mnemonic} {i.op_str}'
                                    for i in decoder.disasm(data[pos:pos+size], address)]})
report = {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(),
          'call_sites': results, 'ranges': ranges,
          'tagging_note': 'FeaturePolicy.limit returns tagged int?; raw x0=0x1c at 0x721478 decodes to Smi 14. fetchDays unboxes then returns an unboxed int.'}
(ROOT / 'analysis/native_verified_sites.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(f'Confirmed {len(results)} direct calls against ELF bytes; four ranges independently disassembled')
