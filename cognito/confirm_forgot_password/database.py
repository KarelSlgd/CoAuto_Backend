from botocore.exceptions import ClientError
import json
import boto3
import hmac
import hashlib
import base64

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


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
        raise e

    return json.loads(secret)


def calculate_secret_hash(client_id, secret_key, username):
    message = username + client_id
    dig = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


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
