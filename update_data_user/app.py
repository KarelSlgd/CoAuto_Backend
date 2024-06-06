import pymysql
import os
import json

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    id_user = body.get('id')
    name = body.get('name')
    phone_number = body.get('phone_number')
    profile_image = body.get('profile_image')
    role = body.get('role')
    password = body.get('password')

    if not id_user or not name or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'body': 'Name exceeds 50 characters.'
        }

    if len(phone_number) < 10:
        return {
            'statusCode': 400,
            'body': 'Phone number must be 10 characters.'
        }

    if len(phone_number) > 10:
        return {
            'statusCode': 400,
            'body': 'Phone number exceeds 10 characters.'
        }

    if not verify_role(role):
        return {
            'statusCode': 400,
            'body': 'Role does not exist.'
        }

    response = update_user(id_user, name, profile_image, role, password)

    return response


def update_user(id_user, name, profile_image, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user SET name=%s, profile_image=%s, id_role=%s, password=SHA2(%s, 256) WHERE id=%s",
                (name, profile_image, role, password, id_user)
            )
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Failed to update user: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'User updated successfully.'
    }


def verify_role(role):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_role FROM role WHERE id_role = %s", role)
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        return False
    finally:
        connection.close()
