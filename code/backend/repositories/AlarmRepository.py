# backend/repositories/AlarmRepository.py
# Imports
from repositories.Database import Database

class AlarmRepository:
    @staticmethod
    def read_alarms():
        """Return every alarm"""
        sql = "SELECT *FROM Alarms ORDER BY timestamp"
        return Database.get_rows(sql)

    @staticmethod
    def read_active_alarms():
        """Returns active alarms"""
        sql = "SELECT * FROM Alarms WHERE active = 1"
        return Database.get_rows(sql)

    @staticmethod
    def read_alarm_by_id(alarm_id):
        """Returns specific alarm"""
        sql = "SELECT * FROM Alarms WHERE alarmID = %s"
        params = [alarm_id]
        return Database.get_one_row(sql, params)

    @staticmethod
    def create_alarm(timestamp, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes):
        """Creates an alarm"""
        sql = "INSERT INTO Alarms (timestamp, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        params = [timestamp, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes]
        return Database.execute_sql(sql, params)

    @staticmethod
    def delete_alarm(alarmID):
        """Delete alarm"""
        sql = "DELETE FROM Alarms WHERE alarmID = %s"
        params = [alarmID]
        return Database.execute_sql(sql, params)

    @staticmethod
    def update_alarm_status(alarmID, active):
        """Update alarm status w/ id"""
        sql = "UPDATE Alarms SET active = %s WHERE alarmID = %s"
        params = [active, alarmID]
        return Database.execute_sql(sql, params)

    @staticmethod
    def update_alarm(alarmID, timestamp, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes):
        """Update alarm specifics"""
        sql = "UPDATE Alarms SET timestamp = %s, label = %s, difficultyID = %s, days_bitmask = %s, active = %s, snooze_enabled = %s, snooze_minutes = %s WHERE alarmID = %s"
        params = [timestamp, label, difficultyID, days_bitmask, active, snooze_enabled, snooze_minutes, alarmID]
        return Database.execute_sql(sql, params)
    @staticmethod
    def clear_alarms():
        sql = "DELETE FROM Alarms"
        Database.execute_sql(sql)