import pymysql
import logging
import boto3
from botocore.exceptions import ClientError
import json
logging.basicConfig(level=logging.INFO)

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def get_connection():
    secrets = get_secret()
    try:
        connection = pymysql.connect(
            host=secrets['HOST'],
            user=secrets['USERNAME'],
            password=secrets['PASSWORD'],
            database=secrets['DB_NAME']
        )
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al conectar a la base de datos', 500)

    return connection


def get_secret():
    secret_name = 'COAUTO'
    region_name = 'us-east-1'

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
        return handle_response(e, 'Error al obtener el secreto', 500)

    return json.loads(secret)


def execute_query(connection, query):
    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            return result
    except Exception as e:
        logging.error(e)
        return None


def close_connection(connection):
    if connection:
        connection.close()
        logging.info("Connection closed")


def handle_response(error, message, status_code):
    return {
        'statusCode': status_code,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': status_code,
            'message': message,
            'error': str(error)
        })
    }

