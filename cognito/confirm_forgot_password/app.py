import json
import boto3
from database import get_secret, calculate_secret_hash
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Invalid request body.'
        }

    email = body.get('email')
    code = body.get('code')
    password = body.get('password')

    try:
        secret = get_secret()
        response = confirm_password(email, code, password, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def confirm_password(email, code, password, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.confirm_forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=code,
            Password=password,
            SecretHash=secret_hash
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps(response)
    }
