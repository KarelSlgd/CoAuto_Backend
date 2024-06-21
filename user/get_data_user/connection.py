import boto3
import pymysql
import os
from botocore.exceptions import ClientError
import json

def get_connection():
    secrets = get_secret()
    try:
        connection = pymysql.connect(
            host=secrets['host'],
            user=secrets['username'],
            password=secrets['password'],
            database=secrets['dbname']
        )
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Failed to connect to database: {str(e)}'
        }

    return connection


def get_secret():
    secret_name = os.getenv('SECRET_NAME')
    region_name = os.getenv('REGION_NAME')

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
            'body': f'Failed to retrieve secret: {str(e)}'
        }

    return json.loads(secret)

