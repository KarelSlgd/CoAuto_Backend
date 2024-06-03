import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']

def lambda_handler(event, context):
    id = event['id']
    name = event['name']
    phone_number = event['phone_number']
    profile_image_url = event['profile_image_url']
    role = event['role']
    password = event['password']

    if not id or not name or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    response = update_user(id, name, phone_number, profile_image_url, role, password)

    return response


def update_user(id, name, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE user SET name=%s, phone_number=%s, profile_image_url=%s, role=%s, password=SHA2(%s, 256) WHERE id=%s", (name, phone_number, profile_image_url, role, password, id))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Failed to update user.'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'User updated successfully.'
    }