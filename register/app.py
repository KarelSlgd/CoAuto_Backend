from dotenv import load_dotenv
import json
import boto3
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64

load_dotenv()


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
    dig = hmac.new(secret_key.encode('utf-8'),message.encode('utf-8'),hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    password = body.get('password')
    email = body.get('email')

    try:
        secret = get_secret()
        response = register_user(email, password, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def register_user(email, password, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.sign_up(
            ClientId=secret['COGNITO_CLIENT_ID'],
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
            ]
        )
        return response

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'User registration successful', 'user': response['UserSub']})
    }