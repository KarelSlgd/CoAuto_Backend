import pymysql
import os
import re

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']

def lambda_handler(event, context):
    email = event['email']
    name = event['name']
    phone_number = event['phone_number']
    profile_image_url = event['profile_image_url']
    role = event['role']
    password = event['password']

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

    if len(email) >= 30:
        return {
            'statusCode': 400,
            'body': 'Email exceeds 50 characters.'
        }

    if not re.match(r'^[0-9]+$', phone_number):
        return {
            'statusCode': 400,
            'body': 'Phone number must be numeric.'
        }

    if len(phone_number) >= 10:
        return {
            'statusCode': 400,
            'body': 'Phone number exceeds 10 characters.'
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'body': 'Name exceeds 50 characters.'
        }

    response = insert_into_user(email, name, phone_number, profile_image_url, role, password)

    return response


def insert_into_user(email, name, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(host=rds_host, user=rds_user, passwd=rds_password, db=rds_db)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, name, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s, SHA2(%s, 256))"
            cursor.execute(insert_query, (email, name, phone_number, profile_image_url, role, password))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'An error occurred: {}'.format(e)
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Record inserted successfully.'
    }