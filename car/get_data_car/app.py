import json
import pymysql
import os
import base64

rds_host = os.getenv('RDS_HOST')
rds_user = os.getenv('DB_USERNAME')
rds_password = os.getenv('DB_PASSWORD')
rds_db = os.getenv('DB_NAME')


def lambda_handler(event, context):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    headers = event.get('headers', {})
    token = headers.get('Authorization')

    if not token:
        return {
            'statusCode': 401,
            'body': json.dumps('Missing token.')
        }

    try:
        decoded_token = get_jwt_claims(token)
        role = decoded_token.get('cognito:groups')
        if role == 'ClientUserGroup':
            return {
                'statusCode': 403,
                'body': json.dumps('Access denied. Role cannot be client.')
            }

    except Exception as e:
        return {
            'statusCode': 401,
            'body': json.dumps(f'Invalid token: {str(e)}')
        }

    cars = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status")
            result = cursor.fetchall()

            for row in result:
                car = {
                    'id_auto': row[0],
                    'model': row[1],
                    'brand': row[2],
                    'year': row[3],
                    'price': row[4],
                    'type': row[5],
                    'fuel': row[6],
                    'doors': row[7],
                    'engine': row[8],
                    'height': row[9],
                    'width': row[10],
                    'length': row[11],
                    'description': row[12],
                    'status': row[13]
                }
                cars.append(car)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get cars",
            "data": cars
        }),
    }


def get_jwt_claims(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_encoded = parts[1]
        payload_decoded = base64.b64decode(payload_encoded + "==")
        claims = json.loads(payload_decoded)

        return claims

    except (ValueError, json.JSONDecodeError) as e:
        return None
