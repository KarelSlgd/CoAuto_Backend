import pymysql
import logging

logging.basicConfig(level=logging.INFO)


def connect_to_db(host, user, password, database):
    try:
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        logging.info("Connected to MySQL database")
        return connection
    except Exception as e:
        logging.error(e)
        return None


def execute_query(connection, query):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    except Exception as e:
        logging.error(e)
        return None


def close_connection(connection):
    if connection:
        connection.close()
        logging.info("Connection closed")