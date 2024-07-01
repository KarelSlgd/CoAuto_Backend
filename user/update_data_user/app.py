import json
from connection import get_connection
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Invalid request body.'
        }

    id_user = body.get('id_user')
    name = body.get('name')
    lastname = body.get('lastname')

    if not id_user or not name:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Name exceeds 50 characters.'
        }

    response = update_user(id_user, name, lastname)

    return response


def update_user(id_user, name, lastname):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user SET name=%s, lastname=%s WHERE id_user=%s",
                (name, lastname, id_user)
            )
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'Failed to update user: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'User updated successfully.'
    }
