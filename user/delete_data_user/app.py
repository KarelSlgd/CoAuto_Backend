import json
from connection import get_connection


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    id_user = body.get('id_user')
    id_status = body.get('id_status')

    if not id_user or not id_status:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    response = delete_user(id_user, id_status)

    return response


def delete_user(id, status):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE user SET id_status=%s WHERE id_user=%s", (status, id))
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
        'body': 'User deleted successfully.'
    }
