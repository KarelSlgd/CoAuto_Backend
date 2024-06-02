import json
import pymysql

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
