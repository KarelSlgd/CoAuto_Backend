from botocore.exceptions import ClientError
import json
import boto3
import hmac
import hashlib
import base64


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


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    email = body.get('email')
    confirmation_code = body.get('confirmation_code')

    try:
        secret = get_secret()
        response = confirmation_registration(email, confirmation_code, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def confirmation_registration(email, confirmation_code, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.confirm_sign_up(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=confirmation_code,
            SecretHash=secret_hash,
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'User confirmed'})
    }
