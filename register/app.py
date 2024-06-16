from dotenv import load_dotenv
import json
import boto3
from botocore.exceptions import ClientError

load_dotenv()


def get_secret():

    secret_name = "COAUTO"
    region_name = "us-east-1"

    # Create a Secrets Manager client
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


secrets = get_secret()


def lambda_handler(event, context):
    body = json.loads(event['body'])

    password = body['password']
    email = body['email']