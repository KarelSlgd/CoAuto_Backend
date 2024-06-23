from botocore.exceptions import ClientError
import json
import boto3


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


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
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
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
