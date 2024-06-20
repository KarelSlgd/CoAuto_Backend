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
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return {
            'statusCode': 400,
            'body': f'Invalid request body. Error: {str(e)}'
        }

    id_auto = body.get('id_auto')
    id_status = body.get('id_status')

    if id_auto is None or id_status is None:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    response = delete_car(id_auto, id_status)

    return response


def delete_car(id_auto, id_status):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE auto SET id_status=%s WHERE id_auto=%s", (id_status, id_auto))
            connection.commit()
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Failed to update auto: {str(e)}'
        }
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Auto status updated successfully.'
    }
