from dotenv import load_dotenv
import json
import boto3
from botocore.exceptions import ClientError

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




def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])

        password = body['password']
        email = body['email']

        if not email or not password:
            return {
                'statusCode': 400,
                'body': json.dumps('Missing parameters.')
            }

        return get_secret()

        #register_user(email, password, secrets)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error.')
        }


def register_user(email, password, secret):
    client = boto3.client('cognito-idp')
    response = client.sign_up(
        ClientId=secret['COGNITO_CLIENT_ID'],
        Username=email,
        Password=password,
        UserAttributes=[
            {
                'Name': 'email',
                'Value': email
            }
        ]
    )

    return {
        'statusCode': 200,
        'body': json.dumps('User registered successfully.')
    }
