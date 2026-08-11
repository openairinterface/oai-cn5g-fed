<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Deployment Pre-Requisites

Complete these host-level steps before running any Docker Compose or Podman-based OAI 5G Core tutorial.

## Supported Hosts And Runtimes

The official OAI CN5G container images use Ubuntu 22.04 as the container base image. They are compatible with the following Linux hosts:

| Host family | Supported versions |
| ----------- | ------------------ |
| Ubuntu      | 22.04 through 26.04 |
| Fedora      | 39 through 43 |
| RHEL        | 8 through 10 |

Any Docker or Podman version available for those host releases should be fine. The tutorials mostly show Docker commands; when using Podman, replace `docker` with `podman` and use your distribution's Compose-compatible command where a tutorial uses `docker compose` or `docker-compose`.

## Required Tools

- Docker or Podman
- A Compose-compatible command (`docker compose`, `docker-compose`, or `podman compose`/`podman-compose`)
- Python 3
- `iptables` or a compatible firewall tool
- Optional but recommended for packet analysis: `tshark` and Wireshark

Check the runtime and Python installation:

```bash
docker --version
docker compose version
python3 --version
```

For Podman:

```bash
podman --version
podman compose version
python3 --version
```

## Runtime Permissions

If you use Docker and want to run commands without `sudo`, add your user to the `docker` group and start a new login session:

```bash
sudo usermod -a -G docker "$USER"
```

If you use Podman, follow your distribution's rootless Podman setup. Some tutorials use packet capture or networking commands that still require `sudo`.

## Image Pulls

The tutorials use official images from Docker Hub under the `oaisoftwarealliance` namespace. Docker Hub login is optional unless your network has reached anonymous pull limits.

```bash
docker login
docker pull oaisoftwarealliance/oai-amf:develop
docker logout
```

Podman users can pull the same images:

```bash
podman pull docker.io/oaisoftwarealliance/oai-amf:develop
```

For the full image list, continue with [Retrieve official images](./RETRIEVE_OFFICIAL_IMAGES.md). To build locally, use [Build images](./BUILD_IMAGES.md).

## Network Configuration

Container forwarding must be enabled for end-to-end connectivity:

```bash
sudo sysctl net.ipv4.conf.all.forwarding=1
sudo iptables -P FORWARD ACCEPT
```

Some environments already use Docker's default `172.17.0.0/16` bridge range. If that overlaps with your network, choose an unused bridge subnet and configure the runtime before deploying OAI CN5G.

For Docker, one option is `/etc/docker/daemon.json`:

```json
{
    "bip": "192.168.17.1/24",
    "ip-forward-no-drop": true
}
```

Then restart Docker:

```bash
sudo systemctl restart docker
docker network inspect bridge
```

## Next Step

Choose one image path:

- Pull official images: [Retrieve official images](./RETRIEVE_OFFICIAL_IMAGES.md)
- Build local images: [Build images](./BUILD_IMAGES.md)
