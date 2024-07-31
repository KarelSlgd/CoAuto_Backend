import boto3
import pymysql
from botocore.exceptions import ClientError
import base64
import json
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def get_connection():
    secrets = get_secret()
    try:
        connection = pymysql.connect(
            host=secrets['HOST'],
            user=secrets['USERNAME'],
            password=secrets['PASSWORD'],
            database=secrets['DB_NAME']
        )
    except Exception as e:
        raise e

    return connection


def get_secret():
    secret_name = 'COAUTO'
    region_name = 'us-east-1'

    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
    except ClientError as e:
        raise e

    return json.loads(secret)


def handle_response(error, message, status_code):
    return {
        'statusCode': status_code,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': status_code,
            'message': message,
            'error': str(error)
        })
    }


def handle_response_success(status_code, message, data):
    return {
        'statusCode': status_code,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': status_code,
            'message': message,
            'data': data
        })
    }


def get_jwt_claims(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token inválido")

        payload_encoded = parts[1]
        payload_decoded = base64.b64decode(payload_encoded + "==")
        claims = json.loads(payload_decoded)

        return claims

    except ValueError as e:
        raise e
