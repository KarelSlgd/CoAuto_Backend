from dotenv import load_dotenv
import json
import pymysql
import os

load_dotenv()

rds_host = os.getenv('RDS_HOST')
rds_user = os.getenv('DB_USERNAME')
rds_password = os.getenv('DB_PASSWORD')
rds_db = os.getenv('DB_NAME')


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    id_auto = event['queryStringParameters'].get('id_auto')
    #body = json.loads(event['body'])
    #id_auto = body['id_auto']

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
            cursor.execute("SELECT id_rate, value, comment, a.model, a.brand, u.name, u.lastname FROM rate r INNER JOIN auto a ON r.id_auto=a.id_auto INNER JOIN user u ON r.id_user=u.id_user WHERE a.id_auto = %s", (id_auto,))
            result = cursor.fetchall()

            for row in result:
                rate = {
                    'id_rate': row[0],
                    'value': row[1],
                    'comment': row[2],
                    'model': row[3],
                    'brand': row[4],
                    'name': row[5],
                    'lastname': row[6]
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
