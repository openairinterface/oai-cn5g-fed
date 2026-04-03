#/bin/bash
# SPDX-License-Identifier: MIT

set -eo pipefail
## Usage ./ci-scripts/checkHelmChartsMinikube.sh $tag $parent_repo
# TAG=$1
# PARENT=$2
NAMESPACE='helm-trial'

if ! command -v helm &> /dev/null
then
    echo "helm is not installed, install it from --> https://helm.sh/docs/intro/install/"
    exit 1
fi

function cleanup {
  echo "Removing minikube"
  minikube delete
}

function deployCore {

  namespace=$1
  helm dependency update charts/oai-5g-core/oai-5g-basic
  helm install basic charts/oai-5g-core/oai-5g-basic -n $namespace
  sleep 1
  ## Wait for all core network NFs to be ready
  echo "----------Sanity Check: Ongoing ----------"
  s=("basic-mysql" "oai-amf" "oai-smf" "oai-nrf" "oai-udr" "oai-udm" "oai-ausf" "oai-upf") 
  for n in ${s[@]}; 
  do
    kubectl wait --for=condition=ready pod -n $namespace -l app.kubernetes.io/name=$n --timeout=3m ||  check="KO"
    if [[ $check == "KO" ]]; then
      echo "----------Sanity Check $n: KO ----------"
      exit 1
    else
      echo "----------Sanity Check $n: OK ----------"
    fi
  done
}

function checkCoreConfiguration {

  namespace=$1
  echo "----------Checking Core Configuration: Ongoing ----------"
  kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-smf'| awk '{print $1}') | grep 'handle_receive'
  kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-upf'| awk '{print $1}') | grep 'handle_receive'
  echo "----------PFCP Session: OK ----------"
  s=("AMF" "SMF" "UPF" "UDR" "UDM" "AUSF") 
  for n in ${s[@]}; 
  do
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-nrf'| awk '{print $1}') | grep OAI-$n ||  check="KO"
    if [[ $check == "KO" ]]; then
      echo "----------NRF-$n: KO ----------"
      exit 1
    else
      echo "----------NRF-$n: OK ----------"
    fi
  done

}

function useCaseOneTesting {

  namespace=$1
  check="OK"
  echo "----------Testing Use Case 1 Monolithic RAN: Ongoing ----------"
  helm install gnb charts/oai-5g-ran/oai-gnb -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-gnb --timeout=5m -n $namespace
  for n in {1..5};
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-gnb'| awk '{print $1}') | grep 'associated AMF 1' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------NGAP Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------NGAP Setup: KO ----------"
    exit 1
  fi
  for n in {1..5};
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-gnb'| awk '{print $1}') | grep 'I Frame.Slot' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------RFSimulator Started: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------RFSimulator Setup: KO ----------"
    exit 1
  fi
  sleep 2
  helm install nrue charts/oai-5g-ran/oai-nr-ue -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-nr-ue --timeout=5m -n $namespace
  sleep 2
  for n in {1..5}; 
  do
    sleep 1
    kubectl exec -it -n $namespace $(kubectl get pods -n $namespace  -l app.kubernetes.io/name=oai-nr-ue | grep 'nr-ue' | awk '{print $1}') -- ifconfig | grep 12.1.1 ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE Connected: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE Connected: KO ----------"
    exit 1
  fi
  kubectl exec -it -n $namespace $(kubectl get pods -n $namespace -l app.kubernetes.io/name=oai-nr-ue | grep 'nr-ue' | awk '{print $1}') -- ping -I oaitun_ue1 12.1.1.1 -c4 ||  check="KO"
  if [[ $check == "KO" ]]; then
    echo "----------Ping to UPF: KO ----------"
    exit 1
  else
    echo "----------Ping to UPF: OK ----------"
  fi
  helm uninstall nrue -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep 'oai-amf'| awk '{print $1}') | grep '5GMM-DEREGISTERED' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE De-registered: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE De-registered: KO ----------"
    exit 1
  fi
  helm uninstall gnb -n $namespace
  for n in {1..10};
  do
    sleep 1
    check="OK"
    kubectl get pods -n $namespace | grep 'oai-gnb' ||  check="KO"
    if [[ $check == "KO" ]]; then
      echo "----------gNB Removed: OK ----------"      
      check="OK"
      break
    else
      continue
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------gNB Removed: KO ----------"
    exit 1
  fi
}

function useCaseTwoTesting {

  namespace=$1
  check="OK"
  echo "----------Testing Use Case 2 F1 Split RAN: Ongoing ----------"
  helm install cu charts/oai-5g-ran/oai-cu -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-cu --timeout=5m -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-cu| awk '{print $1}') | grep 'associated AMF 1' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------NGAP Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------NGAP Setup: KO ----------"
    exit 1
  fi
  helm install du charts/oai-5g-ran/oai-du -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-du --timeout=5m -n $namespace
  sleep 2
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-cu| awk '{print $1}') | grep 'Received F1 Setup Request' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------F1 Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------F1 Setup: KO ----------"
    exit 1
  fi
  for n in {1..5};
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-du| awk '{print $1}') | grep 'I Frame.Slot' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------RFSimulator Started: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------RFSimulator Setup: KO ----------"
    exit 1
  fi
  sleep 5
  helm install nrue charts/oai-5g-ran/oai-nr-ue -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-nr-ue --timeout=5m -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl exec -it -n $namespace $(kubectl get pods -n $namespace  -l app.kubernetes.io/name=oai-nr-ue | grep nr-ue | awk '{print $1}') -- ifconfig | grep 12.1.1 ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE Connected: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE Connected: KO ----------"
    exit 1
  fi
  kubectl exec -it -n $namespace $(kubectl get pods -n $namespace -l app.kubernetes.io/name=oai-nr-ue | grep nr-ue | awk '{print $1}') -- ping -I oaitun_ue1 12.1.1.1 -c4 ||  check="KO"
  if [[ $check == "KO" ]]; then
    echo "----------Ping to UPF: KO ----------"
    exit 1
  else
    echo "----------Ping to UPF: OK ----------"
  fi
  helm uninstall nrue -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-amf| awk '{print $1}') | grep '5GMM-DEREGISTERED' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE De-registered: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE De-registered: KO ----------"
    exit 1
  fi
  helm uninstall cu -n $namespace
  helm uninstall du -n $namespace
}


function useCaseThreeTesting {

  namespace=$1
  check="OK"
  echo "----------Testing Use Case 3 E1-F1 Split RAN: Ongoing ----------"
  helm install cucp charts/oai-5g-ran/oai-cu-cp -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-cu-cp --timeout=5m -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-cu-cp| awk '{print $1}') | grep 'associated AMF 1' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------NGAP Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------NGAP Setup: KO ----------"
    exit 1
  fi
  helm install cuup charts/oai-5g-ran/oai-cu-up -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-cu-up --timeout=5m -n $namespace
  sleep 50
  for n in {1..5};
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-cu-cp| awk '{print $1}') | grep "Accepting new CU-UP ID" || check="KO"
    echo "Testing--------------"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------E1 Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------E1 Setup: KO ----------"
    exit 1
  fi
  helm install du charts/oai-5g-ran/oai-du -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-du --timeout=5m -n $namespace
  sleep 2
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-cu-cp| awk '{print $1}') | grep 'Received F1 Setup Request' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------F1 Setup: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------F1 Setup: KO ----------"
    exit 1
  fi
  for n in {1..5};
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-du| awk '{print $1}') | grep 'I Frame.Slot' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------RFSimulator Started: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------RFSimulator Setup: KO ----------"
    exit 1
  fi
  sleep 5
  helm install nrue charts/oai-5g-ran/oai-nr-ue -n $namespace
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=oai-nr-ue --timeout=5m -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl exec -it -n $namespace $(kubectl get pods -n $namespace  -l app.kubernetes.io/name=oai-nr-ue | grep nr-ue | awk '{print $1}') -- ifconfig | grep 12.1.1 ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE Connected: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE Connected: KO ----------"
    exit 1
  fi
  kubectl exec -it -n $namespace $(kubectl get pods -n $namespace -l app.kubernetes.io/name=oai-nr-ue | grep nr-ue | awk '{print $1}') -- ping -I oaitun_ue1 12.1.1.1 -c4 ||  check="KO"
  if [[ $check == "KO" ]]; then
    echo "----------Ping to UPF: KO ----------"
    exit 1
  else
    echo "----------Ping to UPF: OK ----------"
  fi
  helm uninstall nrue -n $namespace
  for n in {1..5}; 
  do
    sleep 1
    kubectl logs -n $namespace $(kubectl get pods -n $namespace | grep oai-amf| awk '{print $1}') | grep '5GMM-DEREGISTERED' ||  check="KO"
    if [[ $check == "KO" ]]; then
      if  [[ $check == "KO" ]] &&  [[ $n != 5 ]]; then check="OK";continue;fi
    else
      echo "----------UE De-registered: OK ----------"
      break
    fi
  done
  if [[ $check == "KO" ]]; then
    echo "----------UE De-registered: KO ----------"
    exit 1
  fi
  helm uninstall cucp -n $namespace
  helm uninstall cuup -n $namespace
  helm uninstall du -n $namespace
}


trap cleanup EXIT
## Testing only operators without nephio
echo "----------Test Started ----------"
# # create infrastructure
./ci-scripts/create-cluster.sh
#create namespace
kubectl create ns $NAMESPACE
#Deploy core network
deployCore $NAMESPACE
##Configuration check
checkCoreConfiguration $NAMESPACE
#test usecase 1
useCaseOneTesting $NAMESPACE
#test usecase 2
sleep 30
useCaseTwoTesting $NAMESPACE
sleep 30
useCaseThreeTesting $NAMESPACE
## Clean up
kubectl delete ns $NAMESPACE
#minikube delete
echo "----------Test Done ----------"
