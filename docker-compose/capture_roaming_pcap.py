#!/usr/bin/env python3
"""Capture the roaming test traffic on the PLMN A, inter-PLMN and PLMN B bridges.

tcpdump runs in a helper container on the host network (no host tcpdump or
sudo needed) until the given command finishes, or for --seconds. The three
per-bridge captures are merged, in time order, into a single pcap file.
"""
import argparse
import os
import re
from pathlib import Path
import struct
import subprocess
import time
try:
    import yaml
except ImportError:
    raise SystemExit('PyYAML is required: install python3-yaml (apt) or run "pip install pyyaml"')

base = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compose', type=Path, default=base / 'docker-compose-basic-nrf-hr-roaming.yaml')
parser.add_argument('--output', type=Path, required=True, help='merged pcap file')
parser.add_argument('--image', help='any local image with tcpdump (default: the NRF image of the compose file)')
parser.add_argument('--seconds', type=int, default=240)
parser.add_argument('--filter', default='sctp or udp port 8805 or udp port 2152 or tcp port 8080 or tcp port 80 or icmp')
args = parser.parse_args()

compose = yaml.safe_load(args.compose.read_text())
if not args.image:
    # The OAI NF images ship tcpdump: reuse the NRF image of the scenario, ${VAR:-default} resolved
    image = next(s['image'] for name, s in compose['services'].items() if name.startswith('oai-nrf'))
    args.image = re.sub(r'\$\{(\w+):-([^}]*)\}', lambda m: os.environ.get(m.group(1)) or m.group(2), image)
bridges = [n['driver_opts']['com.docker.network.bridge.name'] for n in compose['networks'].values()]
# Start with "docker compose up": wait until the bridges exist
deadline = time.time() + 120
while not all(Path('/sys/class/net', b).exists() for b in bridges):
    if time.time() > deadline:
        raise SystemExit(f'Bridges {bridges} not found; is the deployment starting?')
    time.sleep(0.5)
workdir = args.output.resolve().parent
workdir.mkdir(parents=True, exist_ok=True)
parts = [workdir / f'.{args.output.stem}-{b}.pcap' for b in bridges]
script = ' & '.join(f"tcpdump -U -n -i {b} -w /out/{p.name} '{args.filter}'" for b, p in zip(bridges, parts))
name = f'roaming-pcap-{os.getpid()}'
subprocess.run(['docker', 'run', '-d', '--name', name, '--network', 'host',
                '--cap-add', 'NET_ADMIN', '--cap-add', 'NET_RAW', '-v', f'{workdir}:/out',
                '--entrypoint', '/bin/sh', args.image, '-c', script + ' & wait'],
               check=True, stdout=subprocess.DEVNULL)
time.sleep(2)
if subprocess.run(['docker', 'exec', name, 'pgrep', 'tcpdump'], stdout=subprocess.DEVNULL).returncode:
    raise SystemExit('tcpdump did not start: ' + subprocess.run(['docker', 'logs', name], capture_output=True, text=True).stderr)
print(f'Capturing on {", ".join(bridges)} for {args.seconds}s ...', flush=True)
try:
    time.sleep(args.seconds)
finally:
    subprocess.run(['docker', 'exec', name, 'pkill', '-INT', 'tcpdump'], stderr=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run(['docker', 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Merge classic pcap files with the same link type, ordered by timestamp
header, records = None, []
for part in parts:
    data = part.read_bytes()
    header = header or data[:24]
    offset = 24
    while offset + 16 <= len(data):
        sec, usec, incl, _ = struct.unpack('<IIII', data[offset:offset + 16])
        records.append(((sec, usec), data[offset:offset + 16 + incl]))
        offset += 16 + incl
    part.unlink()
records.sort(key=lambda r: r[0])
args.output.write_bytes(header + b''.join(r[1] for r in records))
print(f'Wrote {len(records)} packets to {args.output}')
