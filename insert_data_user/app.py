import pymysql
import os
import re
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

    email = body.get('email')
    name = body.get('name')
    phone_number = body.get('phone_number')
    profile_image_url = body.get('profile_image_url')
    role = body.get('role')
    password = body.get('password')

    if not email or not name or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return {
            'statusCode': 400,
            'body': 'Invalid email format.'
        }

    if len(email) >= 50:
        return {
            'statusCode': 400,
            'body': 'Email exceeds 50 characters.'
        }

    if not re.match(r'^[0-9]+$', phone_number):
        return {
            'statusCode': 400,
            'body': 'Phone number must be numeric.'
        }

    if len(phone_number) > 10:
        return {
            'statusCode': 400,
            'body': 'Phone number exceeds 10 characters.'
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'body': 'Name exceeds 50 characters.'
        }

    if not verify_role(role):
        return {
            'statusCode': 400,
            'body': 'Role does not exist.'
        }

    response = insert_into_user(email, name, phone_number, profile_image_url, role, password)

    return response


def insert_into_user(email, name, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, name, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s, SHA2(%s, 256))"
            cursor.execute(insert_query, (email, name, phone_number, profile_image_url, role, password))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Record inserted successfully.'
    }

def verify_role(role):
    connection = pymysql.connect(host=rds_host, user=rds_user, passwd=rds_password, db=rds_db)

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM role WHERE name = %s", (role,))
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        return False
    finally:
        connection.close()
