# OAI 5G Core Network Deployment (Non-Containerized)

## Overview

This tutorial explains how to build and deploy the **OAI 5G Core Network** in a **non-containerized** environment on a single host machine.

* This tutorial covers the following 5G Core Network Functions:

  * NRF
  * UDR
  * UDM
  * AUSF
  * AMF
  * SMF
  * UPF

---

## Tested Environment

| Component  | Version                        |
| ---------- | ------------------------------ |
| OS         | Ubuntu 22.04 LTS               |
| Compiler   | gcc / g++ 11                   |
| OAI Branch | `develop`                      |
| Deployment | non-containerized |

---

## 1. Prerequisites

### 1.1 Install Compiler

```bash
sudo apt update
sudo apt install -y gcc g++
```

Verify:

```bash
gcc --version
g++ --version
```

Expected:

```console
gcc (Ubuntu 11.4.0-1ubuntu1~22.04.2) 11.4.0
g++ (Ubuntu 11.4.0-1ubuntu1~22.04.2) 11.4.0
```

> You can refer this [documentation](https://www.dedicatedcore.com/blog/install-gcc-compiler-ubuntu/) for more details on installing GCC on Ubuntu.

---

## 2. Networking Prerequisites

Create a Linux network interface that all core network functions will use to communicate with each other.

### 2.1 Create Core Network Interface

Create the interface **once**, before starting any NF:

```bash
sudo ip link add oai-core type dummy
sudo ip addr add 192.168.70.10/24 dev oai-core
sudo ip link set oai-core up
```

Verify:

```bash
ip -4 addr show oai-core | awk '/inet / {print $2}'
```

Expected:

```console
192.168.70.10/24
```

---

## 3. Clone and Build Network Functions

Each Network Function is built independently.

### 3.1 Clone Repository

```bash
git clone https://gitlab.eurecom.fr/oai/cn5g/oai-cn5g-amf.git
cd oai-cn5g-amf
git checkout develop
cd build/scripts
```

### 3.2 Install Dependencies

```bash
./build_amf --install-deps --force
```

Expected:

```text
AMF deps installation successful
```

### 3.3 Compile AMF

```bash
./build_amf
```

---

### 3.4 Build Other Network Functions

Repeat the same steps for:

| NF   | Repository              |
| ---- | ----------------------- |
| NRF  | oai-cn5g-nrf            |
| UDR  | oai-cn5g-udr            |
| UDM  | oai-cn5g-udm            |
| AUSF | oai-cn5g-ausf           |
| SMF  | oai-cn5g-smf            |
| UPF  | oai-cn5g-upf            |

> This process may take several minutes per NF depending on your system.
Please be patient and allow each build to complete before moving to the next one.
---

## 4. Configuration Files

Configuration files are stored [here](configurations). Please take a moment to glance through each configuration file before proceeding to the next step.

---

## 5. Start Network Functions

Start each Network Function in a separate terminal, in the following order:

1. NRF
2. UDR
3. UDM
4. AUSF
5. AMF
6. SMF
7. UPF

Place the configuration files in each network function's repository in the folder `etc/`.

For example:

```bash
cd ~/oai-cn5g-nrf/etc
git checkout develop
ls | grep config_nrf.yaml # config_nrf.yaml
```

Repeat this step for all other Network Functions before proceeding.

### 5.1 NRF

```bash
sudo ./build/nrf/build/nrf -c etc/config_nrf.yaml -o
```

---

### 5.2 UDR

```bash
./build/udr/build/udr -c etc/config_udr.yaml -o
```

---

### 5.3 UDM

```bash
./build/udm/build/udm -c etc/config_udm.yaml -o
```

---

### 5.4 AUSF

```bash
./build/ausf/build/ausf -c etc/config_ausf.yaml -o
```

> If you see PID file errors:

```bash
sudo mkdir -p /tmp
sudo chmod 777 /tmp
```

---

### 5.5 AMF

```bash
./build/amf/build/amf -c etc/config_amf.yaml -o
```

---

### 5.6 SMF

```bash
./build/smf/build/smf -c etc/config_smf.yaml -o
```

---


## 6. Notes and Troubleshooting

Always read the logs carefully — most configuration or runtime issues are clearly indicated there.

If issues persist, please write to the OAI mailing list and include the following information:

- Operating System version
- gcc / g++ version
- System architecture (e.g., x86_64)
- Exact commands used to build and run the Network Functions
- Git branch used (if not `develop`) 
- Relevant log showing the error

Providing complete and precise information will help the community diagnose and resolve the issue more efficiently.

---