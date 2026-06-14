#!/usr/bin/env bash
set -euo pipefail

SSID="${SSID:-Outbush-AI}"
PASSWORD="${PASSWORD:-outbush-field-guide}"
IFACE="${IFACE:-wlan0}"
ADDRESS="${ADDRESS:-10.42.0.1/24}"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo on the Pi. Warning: this may disconnect SSH if wlan0 is your current link." >&2
  exit 1
fi

if nmcli connection show "$SSID" >/dev/null 2>&1; then
  nmcli connection delete "$SSID"
fi

nmcli connection add type wifi ifname "$IFACE" con-name "$SSID" autoconnect no ssid "$SSID"
nmcli connection modify "$SSID" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared ipv4.addresses "$ADDRESS" ipv6.method disabled
nmcli connection modify "$SSID" wifi-sec.key-mgmt wpa-psk wifi-sec.psk "$PASSWORD"

cat <<MSG
Created NetworkManager hotspot connection '$SSID' on $IFACE.

To activate:
  sudo nmcli connection up "$SSID"

To roll back:
  sudo nmcli connection down "$SSID"

Do not activate over SSH unless you have console access or a rollback timer.
MSG
