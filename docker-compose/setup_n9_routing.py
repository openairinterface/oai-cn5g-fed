#!/usr/bin/env python3
"""Join the V-UPF and H-UPF over the inter-PLMN network for home-routed roaming.

Each UPF keeps its single N3/N4/N6 interface (eth0) in its own PLMN. This
script attaches both UPFs to the network shared by the SEPPs, at the address
of the org.openairinterface.n9.ipv4 label, and routes the peer UPF's GTP-U
address through it, so the N9 tunnel crosses the inter-PLMN network (IPX).
It is idempotent and can be re-run after the UPFs are restarted.
"""
import argparse
import json
from pathlib import Path
import subprocess
try:
    import yaml
except ImportError:
    raise SystemExit('PyYAML is required: install python3-yaml (apt) or run "pip install pyyaml"')

base = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--compose', type=Path, default=base / 'docker-compose-basic-nrf-hr-roaming.yaml')
args = parser.parse_args()
compose = yaml.safe_load(args.compose.read_text())
services = compose['services']
label = 'org.openairinterface.n9.ipv4='

# The inter-PLMN network is the one both SEPPs are attached to
sepps = [s for s in services.values() if 'oai-sepp' in s['image']]
shared = set.intersection(*(set(s['networks']) for s in sepps))
assert len(shared) == 1, 'SEPPs must share exactly one network'
roaming = shared.pop()
roaming_name = compose['networks'][roaming].get('name', roaming)

upfs = []
for name, s in services.items():
    n9 = [l[len(label):] for l in s.get('labels', []) if l.startswith(label)]
    if 'oai-upf' in s['image'] and n9:
        local = next(iter(s['networks'].values()))['ipv4_address']
        upfs.append({'service': name, 'container': s['container_name'], 'gtpu': local, 'n9': n9[0]})
assert len(upfs) == 2, 'Expected one V-UPF and one H-UPF with an N9 label'

for upf in upfs:
    info = json.loads(subprocess.check_output(['docker', 'inspect', upf['container']]))[0]
    if roaming_name not in info['NetworkSettings']['Networks']:
        subprocess.run(['docker', 'network', 'connect', '--ip', upf['n9'], roaming_name, upf['container']], check=True)
        print(f"{upf['service']}: connected to {roaming_name} as {upf['n9']}")
    else:
        print(f"{upf['service']}: already on {roaming_name}")

for upf, peer in ((upfs[0], upfs[1]), (upfs[1], upfs[0])):
    subprocess.run(['docker', 'exec', upf['container'], 'ip', 'route', 'replace',
                    peer['gtpu'] + '/32', 'via', peer['n9']], check=True)
    print(f"{upf['service']}: N9 to {peer['service']} GTP-U {peer['gtpu']} via {peer['n9']}")
