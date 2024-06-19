import json
import os
from common.app import get_connection
rds_host = os.getenv('RDS_HOST')
rds_user = os.getenv('DB_USERNAME')
rds_password = os.getenv('DB_PASSWORD')
rds_db = os.getenv('DB_NAME')


def lambda_handler(event, context):
    connection = get_connection()
    users = []
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_user, email, u.name AS nameUser, profile_image, r.name as nameRole, s.value FROM user u INNER JOIN role r ON u.id_role = r.id_role INNER JOIN status s ON u.id_status = s.id_status;")
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

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
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
