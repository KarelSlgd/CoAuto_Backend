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
    password = body.get('password')

    try:
        secret = get_secret()
        response = login_auth(email, password, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def login_auth(email, password, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)

        response = client.initiate_auth(
            ClientId=secret['COGNITO_CLIENT_ID'],
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': email,
                'PASSWORD': password,
                'SECRET_HASH': secret_hash
            },
        )
        user_groups = client.admin_list_groups_for_user(
            Username=email,
            UserPoolId=secret['COGNITO_USER_POOL_ID']
        )
        role = None
        if user_groups['Groups']:
            role = user_groups['Groups'][0]['GroupName']
        return {
            'statusCode': 200,
            'body': json.dumps({'response':response['AuthenticationResult'], 'role':role})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }
