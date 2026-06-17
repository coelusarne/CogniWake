# backend/repositories/SettingsRepository.py
# Imports
from repositories.Database import Database

class SettingsRepository:
    @staticmethod
    def get_value(key: str, default: str = None):
        """Get value of specific settingKey"""
        sql = "SELECT settingValue FROM Settings WHERE SettingKey = %s LIMIT 1"
        row = Database.get_one_row(sql, [key])

        if not row:
            return default

        return row["settingValue"]

    @staticmethod
    def set_value(key: str, value: str):
        """Set value of specific settingKey"""
        existing = SettingsRepository.get_value(key)

        if existing is None:
            sql = "INSERT INTO Settings (SettingKey, settingValue) VALUES (%s, %s)"
            Database.execute_sql(sql, [key, value])
        else:
            sql = "UPDATE Settings SET settingValue = %s WHERE SettingKey = %s"
            Database.execute_sql(sql, [value, key])

    @staticmethod
    def get_theme_color():
        """returns the theme color"""
        return SettingsRepository.get_value("theme_color", "#b2b2b3")

    @staticmethod
    def set_theme_color(color: str):
        """sets the theme color"""
        SettingsRepository.set_value("theme_color", color)

    @staticmethod
    def get_network_mode():
        """Returns network mode"""
        return SettingsRepository.get_value("network_mode", "ap")

    @staticmethod
    def set_network_mode(mode: str):
        """sets the network mode"""
        SettingsRepository.set_value("network_mode", mode)

    @staticmethod
    def get_wifi_ssid():
        """returns the current wifi_ssid"""
        return SettingsRepository.get_value("wifi_ssid", "")

    @staticmethod
    def set_wifi_ssid(ssid: str):
        """sets the wifi ssid"""
        SettingsRepository.set_value("wifi_ssid", ssid)

    @staticmethod
    def get_time_mode():
        """
        returns the current time mode
        """
        return SettingsRepository.get_value("time_mode", "manual")

    @staticmethod
    def set_time_mode(mode: str):
        """
        sets the time mode(shocker)
        """
        SettingsRepository.set_value("time_mode", mode)

    @staticmethod
    def get_manual_datetime():
        """
        returns the manual datetime
        """
        return SettingsRepository.get_value("manual_datetime", "")

    @staticmethod
    def set_manual_datetime(value: str):
        """
        sets the manual datetime...
        """
        SettingsRepository.set_value("manual_datetime", value)

    @staticmethod
    def get_username():
        """returns the current username"""
        return SettingsRepository.get_value("username", "")

    @staticmethod
    def set_username(value: str):
        """Sets the username"""
        SettingsRepository.set_value("username", value)

    @staticmethod
    def get_weather():
        """Gets the weather config"""
        return SettingsRepository.get_value("weather", "")
    
    @staticmethod
    def set_weather(value: str):
        """Sets the weather config"""
        return SettingsRepository.set_value("weather", value)
    
    @staticmethod
    def get_weather_details():
        """Gets the weather details"""
        return SettingsRepository.get_value("weather_details", "")

    @staticmethod
    def set_weather_details(value: str):
        """Sets the weather details"""
        return SettingsRepository.set_value("weather_details", value)
