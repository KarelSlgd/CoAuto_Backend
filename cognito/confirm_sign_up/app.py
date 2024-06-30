import json
import boto3
from database import get_secret, calculate_secret_hash


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
        client.confirm_sign_up(
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
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        'body': json.dumps({'message': 'User confirmed'})
    }
