"""
test_wifi.py - scan for nearby Wi-Fi networks.

Confirms the ESP32 Wi-Fi radio works. Does not connect; just lists the
SSIDs it can see with signal strength.

Run:  mpremote run tests/test_wifi.py
"""

import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

print('scanning...')
nets = wlan.scan()  # (ssid, bssid, channel, rssi, security, hidden)

if not nets:
    print('no networks found (radio may still be warming up)')
else:
    print('found %d networks' % len(nets))
    print('%-24s %6s %4s %s' % ('SSID', 'RSSI', 'CH', 'SEC'))
    for ssid, bssid, channel, rssi, security, hidden in sorted(
        nets, key=lambda n: n[3], reverse=True
    ):
        print('%-24s %6d %4d %s' % (
            ssid.decode() if isinstance(ssid, bytes) else ssid,
            rssi, channel, security
        ))

wlan.active(False)
print('done')
