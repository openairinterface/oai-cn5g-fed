<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<table style="border-collapse: collapse; border: none;">
  <tr style="border-collapse: collapse; border: none;">
    <td style="border-collapse: collapse; border: none;">
      <a href="http://www.openairinterface.org/">
         <img src="../../docs/images/oai_final_logo.png" alt="" border=3 height=50 width=150>
         </img>
      </a>
    </td>
    <td style="border-collapse: collapse; border: none; vertical-align: center;">
      <b><font size = "5">Core Network Quectel Testing Setup</font></b>
    </td>
  </tr>
</table>

The motive of this testing is to be sure all the merge request on AMF, SMF, UDR, UDM, AUSF and UPF github repositories always works properly with COTSUE. This testing will be performed via oai-jenkins platform, this readme explains how jenkins perform the testing.

Our correct testing scenario is

1. Deploy Core Network
2. Start gNB (USRP B210)
3. Perform_In_Loop_Twice(Start UE(Triggers Registration and PDU Session for `oai` and `ims` dnn) --> Stop UE (Triggers PDU session release for `oai` and `ims` dnn in order and then DE-Registration))
4. Collect Logs
5. Stop gNB
6. Remove the Core Network


![Helm Chart Deployment](./images/core-ci.png)

1.  [Deploy the Core Network](#1-deploy-the-core-network)
2.  [Start the gNB](#2-start-the-gnb)
3.  [Perform the Test](#3-perform-the-test)
4.  [Collect the Artifacts](#4-collect-the-artifacts)
5.  [Remove the Deployment](#5-remove-the-deployment)
6.  [Analyze the Artifacts](#6-analyze-the-artifacts)



### Pre-requisite

You need to have access to below machines

|Server                      |Software/Hardware                                          |
|:---------------------------|:----------------------------------------------------------|
|Openshift client            |oc, helm (v3)                                              |
|Image builder               |Podman                                                     |
|gNB Server                  |USRP B210                                                  |
|UE Server                   |Quectel RM520                                              |


Important configuration related information


|Key       |Values                                                        |
|:---------|:-------------------------------------------------------------|
|PLMN      |00101                                                         |
|UE Release|16                                                            |
|IMSI      |001010000000100                                               |
|TAC       |0x01                                                          |
|key       |fec86ba6eb707ed08905757b1bb44b8f                              |
|opc       |C42449363BBAD02B66D16BC975D77CC1                              |
|ip-address|12.1.1.100 (for oai DNN) dynamic for ims DNN (mostly 12.2.1.2)|
|Slice,DNN |oai(1,0xFFFFFF),ims(1,0xFFFFFF)                               |


Know how to use helm, docker-compose, oc, kubectl commands.

Of course! clone this repository and go to `ci-scripts/charts` directory.


## 1. Deploy the Core Network

Login to openshift cluster, you should know the password and from where to login.

```shell
oc login -u <USER> <OPENSHIFT_API_URL>
oc project <PROJECT>
```

Now make sure that all the network function image tags you want to use are present when you do `oc get is`. At the time of writing this tutorial these tags are here

```
NAME             IMAGE REPOSITORY                                                                            TAGS               UPDATED
oai-amf          <openshift-registry-url>/<PROJECT>/oai-amf          develop-eaed3191   27 hours ago
oai-ausf         <openshift-registry-url>/<PROJECT>/oai-ausf         develop-702608a7   27 hours ago
oai-nrf          <openshift-registry-url>/<PROJECT>/oai-nrf          develop-f66cc2fe   27 hours ago
oai-smf          <openshift-registry-url>/<PROJECT>/oai-smf          develop-5c7fbfd7   27 hours ago
oai-upf          <openshift-registry-url>/<PROJECT>/oai-upf          develop-8c4397a    27 hours ago
oai-udm          <openshift-registry-url>/<PROJECT>/oai-udm          develop-7723778c   27 hours ago
oai-udr          <openshift-registry-url>/<PROJECT>/oai-udr          develop-89a82cc0   27 hours ago
oai-traffic-gen  <openshift-registry-url>/<PROJECT>/oai-traffic-gen  latest             27 hours ago
```
**NOTE** Never delete `oai-traffic-gen` image stream it is used to collect pcaps from the network functions.

Build the CentOS images of the network functions as described in [BUILD_IMAGES.md](../../docs/BUILD_IMAGES.md), then push them to your openshift project.

For example the images can be pushed using below command

```shell
#first tag the image
sudo podman tag oai-amf:develop <openshift-registry-url>/<PROJECT>/oai-amf:<TAG-YOU-WANT>
oc whoami -t | sudo podman login -u <USER> --password-stdin https://<openshift-registry-url> --tls-verify=false
sudo podman push <openshift-registry-url>/<PROJECT>/oai-amf:<TAG-YOU-WANT>
sudo podman rmi <openshift-registry-url>/<PROJECT>/oai-amf:<TAG-YOU-WANT>
sudo podman logout https://<openshift-registry-url>
```
**NOTE**: At the time of login or logout if you have error saying weird https then remove https:// from url and then re-try.

Once images are push it will be good to verify that they are present in the right project/namespace

```shell
# grep the pushed tag of all the network functions
oc get istag | grep NRF_TAG_YOU_PUSHED
oc get istag | grep AMF_TAG_YOU_PUSHED
oc get istag | grep SMF_TAG_YOU_PUSHED
oc get istag | grep UPF_TAG_YOU_PUSHED
oc get istag | grep AUSF_YOU_PUSHED
oc get istag | grep UDR_TAG_YOU_PUSHED
oc get istag | grep UDM_TAG_YOU_PUSHED
```

### 1.1 Changing the tags

Once the images are present in your openshift project/namespace. We are ready to prepare the helm-charts with images tags pushed to the cluster.

For the basic deployment the charts are present in `ci-scripts/charts/oai-5g-basic` and the most important file is `values.yaml` with all the configuration information.

These charts are set up for the OAI CI testbed: they pull the images from the `oaicicd-core` project and use the network addresses of that lab. To deploy them elsewhere, adapt the `values.yaml` and the `templates/rbac.yaml` of each chart. For a regular helm deployment, follow [DEPLOY_SA5G_HC.md](../../docs/DEPLOY_SA5G_HC.md) instead.

Do not change any other helm-charts unless you don't find the configuration variable you want to change.

```shell
#assuming my current directory is ci-scripts/charts/oai-5g-basic
sed -i 's/NRF_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/AMF_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/SMF_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/UPF_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/AUSF_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/UDR_TAG/<TAG_YOU_WANT>/g' values.yaml
sed -i 's/UDM_TAG/<TAG_YOU_WANT>/g' values.yaml
```

The UPF is configured to support two subnets, to disable that please remove the `ims` DNN from `config.yaml`

### 1.2 Deploy the Basic Core Network

This step can take somewhere 3 to 4 mins so if planning a timeout do not plan less than 6 mins (taking some margin)

Run the below command on the openshift client which has access to `helm command`

```shell
#assuming my current directory is ci-scripts/charts/oai-5g-basic
oc project <PROJECT>
helm dependency update
helm install oai5gcn . --wait
oc describe pod &> pod-describe-logs.logs
#Check that deployment is ready
export READY_PODS=$(oc get pods -o custom-columns=NAMESPACE:metadata.namespace,POD:metadata.name,PodIP:status.podIP,READY:status.containerStatuses[*].ready | grep -v NAME | wc -l)
export TOTAL_PODS=$(oc get pods | grep -v NAME | wc -l)
## when READY_PODS==TOTAL_PODS the deployment is complete
```

By default the time-out for `helm install --wait` is 5 mins, if you want to reduce or increase it add this flag `--timeout xxx`, for example `--timeout 8m`

The above commands make sure that the network functions are up and running using the healthcheck script present in `Dockerfile` of each network function. In kubernetes it is known as readiness probe. Every network function helm-chart has a variable `readinessProbe` to turn on and off this functionality.

**NOTE**: You might need to add `sleep` after helm because it can time for PFCP heartbeats.

### 1.3 Check if the Deployment is correct

This is only needed to be sure that SMF and UPF are sharing the PFCP heartbeat, the required network functions have registered to NRF else there is no point going further.

All the network functions register to NRF (`register_nf` in `config.yaml`), but the check below only looks at AMF, SMF and UPF.

Make a shell script out of the below lines and run it on the openshift client which has access to `helm command`

```shell
#!/bin/bash
#to check AMF-NRF registration
oc project <PROJECT>
#the NFs use HTTP/2, so query the NRF service from inside the NRF pod
NRF_URL=$(oc get svc oai-nrf -o json | jq -r ".status.loadBalancer.ingress[0].ip")
NRF_POD=$(oc get pods -l app.kubernetes.io/name=oai-nrf -o jsonpath="{.items[*].metadata.name}")
AMF_namf=$(oc exec $NRF_POD -- curl -s --http2-prior-knowledge -X GET "http://$NRF_URL/nnrf-nfm/v1/nf-instances?nf-type=AMF" | jq -r ._links.item[0].href)
#to check SMF-NRF registration
SMF_nsmf=$(oc exec $NRF_POD -- curl -s --http2-prior-knowledge -X GET "http://$NRF_URL/nnrf-nfm/v1/nf-instances?nf-type=SMF" | jq -r ._links.item[0].href)
#to check UPF-NRF registration
UPF_nupf=$(oc exec $NRF_POD -- curl -s --http2-prior-knowledge -X GET "http://$NRF_URL/nnrf-nfm/v1/nf-instances?nf-type=UPF" | jq -r ._links.item[0].href)
if [[ -z $AMF_namf ]] || [[ -z $UPF_nupf ]] || [[ -z $SMF_nsmf ]]; then
      echo "There is a problem with NRF connection"
      exit 1
fi
UPF_POD=$(oc get pods | grep oai-upf | awk {'print $1'})
UPF_log1=$(oc logs $UPF_POD upf | grep 'Received SX HEARTBEAT REQUEST')
UPF_log2=$(oc logs $UPF_POD upf | grep 'handle_receive(16 bytes)')
if [[ -z $UPF_log1 ]] || [[ -z $UPF_log2 ]] ; then
      echo "PFCP Heartbeat Issue"
      exit 1
fi
echo "Core network is healthy"
```
If the output is `Core network is healthy` then you can move forward

## 2. Start the gNB

Login to the gNB server and start the gNB

```shell
#assuming my current directory is the root of this repository
cd ci-scripts/docker-compose/gnb-ci-testbed
docker-compose up -d
```
Check if gNB is connected to the AMF, because if not there is no point in moving forward, you can directly go to step 4 collect the artifacts

```shell
docker logs sa-b210-gnb | grep 'Received NGAP_REGISTER_GNB_CNF: associated AMF 1' | wc -l
```

## 3. Perform the Test

Login to the UE server,


```shell
#assuming my current directory is the root of this repository
cd ci-scripts/cots-ue-mbim-scripts
#start the UE
sudo ./start.sh
#if echo $? is 0 then testing was Successful Testing
#Stop the UE
sudo ./stop.sh
#Perform the test again after 5 seconds gap
sleep 5
sudo ./start.sh
#if echo $? is 0 then testing was Successful Testing
#Stop the UE
sudo ./stop.sh
```

You can re-direct the output to file in case the logs are necessary else they will be printed on the console

It is important to check twice to be sure everything works.

Stop the gNB before collecting artifacts, login to gnb machine

```shell
cd ci-scripts/docker-compose/gnb-ci-testbed
docker-compose stop -t2
```

## 4. Collect the Artifacts

First collect logs and pcap for core network functions

Login to the openshift client

Collect logs and pcap using below shell script

```shell
#!/bin/bash
oc project <PROJECT>
NRF=$(oc get pods | grep oai-nrf | awk {'print $1'})
UDR=$(oc get pods | grep oai-udr | awk {'print $1'})
UDM=$(oc get pods | grep oai-udm | awk {'print $1'})
AUSF=$(oc get pods | grep oai-ausf | awk {'print $1'})
AMF=$(oc get pods | grep oai-amf | awk {'print $1'})
SMF=$(oc get pods | grep oai-smf | awk {'print $1'})
UPF=$(oc get pods | grep oai-upf | awk {'print $1'})
folder_name=logs_$(date +"%d-%m-%y-%H-%M-%S")

echo "creating a folder for storing logs, folder name:" $folder_name
mkdir -p $folder_name
echo "getting $NRF logs"
oc logs $NRF nrf &> $folder_name/nrf.logs
echo "getting $UDR logs"
oc logs $UDR udr &> $folder_name/udr.logs
echo "getting $UDM logs"
oc logs $UDM udm &> $folder_name/udm.logs
echo "getting $AUSF logs"
oc logs $AUSF ausf &> $folder_name/ausf.logs
echo "getting $AMF logs"
oc logs $AMF amf &> $folder_name/amf.logs
echo "getting $SMF logs"
oc logs $SMF smf &> $folder_name/smf.logs
echo "getting $UPF logs"
oc logs $UPF upf &> $folder_name/upf.logs
#Collect Resource Consumption (Normally the window is 5 mins)
oc get pods.metrics.k8s.io &> $folder_name/nf-resource-consumption.log
oc rsync $NRF:/pcap $folder_name/
```

Login to gNB host machine and copy gNB logs

```shell
docker logs sa-b210-gnb &> gnb.logs
```

## 5. Remove the Deployment

Stop the gNB, login to gNB machine

```shell
cd ci-scripts/docker-compose/gnb-ci-testbed
docker-compose down -t2
```

Stop the core-network functions, login to the openshift client

```shell
oc project <PROJECT>
helm uninstall oai5gcn
```

The default graceperiod for all network functions is `5 seconds` so if you want to put a time out then you can put `10 seconds`

## 6. Analyze the Artifacts

Once all the artifacts are collected to be sure that everything went perfectly fine, please check in the collected pcaps below messages are there.

Bare-minimum pcap of interest AMF and UPF.

Normally you will see below messages twice because we connected the UE twice and did ping twice.

Below messages are from AMF pcap

- NGSetupRequest
- NGSetupResponse
- InitialUEMessage, Registration request, Registration request
- DownlinkNASTransport, Identity request
- UplinkNASTransport, Identity response
- DownlinkNASTransport, Authentication request
- UplinkNASTransport, Authentication response
- DownlinkNASTransport, Security mode command
- UplinkNASTransport, Security mode complete, Registration request
- UERadioCapabilityInfoIndication
- UplinkNASTransport, Registration complete
- PDU session establishment request
- PDUSessionResourceSetupRequest, DL NAS transport, PDU session establishment accept
- PDUSessionResourceSetupResponse
- UplinkNASTransport, UL NAS transport, PDU session release request (Regular deactivation)
- PDUSessionResourceReleaseCommand, DL NAS transport, PDU session release command (Regular deactivation)
- PDUSessionResourceReleaseResponse
- UplinkNASTransport, UL NAS transport, PDU session release complete, UplinkNASTransport, Deregistration request (UE originating)
- SHUTDOWN
- SHUTDOWN ACK
- SHUTDOWN_COMPLETE

In UPF pcap you should see GTP packets minimum 8 times because the ping was 4 packets
