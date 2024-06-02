import json
import pymysql

rds_host = 'integradora-desarrollo.cd4gi2og06nk.us-east-2.rds.amazonaws.com'
name = 'root'
password = 'superroot'
db_name = 'coauto'


def lambda_handler(event, context):
    connection = pymysql.connect(
        host=rds_host,
        user=name,
        password=password,
        database=db_name
    )

    users = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, phone_number, profile_image_url, role FROM user")
            result = cursor.fetchall()

            for row in result:
                user = {
                    'id': row[0],
                    'email': row[1],
                    'phone_number': row[2],
                    'profile_image_url': row[3],
                    'role': row[4]
                }
                users.append(user)

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Error users",
                "error": str(e)
            }),
        }

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get users",
            "data": users
        }),
    }
