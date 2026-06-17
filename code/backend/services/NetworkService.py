# backend/services/NetworkService.py
# Imports
import subprocess
import socket
from repositories.SettingsRepository import SettingsRepository
from repositories.LogsRepository import LogsRepository
class NetworkService:
    """Manages the network configuration of the device"""
    AP_SSID = "CogniWake"
    AP_PASSWORD = "c0gn!wake"
    _cached_networks = []

    @staticmethod
    def _run(command):
        """Execute command"""
        return subprocess.run(command, capture_output=True, text=True, check=False)

    @staticmethod
    def get_known_wifi_ssids():
        """Return ssids from saved NetworkManager wifi connections."""
        result = NetworkService._run(["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"])
        known = set()

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            parts = line.split(":", 1)
            if len(parts) != 2:
                continue

            name, conn_type = parts[0].strip(), parts[1].strip()
            if conn_type != "802-11-wireless": # continue if not connected already
                continue

            ssid_result = NetworkService._run(["nmcli", "-g", "802-11-wireless.ssid", "connection", "show", name])

            ssid = ssid_result.stdout.strip() or name
            if ssid:
                known.add(ssid)

        return known

    @staticmethod
    def scan_networks():
        """scan availble networks"""
        known_ssids = NetworkService.get_known_wifi_ssids()
        result = NetworkService._run(["nmcli","-t","-f","SSID,SIGNAL","dev","wifi","list"])
        networks = []
        seen = set()

        for line in result.stdout.splitlines():
            if not line.strip():
                continue

            parts = line.split(":", 1)
            ssid = parts[0].strip()

            if (not ssid or ssid == NetworkService.AP_SSID or ssid in seen):
                continue

            seen.add(ssid)
            signal = "0"

            if len(parts) > 1:
                signal = parts[1].strip()

            networks.append({"ssid": ssid, "signal": signal, "known": ssid in known_ssids})

        if networks:
            NetworkService._cached_networks = networks
        return NetworkService._cached_networks[:5]
    
    @staticmethod
    def auto_connect_known_network():
        """auto connects to known networks, autoconnect is disabled on networks itself to not interfere with the AP when starting up"""
        if SettingsRepository.get_network_mode() != "wifi":
            return

        available = NetworkService.scan_networks()

        for network in available:
            if network["known"]:
                try:
                    subprocess.run(["sudo", "nmcli", "dev", "wifi", "connect", network["ssid"]],check=True)
                    SettingsRepository.set_wifi_ssid(network["ssid"])
                    LogsRepository.add_system_log("SYSTEM", f"Auto-connected to {network['ssid']}")
                    return True

                except Exception:
                    pass
                return False
            
    @staticmethod
    def get_config():
        """returns current device config"""
        return {
            "network_mode": SettingsRepository.get_network_mode(),
            "wifi_ssid": SettingsRepository.get_wifi_ssid(),
            "connected_ssid": NetworkService.get_current_connection(),
            "networks": NetworkService._cached_networks,
            "ip_address": NetworkService.get_ip_address()
        }

    @staticmethod
    def connect_wifi(ssid, password=None):
        """Method to connect to a network."""
        command = ["sudo","nmcli","dev","wifi","connect", ssid]
        if password:
            command += ["password", password]
        subprocess.run(command, check=True)
        subprocess.run(command, check=True)
        # disable autoconnect, handled by this service here
        subprocess.run(["sudo", "nmcli", "connection", "modify",ssid,"connection.autoconnect","no"], check=False)
        SettingsRepository.set_network_mode("wifi")
        SettingsRepository.set_wifi_ssid(ssid)
        LogsRepository.add_system_log("SYSTEM", f"Connected to WiFi {ssid}")

    @staticmethod
    def enable_access_point():
        """method to enable access point"""
        subprocess.run(["sudo","nmcli","dev","wifi","hotspot","ifname","wlan0","ssid",NetworkService.AP_SSID,"password", NetworkService.AP_PASSWORD], check=True)

        SettingsRepository.set_network_mode("ap")
        SettingsRepository.set_wifi_ssid("")
        LogsRepository.add_system_log("SYSTEM", "Access Point enabled")

    @staticmethod
    def refresh_networks():
        """method to refresh the list, when ap mode is on the ap is disable and the pi scans for networks, then reenables the ap"""
        current_mode = (SettingsRepository.get_network_mode())
        LogsRepository.add_system_log("SYSTEM", "Network scan started")
        if current_mode == "ap":
            subprocess.run(["sudo","nmcli","connection","down","Hotspot"])

        networks = NetworkService.scan_networks()

        if current_mode == "ap":
            NetworkService.enable_access_point()

        return networks

    @staticmethod
    def get_current_connection():
        """returns ssid of current con"""
        result = NetworkService._run(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev","wifi"])

        for line in result.stdout.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1]

        return ""

    @staticmethod
    def get_ip_address():
        """Gets the current ip address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip

        except Exception:
            current_mode = SettingsRepository.get_network_mode()
            if current_mode == "ap":
                result = NetworkService._run(["ip", "-4", "addr", "show", "wlan0"])

                for line in result.stdout.splitlines():
                    line = line.strip()

                    if line.startswith("inet "):
                        return line.split()[1].split("/")[0]
            return "IP unavailable"