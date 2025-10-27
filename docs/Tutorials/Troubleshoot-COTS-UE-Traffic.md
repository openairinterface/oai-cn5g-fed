# OpenAirInterface 5G Core Network : testing with Commercial UE traffic troubleshooting

`COTS-UE` means `Commercial Off-The-Shelf UE`.

Prior to `2022.w12` tag, if you were deploying a `minimalist` or `basic` OAI 5G CN, you would see the following issue:

* Ping operations from `ext-dn` to `COTS-UE` or from `COTS-UE` to `ext-dn` were OK
* `TCP` iperf traffic test was OK in `Downlink` and `Uplink`
* `UDP` iperf traffic test was OK in `Uplink` (ie from `COTS-UE` to `ext-dn`)
* But `UDP` `Downlink` iperf traffic test was not working.

The issue is the `MTU` value affected to the interface on the UE.

For example, we are using Quectel modules and it looks like this:

```bash
$ ifconfig wwan0
wwan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1356
        inet 12.1.1.129 netmask 255.255.255.0  broadcast 12.1.1.255
```

2 solutions:

* Either you force the `MTU` value (if possible):

```bash
$ sudo ip link set dev wwan0 mtu 1500
```

* The better one is to tell the `SMF` to use this `1500` value.

I made 2 examples in the `docker-compose/docker-compose-basic-nrf.yaml` and `docker-compose/docker-compose-mini-nrf.yaml` files:

```bash
$ git diff docker-compose/docker-compose-basic-nrf.yaml
diff --git a/docker-compose/docker-compose-basic-nrf.yaml b/docker-compose/docker-compose-basic-nrf.yaml
index 04aceae..fef0835 100644
--- a/docker-compose/docker-compose-basic-nrf.yaml
+++ b/docker-compose/docker-compose-basic-nrf.yaml
@@ -250,6 +250,7 @@ services:
             - DNN_RANGE1=12.1.1.2 - 12.1.1.128
             - DNN_RANGE0=12.2.1.2 - 12.2.1.128
             - DNN_NI1=default
+            - UE_MTU=1500
         depends_on:
             - oai-nrf
             - oai-amf
$ git diff docker-compose/docker-compose-mini-nrf.yaml
diff --git a/docker-compose/docker-compose-mini-nrf.yaml b/docker-compose/docker-compose-mini-nrf.yaml
index cd58557..35b3d3b 100644
--- a/docker-compose/docker-compose-mini-nrf.yaml
+++ b/docker-compose/docker-compose-mini-nrf.yaml
@@ -147,6 +147,7 @@ services:
             - DNN_RANGE1=12.1.1.2 - 12.1.1.128
             - DNN_RANGE0=12.2.1.2 - 12.2.1.128
             - DNN_NI1=default
+            - UE_MTU=1500
         depends_on:
             - oai-nrf
             - oai-amf
```

With this `SMF` setup:

```bash
$ ifconfig wwan0
wwan0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 12.1.1.129 netmask 255.255.255.0  broadcast 12.1.1.255
```
