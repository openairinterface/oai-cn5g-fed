#!/usr/bin/env python3
"""Capture complete Docker logs, including every home and visited NF."""
import argparse
import datetime
import json
import os
from pathlib import Path
import subprocess
try:
    import yaml
except ImportError:
    raise SystemExit('PyYAML is required: install python3-yaml (apt) or run "pip install pyyaml"')

base = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--since', help='Optional Docker timestamp; omit to capture complete container logs')
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--compose', type=Path, default=base / 'docker-compose-basic-nrf-lbo-roaming.yaml')
args = parser.parse_args()
os.umask(0o077)
args.output.mkdir(parents=True, exist_ok=True)
until = datetime.datetime.now(datetime.timezone.utc).isoformat()
config = yaml.safe_load(args.compose.read_text())
manifest = {'compose': args.compose.name, 'since': args.since, 'until': until, 'containers': []}
for service, spec in config['services'].items():
    name = spec['container_name']
    info = json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
    with (args.output / (service + '.txt')).open('w') as output:
        command = ['docker', 'logs', '--timestamps', '--until', until]
        if args.since:
            command += ['--since', args.since]
        subprocess.run(command + [name], stdout=output, stderr=subprocess.STDOUT, check=True)
    manifest['containers'].append({'service': service, 'container': name,
        'image': info['Config']['Image'], 'image_id': info['Image'],
        'started_at': info['State']['StartedAt'], 'running': info['State']['Running'],
        'health': info['State'].get('Health', {}).get('Status', 'not configured')})
(args.output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Captured {len(manifest["containers"])} containers, including all eight NFs per PLMN, in {args.output}')
print('Raw debug logs may contain authentication material; publish only selected, redacted excerpts.')
