import json
import boto3
import pymysql
from botocore.exceptions import ClientError


def get_connection():
    secrets = get_secret()
    connection = pymysql.connect(
        host=secrets['host'],
        user=secrets['username'],
        password=secrets['password'],
        database=secrets['dbname']
    )
    return connection


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
