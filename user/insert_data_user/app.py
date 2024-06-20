import re
import json
from user.insert_data_user.connection import get_connection


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
    lastname = body.get('lastname')
    id_role = body.get('id_role')

    if not email or not name or not id_role or not lastname:
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

    if len(name) > 50:
        return {
            'statusCode': 400,
            'body': 'Name exceeds 50 characters.'
        }

    if not verify_role(id_role):
        return {
            'statusCode': 400,
            'body': 'Role does not exist.'
        }

    response = insert_into_user(email, name, lastname, id_role)
    return response


def insert_into_user(email, name, lastname, role):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, name, lastname, id_role, id_status) VALUES (%s, %s, %s, %s, 1)"
            cursor.execute(insert_query, (email, name, lastname, role))
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
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_role FROM role WHERE id_role = %s", role)
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        return False
    finally:
        connection.close()
