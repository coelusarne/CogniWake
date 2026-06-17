# backend/repositories/LogsRepository.py
# Imports
from repositories.Database import Database

class LogsRepository:
    @staticmethod
    def add_system_log(source, message):
        sql = "INSERT INTO SystemLogs (timestamp, source, message) VALUES (NOW(), %s, %s)"
        Database.execute_sql(sql, [source, message])

    @staticmethod
    def get_system_logs(limit=100):
        sql = "SELECT * FROM SystemLogs ORDER BY timestamp DESC LIMIT %s"
        return Database.get_rows(sql, [limit])
    @staticmethod
    def clear_system_logs():
        sql = "DELETE FROM SystemLogs"
        Database.execute_sql(sql)