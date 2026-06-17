# backend/repositories/MathRepository.py
# Imports
from repositories.Database import Database

class MathRepository:
    @staticmethod
    def create_log(alarm_id: int, query: str):
        sql = """INSERT INTO MathLogs (alarmID, triggered_at, mathQuery, time_to_complete, completed) VALUES (%s, NOW(), %s, NULL, 0)"""
        return Database.execute_sql(sql, [alarm_id, query])

    @staticmethod
    def complete_log(log_id: int, time_to_complete: int):
        sql = "UPDATE MathLogs SET completed = 1, time_to_complete = %s WHERE logID = %s"
        Database.execute_sql(sql, [time_to_complete, log_id])

    @staticmethod
    def add_answer(log_id: int, attempt_number: int, answer: str, correct: int):
        sql = "INSERT INTO MathAnswers (logID, attempt_number, answer_given, correct) VALUES (%s, %s, %s, %s)"
        Database.execute_sql(sql,[log_id, attempt_number, answer, correct])

    @staticmethod
    def get_average_attempts():
        sql = "SELECT AVG(attempt_number) AS average_attempts FROM (SELECT logID, MAX(attempt_number) AS attempt_number FROM MathAnswers GROUP BY logID) attempts"
        return Database.get_one_row(sql)

    @staticmethod
    def get_average_solve_time():
        sql = "SELECT AVG(time_to_complete) AS average_time FROM MathLogs WHERE completed = 1"
        return Database.get_one_row(sql)

    @staticmethod
    def get_first_try_percentage():
        sql = """
            SELECT (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM MathLogs WHERE completed = 1)) AS percentage
            FROM (SELECT logID FROM MathAnswers WHERE correct = 1 GROUP BY logID HAVING MIN(attempt_number) = 1) first_try
        """
        return Database.get_one_row(sql)

    @staticmethod
    def get_recent_history(limit=10):
        sql = """
            SELECT
                ml.logID,
                ml.triggered_at,
                ml.mathQuery,
                ml.time_to_complete,
                md.difficultyName,
                GROUP_CONCAT(CONCAT(ma.answer_given, ':', ma.correct) ORDER BY ma.attempt_number SEPARATOR '|') AS answers
            FROM MathLogs ml
            LEFT JOIN Alarms a
                ON a.alarmID = ml.alarmID
            LEFT JOIN MathDifficulties md
                ON md.difficultyID = a.difficultyID
            LEFT JOIN MathAnswers ma
                ON ma.logID = ml.logID
            GROUP BY ml.logID, ml.triggered_at, ml.mathQuery, ml.time_to_complete, md.difficultyName
            ORDER BY ml.logID DESC
            LIMIT %s
        """
        return Database.get_rows(sql, [limit])
    @staticmethod
    def get_next_alarm():
        sql = "SELECT * FROM Alarms WHERE active = 1 ORDER BY timestamp ASC LIMIT 1"
        return Database.get_one_row(sql)
    @staticmethod
    def delete_history():
        Database.execute_sql("DELETE FROM MathAnswers")
        Database.execute_sql("DELETE FROM MathLogs")    