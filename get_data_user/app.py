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
            cursor.execute("SELECT id_user, email, u.name AS nameUser, profile_image, r.name as nameRole, s.value FROM user u INNER JOIN role r ON u.id_role = r.id_role INNER JOIN status s ON u.id_status = s.id_status;")
            result = cursor.fetchall()

            for row in result:
                user = {
                    'id_user': row[0],
                    'email': row[1],
                    'nameUser': row[2],
                    'profile_image': row[3],
                    'nameRole': row[4],
                    'status': row[5]
                }
                users.append(user)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get users",
            "data": users
        }),
    }
