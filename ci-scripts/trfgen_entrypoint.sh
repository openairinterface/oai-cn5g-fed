#!/usr/bin/env bash
# SPDX-License-Identifier: MIT

UPF_FQDN=${UPF_FQDN:-oai-upf}
USE_FQDN=${USE_FQDN:-no}
UE_NETWORK=${UE_NETWORK:-12.1.1.0/24}

EBPF_GW_SETUP=${EBPF_GW_SETUP:-no}
EBPF_GW_MTU=${EBPF_GW_MTU:-1460}

# Returns 0 if $1 is reachable directly on one of our interfaces, and echoes the
# interface to use. Docker's embedded DNS forwards names it does not know to the
# host's resolver, and many ISP or captive-portal resolvers answer *every* name with
# a wildcard public address. getent then "succeeds" with something like
# 195.154.179.210 and the route add fails with "Nexthop has invalid gateway".
# An on-link check is what distinguishes a real container address from that: for a
# neighbour, "ip route get" answers "<addr> dev X", for anything routed it answers
# "<addr> via <gw> dev X".
upf_addr_is_on_link() {
    local addr="$1" route_info
    route_info=$(ip -o route get "${addr}" 2>/dev/null) || return 1
    [[ "${route_info}" == *" via "* ]] && return 1
    echo "${route_info}" | sed -nE 's/.* dev ([^ ]+).*/\1/p'
    return 0
}

if [[ ${USE_FQDN} == "yes" ]];then
    # Escape hatch: skip DNS entirely when the address is known up front
    if [[ -n "${UPF_ADDR}" ]]; then
        echo -e "Using UPF address from the environment : ${UPF_ADDR}"
    else
        echo -e "Trying to resolve UPF by FQDN : $UPF_FQDN"
    fi
    x=0
    UPF_DEV=""
    while [ $x -le 50 ]
    do
        if [[ -z "${UPF_ADDR}" ]]; then
            echo -e "Try number $x"
            # Ask Docker's embedded DNS first: on a user-defined network the
            # <service>.<network> alias is resolved locally, so a wildcard upstream
            # answer is less likely to be reached at all.
            CANDIDATE=$(getent hosts "${UPF_FQDN}" | awk '{print $1; exit}')
        else
            CANDIDATE="${UPF_ADDR}"
        fi

        if [[ -n "${CANDIDATE}" ]]; then
            UPF_DEV=$(upf_addr_is_on_link "${CANDIDATE}")
            if [[ -n "${UPF_DEV}" ]]; then
                UPF_ADDR="${CANDIDATE}"
                break
            fi
            # Resolvable but not a neighbour: almost always a wildcard DNS answer,
            # or the UPF is not attached to this network yet. Keep waiting.
            echo -e "Ignoring $UPF_FQDN -> ${CANDIDATE}: not reachable on any local network"
        fi
        x=$((x + 1))
        sleep 5
    done

    if [[ -z "${UPF_DEV}" ]]; then
      echo -e "Could not resolve $UPF_FQDN to an address on a local network."
      echo -e "If your DNS resolves unknown names to a public address, set UPF_ADDR"
      echo -e "explicitly on this service, for example UPF_ADDR=192.168.70.134"
      exit 2
    fi

    echo -e "\nResolving UPF by FQDN : $UPF_FQDN - $UPF_ADDR (on ${UPF_DEV})"
    echo -e "ip route add $UE_NETWORK via $UPF_ADDR dev ${UPF_DEV}"
    ip route add "$UE_NETWORK" via "$UPF_ADDR" dev "${UPF_DEV}"
fi

if [[ ${EBPF_GW_SETUP} == "yes" ]];then
  N6_IF_NAME=(`ifconfig | grep -B1 "inet $EBPF_GW_N6_IP_ADDR" | awk '$1!="inet" && $1!="--" {print $1}' | sed -e "s@:@@"`)
  N3_IF_NAME=(`ifconfig | grep -B1 "inet $GW_N3_IP_ADDR" | awk '$1!="inet" && $1!="--" {print $1}' | sed -e "s@:@@"`)
  SGI_IF_NAME=(`ifconfig | grep -B1 "inet $GW_SGI_IP_ADDR" | awk '$1!="inet" && $1!="--" {print $1}' | sed -e "s@:@@"`)
  DEFAULT_ROUTE=(`ip route show default`)

  if [[ -n "$N6_IF_NAME" ]]; then
    echo
    echo -e "1. Disable TCP Checksum on N6 interface ($N6_IF_NAME):"
    ethtool -K $N6_IF_NAME tx off

    echo
    echo -e "2. Setup MTU ($EBPF_GW_MTU) on N6 interface ($N6_IF_NAME):"
    ifconfig $N6_IF_NAME mtu $EBPF_GW_MTU
    ifconfig $N6_IF_NAME

    echo
    echo -e "3. Add a route to UE subnet ($UE_IP_ADDRESS_POOL) via UPF N6 interface ($N6_UPF_IP_ADDR):"
    ip route add $UE_IP_ADDRESS_POOL via $N6_UPF_IP_ADDR dev $N6_IF_NAME
  else
    echo
    echo -e "N6 interface does not exist;\nThe UPF will not be able to reach the \nGateway neither the Internet"
    echo
  fi

  if [[ -n "$N3_IF_NAME" ]]; then
    echo
    echo -e "4. Disable the useless N3 interface ($N3_IF_NAME):"
    ifconfig $N3_IF_NAME down
  fi

  if [[ -n "$SGI_IF_NAME" ]]; then
    echo
    echo -e "5. Update the default route:"

    if [[ -n "$DEFAULT_ROUTE" ]]; then
      echo "Delete the default route: $DEFAULT_ROUTE"
      ip route del default
    fi

    echo -e "Sgi interface is $SGI_IF_NAME"
    ip route add default via $SGI_DEMO_OAI_ADDR
    ip route
  else
    echo -e "Sgi interface does not exist;\nThe UPF will not be able to reach the Internet"
  fi

  echo
  echo "6. Add SNAT rule to allow UE traffic to reach the internet:"
  iptables -t nat -A POSTROUTING -o $SGI_IF_NAME -s $UE_IP_ADDRESS_POOL -j SNAT --to-source $GW_SGI_IP_ADDR

fi

echo "Done setting the configuration"

if [[ ${EBPF_GW_SETUP} == "yes" ]];then
  echo
  echo -e "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo "Gateway Has the following configuration :"
  echo
  echo "                 +---------------+                      "
  echo "                 |               |                      "
  echo "  (UPF)----------|  OAI-EXT-GW   |----------- (Internet)"
  echo "              N6 |               | Sgi                  "
  echo "                 +---------------+                      "
  echo
  echo "    GW N6 Interface ----------------: (Ifname, IPv4, MTU) = (${N6_IF_NAME}, $(ip addr show "${N6_IF_NAME}" | grep -oE 'inet ([0-9]+\.){3}[0-9]+' | awk '{print $2}'), $(ip link show "$N6_IF_NAME" | awk '/mtu/ {print $5}'))"
  echo "    GW Sgi Interface ---------------: (Ifname, IPv4, MTU) = (${SGI_IF_NAME}, $(ip addr show "${SGI_IF_NAME}" | grep -oE 'inet ([0-9]+\.){3}[0-9]+' | awk '{print $2}'), $(ip link show "$SGI_IF_NAME" | awk '/mtu/ {print $5}'))"
  echo "    GW Default Route ---------------: $(ip route show default)"
  echo "    Route to UE --------------------: $(ip route show | grep -E "${UE_IP_ADDRESS_POOL}.*via ${N6_UPF_IP_ADDR}.*dev ${N6_IF_NAME}")"
  echo "    Iptables Postrouting -----------: $(iptables -t nat -L | grep -E "SNAT.*${UE_IP_ADDRESS_POOL}.*to:${GW_SGI_IP_ADDR}")"
  echo
  echo -e "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
  echo
fi

exec "$@"
