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
    id_status = body.get('id_status')

    if not id_user or not id_status:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    response = delete_user(id_user, id_status)

    return response


def delete_user(id_user, status):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE user SET id_status=%s WHERE id_user=%s", (status, id_user))
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
        'body': 'User deleted successfully.'
    }
