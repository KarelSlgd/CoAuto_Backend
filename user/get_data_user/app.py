import json
import boto3
import pymysql
import os
from botocore.exceptions import ClientError


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


def lambda_handler(event, context):
    connection = get_connection()
    users = []
    try:
        query = """SELECT 
                        id_user, 
                        id_cognito, 
                        email,
                        u.name AS nameUser,
                        lastname, 
                        r.name AS nameRole,
                        s.value 
                    FROM user u
                    INNER JOIN role r 
                        ON u.id_role = r.id_role 
                    INNER JOIN status s 
                        ON u.id_status = s.id_status;"""
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            for row in result:
                user = {
                    'idUser': row['id_user'],
                    'idCognito': row['id_cognito'],
                    'email': row['email'],
                    'name': row['nameUser'],
                    'lastname': row['lastname'],
                    'role': row['nameRole'],
                    'status': row['value']
                }
                users.append(user)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get users",
            "data": users
        }),
    }
