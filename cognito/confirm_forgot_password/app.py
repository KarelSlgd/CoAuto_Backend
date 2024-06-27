import json
import boto3
from database import get_secret


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
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
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def confirm_password(email, code, password, secret):
    try:
        client = boto3.client('cognito-idp')
        response = client.confirm_forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=code,
            Password=password
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
