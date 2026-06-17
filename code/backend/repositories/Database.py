# backend/repositories/Database.py
# Imports
from mysql import connector
import os

class Database:
    @staticmethod
    def __open_connection():
        try:
            db = connector.connect(
                option_files=os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '../config.py')
                ),
                autocommit=False
            )
            cursor = db.cursor(dictionary=True, buffered=True)
            return db, cursor
        except connector.Error as err:
            print(err)
            return

    @staticmethod
    def get_rows(sqlQuery, params=None):
        result = None
        db, cursor = Database.__open_connection()
        try:
            cursor.execute(sqlQuery, params)
            result = cursor.fetchall()
            cursor.close()
            db.close()
        except Exception as error:
            print(error)
            result = None
        finally:
            return result

    @staticmethod
    def get_one_row(sqlQuery, params=None):
        db, cursor = Database.__open_connection()
        try:
            cursor.execute(sqlQuery, params)
            result = cursor.fetchone()
            cursor.close()
            db.close()
        except Exception as error:
            print(error)
            result = None
        finally:
            return result
        
    @staticmethod
    def execute_sql(sqlQuery, params=None):
        result = None
        db, cursor = Database.__open_connection()
        try:
            cursor.execute(sqlQuery, params)
            db.commit()
            result = cursor.lastrowid
            if result == 0:
                result = cursor.rowcount
        except connector.Error as error:
            db.rollback()
            print(error)
            result = None
        finally:
            cursor.close()
            db.close()
            return result