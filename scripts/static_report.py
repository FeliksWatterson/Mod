"""Produce metadata, DEX references and ELF/string evidence without executing app code."""
import hashlib
import json
import pathlib
import re
from loguru import logger
from androguard.core.apk import APK
from androguard.core.dex import DEX
from elftools.elf.elffile import ELFFile

logger.remove()
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis'
PATTERN = re.compile(r'(?i)(entitle|premium|ispro|is_pro|billing|purchase|subscription|skyradar|sky_radar|SkyRadarBridge|atlas-image)')


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')


def main():
    manifests = OUT / 'manifests'
    manifests.mkdir(exist_ok=True)
    metadata = []
    for path in sorted((OUT / 'splits').glob('*.apk')):
        apk = APK(str(path))
        xml = apk.get_android_manifest_axml().get_xml()
        (manifests / (path.stem + '.xml')).write_bytes(xml)
        certs = apk.get_certificates()
        metadata.append({'file': path.name, 'package': apk.get_package(),
                         'version_name': apk.get_androidversion_name(),
                         'version_code': apk.get_androidversion_code(),
                         'min_sdk': apk.get_min_sdk_version(), 'target_sdk': apk.get_target_sdk_version(),
                         'permissions': apk.get_permissions(),
                         'cert_sha256': [hashlib.sha256(c.dump()).hexdigest() for c in certs]})
    write_json('apk_metadata.json', metadata)
    dex_info, references = [], []
    for path in sorted((OUT / 'unpacked' / 'base').glob('classes*.dex')):
        dex = DEX(path.read_bytes())
        classes = [c.get_name() for c in dex.get_classes()]
        dex_info.append({'file': path.name, 'header': path.read_bytes()[:8].decode('ascii'),
                         'class_count': len(classes), 'classes': classes,
                         'string_count': len(dex.get_strings()),
                         'method_id_count': dex.header.method_ids_size})
        (OUT / (path.name + '.strings.txt')).write_text('\n'.join(str(s) for s in dex.get_strings()), encoding='utf-8')
        for cls in dex.get_classes():
            for method in cls.get_methods():
                if not method.get_code():
                    continue
                offset = 0
                for instruction in method.get_instructions():
                    text = instruction.get_output()
                    if instruction.get_name().startswith('const-string') and PATTERN.search(text):
                        references.append({'dex': path.name, 'class': cls.get_name(),
                                           'method': method.get_name(), 'descriptor': method.get_descriptor(),
                                           'method_code_file_offset': hex(method.get_code_off()),
                                           'instruction_byte_offset': hex(offset), 'instruction': text})
                    offset += instruction.get_length()
    write_json('dex_inventory.json', dex_info)
    write_json('dex_string_references.json', references)
    elf_info = []
    strings_dir = OUT / 'strings'
    strings_dir.mkdir(exist_ok=True)
    for path in sorted((OUT / 'unpacked').rglob('*.so')):
        data = path.read_bytes()
        (strings_dir / (path.name + '.txt')).write_text('\n'.join(
            f'{m.start():08x} {m.group().decode("ascii")}' for m in re.finditer(rb'[\x20-\x7e]{4,}', data)), encoding='utf-8')
        with path.open('rb') as stream:
            elf = ELFFile(stream)
            symbols = elf.get_section_by_name('.dynsym')
            elf_info.append({'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(),
                             'machine': elf['e_machine'], 'class': elf.elfclass,
                             'sections': [{'name': s.name, 'offset': hex(s['sh_offset']),
                                           'address': hex(s['sh_addr']), 'size': s['sh_size']} for s in elf.iter_sections()],
                             'load_segments': [{'offset': hex(s['p_offset']), 'vaddr': hex(s['p_vaddr']),
                                                'alignment': s['p_align']} for s in elf.iter_segments() if s['p_type'] == 'PT_LOAD'],
                             'symbols': [{'name': s.name, 'value': hex(s['st_value']), 'size': s['st_size']}
                                         for s in symbols.iter_symbols()] if symbols else []})
    write_json('elf_inventory.json', elf_info)
    loc = OUT / 'unpacked/base/assets/flutter_assets/assets/i18n/en.json'
    write_json('localization_entitlement_candidates.json', {k: v for k, v in json.loads(loc.read_text(encoding='utf-8')).items()
               if re.search(r'(?i)\bpro\b|premium|subscription|unlock|free plan|7.day|3.day|paid|purchase', v)})
    print(f'Inspected {len(metadata)} manifests, {len(dex_info)} DEX files, {len(elf_info)} ELF libraries; {len(references)} DEX string references')


if __name__ == '__main__':
    main()
