import json
import boto3
from database import get_secret, calculate_secret_hash, get_connection
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

    password = body.get('password')
    email = body.get('email')
    picture = body.get('picture')
    name = body.get('name')
    lastname = body.get('lastname')

    if not password or not email or not picture or not name or not lastname:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Name exceeds 50 characters.'
        }

    if len(lastname) > 100:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Lastname exceeds 100 characters.'
        }

    try:
        secret = get_secret()
        response = register_user(email, password, picture, name, lastname, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def register_user(email, password, picture, name, lastname, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.sign_up(
            ClientId=secret['COGNITO_CLIENT_ID'],
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'picture',
                    'Value': picture
                },
                {
                    'Name': 'name',
                    'Value': name
                }

            ]
        )
        client.admin_add_user_to_group(
            UserPoolId=secret['COGNITO_USER_POOL_ID'],
            Username=email,
            GroupName=secret['COGNITO_GROUP_NAME']
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    insert_into_user(email, response['UserSub'], name, lastname)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({'message': 'Send verification code', 'user': response['UserSub']})
    }


def insert_into_user(email, id_cognito, name, lastname, role):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, id_cognito, name, lastname, id_role, id_status) VALUES (%s, %s, %s, %s, 2, 1)"
            cursor.execute(insert_query, (email, id_cognito, name, lastname, role))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'An error occurred: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'Record inserted successfully.'
    }
