import json
import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    id_auto = event['queryStringParameters'].get('id_auto')

    if not id_auto:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing id_auto parameter.'
            })
        }

    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    rates = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_rate, value, comment, id_auto, id_user FROM rate WHERE id_auto = %s", (id_auto,))
            result = cursor.fetchall()

            for row in result:
                rate = {
                    'id_rate': row[0],
                    'value': row[1],
                    'comment': row[2],
                    'id_auto': row[3],
                    'id_user': row[4]
                }
                rates.append(rate)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Rates retrieved successfully.',
            'data': rates
        })
    }
