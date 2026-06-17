# backend/services/TimeService.py
# Imports
import subprocess
from repositories.SettingsRepository import SettingsRepository

class TimeService:
    """
    Manages the time configuration.
    """

    @staticmethod
    def get_config():
        """
        returns the current config
        """
        return {
            "time_mode": SettingsRepository.get_time_mode(),
            "manual_datetime": SettingsRepository.get_manual_datetime()
        }

    @staticmethod
    def enable_ntp():
        """
        enables the network time protocol
        """
        subprocess.run(["sudo","timedatectl","set-ntp","true"],check=True)

        # sync system time -> rtc
        subprocess.run(["sudo","hwclock","--systohc"],check=True)

    @staticmethod
    def set_manual_time(date_time):
        """
        sets manual time
        """
        subprocess.run(["sudo","timedatectl","set-ntp","false"],check=True)
        subprocess.run(["sudo","timedatectl","set-time",date_time],check=True)

        # sync system time -> rtc
        subprocess.run(["sudo","hwclock","--systohc"],check=True)

    @staticmethod
    def sync_from_rtc():
        """loads the rtc time into the system clock"""
        subprocess.run(["sudo","hwclock","--hctosys"],check=True)