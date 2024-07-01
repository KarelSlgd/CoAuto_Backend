import json
import boto3
from database import get_secret
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

    try:
        secret = get_secret()
        response = forgot_pass(email, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def forgot_pass(email, secret):
    try:
        client = boto3.client('cognito-idp')
        response = client.forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email
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
