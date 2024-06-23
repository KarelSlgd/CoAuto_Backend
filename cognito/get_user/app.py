from botocore.exceptions import ClientError
import json
import boto3
import hmac
import hashlib
import base64
import pymysql


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


def calculate_secret_hash(client_id, secret_key, username):
    message = username + client_id
    dig = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    token = body.get('token')

    try:
        response = get_info(token)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def get_info(token):
    try:
        client = boto3.client('cognito-idp')
        response = client.get_user(
            AccessToken=token
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    user = get_into_user(response['Username'])

    return {
        'statusCode': 200,
        'body': json.dumps({
            'userAttributes': response['UserAttributes'],
            'user': user
        })
    }


def get_into_user(token):
    connection = get_connection()
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
                        ON u.id_status = s.id_status
                    WHERE id_cognito = '{token}';""".format(token=token)

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            user = {
                'idUser': result['id_user'],
                'idCognito': result['id_cognito'],
                'email': result['email'],
                'name': result['nameUser'],
                'lastname': result['lastname'],
                'role': result['nameRole'],
                'status': result['value']
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        connection.close()

    return json.dumps(user)
