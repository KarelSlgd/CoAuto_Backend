import json
import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']


def lambda_handler(event, context):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    users = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_rate, value, comment, id_auto, id_user FROM rate")
            result = cursor.fetchall()

            for row in result:
                user = {
                    'id_rate': row[0],
                    'value': row[1],
                    'comment': row[2],
                    'id_auto': row[3],
                    'id_user': row[4]
                }
                users.append(user)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get rate",
            "data": users
        }),
    }
