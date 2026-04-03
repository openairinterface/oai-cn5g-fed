<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<table>
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="./images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">OpenAirInterface 5G Core Network with MongoDB</font></b>
    </td>
  </tr>
</table>

## 1. Pre-requisites

Create a folder where you can store all the result files of the tutorial and later compare them with our provided result files, we recommend creating exactly the same folder to not break the flow of commands afterwards

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: rm -rf /tmp/oai/mongodb-test
```
-->

``` shell
docker-compose-host $: mkdir -p /tmp/oai/mongodb-test
docker-compose-host $: chmod 777 /tmp/oai/mongodb-test
```

## 2. Deploy Core-Network with Mongo DB

``` shell
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-mongodb.yaml up -d mongodb
docker-compose-host $: nohup sudo tshark -i demo-oai -f '(not host 192.168.70.135 and not arp and not port 53 and not port 2152) or (host 192.168.70.135 and icmp)' -w /tmp/oai/mongodb-test/mongodb-test.pcap > /tmp/oai/mongodb-test/mongodb-test.log 2>&1 &
docker-compose-host $: ../ci-scripts/checkContainerStatus.py --container_name mongodb --timeout 30
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-mongodb.yaml up -d
docker-compose-host $: ../ci-scripts/checkContainerStatus.py --container_name oai-smf --timeout 30
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-mongodb.yaml ps -a
docker-compose-host $: sleep 30
docker-compose-host $: sudo chmod 666 /tmp/oai/mongodb-test/mongodb-test.*
```

## 3. Test with RAN emulator

``` shell
docker-compose-host $: docker-compose -f docker-compose-gnbsim.yaml up -d gnbsim
docker-compose-host $: ../ci-scripts/checkContainerStatus.py --container_name gnbsim --timeout 30
docker-compose-host $: docker logs gnbsim 2>&1 | grep "UE address:"
docker-compose-host $: docker exec oai-ext-dn ping 12.1.1.4 -c4
```
## 4. Get Logs

<!---
For CI purposes please ignore this line
``` shell
docker-compose-host $: docker-compose -f docker-compose-gnbsim.yaml stop -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-mongodb.yaml stop -t 30
```
-->

``` shell
docker-compose-host $: docker logs oai-amf > /tmp/oai/mongodb-test/amf.log 2>&1
docker-compose-host $: docker logs oai-smf > /tmp/oai/mongodb-test/smf.log 2>&1
docker-compose-host $: docker logs oai-nrf > /tmp/oai/mongodb-test/nrf.log 2>&1
docker-compose-host $: docker logs oai-upf > /tmp/oai/mongodb-test/upf.log 2>&1
docker-compose-host $: docker logs oai-udr > /tmp/oai/mongodb-test/udr.log 2>&1
docker-compose-host $: docker logs oai-udm > /tmp/oai/mongodb-test/udm.log 2>&1
docker-compose-host $: docker logs oai-ausf > /tmp/oai/mongodb-test/ausf.log 2>&1
docker-compose-host $: docker logs oai-ext-dn > /tmp/oai/mongodb-test/ext-dn.log 2>&1
docker-compose-host $: docker logs gnbsim > /tmp/oai/mongodb-test/gnbsim.log 2>&1
docker-compose-host $: docker logs mongodb > /tmp/oai/mongodb-test/mongodb.log 2>&1
```

## 5. Undeploy

``` shell
docker-compose-host $: docker-compose -f docker-compose-gnbsim.yaml down -t 2
docker-compose-host $: docker-compose -f docker-compose-basic-nrf-mongodb.yaml down -t 2
```

## 6. Dummy section

