from dotenv import load_dotenv
import json
import os
from .database import connect_to_db, close_connection, execute_query

load_dotenv()


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    if 'queryStringParameters' in event:
        id_auto = event['queryStringParameters'].get('id_auto')
    else:
        body = json.loads(event.get('body', '{}'))
        id_auto = body.get('id_auto')

    if not id_auto:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing id_auto parameter.'
            })
        }

    rds_host = os.getenv('RDS_HOST')
    rds_user = os.getenv('DB_USERNAME')
    rds_password = os.getenv('DB_PASSWORD')
    rds_db = os.getenv('DB_NAME')

    connection = connect_to_db(rds_host, rds_user, rds_password, rds_db)
    query = f"SELECT id_rate, value, comment, a.model, a.brand, u.name, u.lastname FROM rate r INNER JOIN auto a ON r.id_auto=a.id_auto INNER JOIN user u ON r.id_user=u.id_user WHERE a.id_auto = {id_auto}"
    rates = []

    try:
        result = execute_query(connection, query)

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
        close_connection(connection)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Rates retrieved successfully.',
            'data': rates
        })
    }