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
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': f'Invalid request body. Error: {str(e)}'
        }

    id_auto = body.get('id_auto')
    id_status = body.get('id_status')

    if id_auto is None or id_status is None:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    response = delete_car(id_auto, id_status)

    return response


def delete_car(id_auto, id_status):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE auto SET id_status=%s WHERE id_auto=%s", (id_status, id_auto))
            connection.commit()
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'Failed to update auto: {str(e)}'
        }
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'Auto status updated successfully.'
    }
