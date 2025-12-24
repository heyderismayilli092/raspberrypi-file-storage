#!/bin/bash

# available network interfaces are being retrieved
WIFI_INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -E '^wlo|^wlan|^wlp')
ETH_INTERFACES=$(ip -o link show | awk -F': ' '{print $2}' | grep -E '^eth|^eno|^enp')

get_ip() {
    ip -4 addr show "$1" | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1
}

ACTIVE_IFACE=""
IP_ADDR=""

# Wi-Fi interfaces are sorted and checked
for IFACE in $WIFI_INTERFACES; do
    IP=$(get_ip "$IFACE")
    if [[ -n "$IP" ]]; then
        ACTIVE_IFACE="$IFACE"
        IP_ADDR="$IP"
        break
    fi
done

# check Ethernet interface
if [[ -z "$IP_ADDR" ]]; then
    for IFACE in $ETH_INTERFACES; do
        IP=$(get_ip "$IFACE")
        if [[ -n "$IP" ]]; then
            ACTIVE_IFACE="$IFACE"
            IP_ADDR="$IP"
            break
        fi
    done
fi

# if none is present, localhost is used
if [[ -z "$IP_ADDR" ]]; then
    ACTIVE_IFACE="lo"
    IP_ADDR="127.0.0.1"
fi

gunicorn -k eventlet -w 1 -b $IP_ADDR:1033 file-storage:app
