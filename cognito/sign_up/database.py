from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import pymysql
import json
import boto3


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
        return {
            'statusCode': 500,
            'body': f'Failed to connect to database: {str(e)}'
        }

    return connection


def get_secret():
    secret_name = "COAUTO"
    region_name = "us-east-1"

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
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return json.loads(secret)


def calculate_secret_hash(client_id, secret_key, username):
    message = username + client_id
    dig = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()
