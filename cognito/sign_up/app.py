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
            'body': json.dumps({'message': 'Invalid request body.'}),
        }

    password = body.get('password')
    email = body.get('email')
    profile_image = body.get('profile_image')
    name = body.get('name')
    lastname = body.get('lastname')

    if not password or not email or not profile_image or not name or not lastname:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Missing parameters.'})
        }

    if len(name) > 50:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Name exceeds 50 characters.'})
        }

    if len(lastname) > 100:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({'message': 'Lastname exceeds 100 characters.'})
        }

    try:
        secret = get_secret()
        response = register_user(email, password, profile_image, name, lastname, secret)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({'message': f'An error occurred: {str(e)}'})
        }


def register_user(email, password, profile_image, name, lastname, secret):
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
            'body': json.dumps({'message': f'An error occurred: {str(e)}'})
        }

    insert_into_user(email, response['UserSub'], name, lastname, profile_image)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({'message': 'Send verification code', 'user': response['UserSub']})
    }


def insert_into_user(email, id_cognito, name, lastname, profile_image):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, id_cognito, name, lastname, id_role, id_status, profile_image) VALUES (%s, %s, %s, %s, 2, 1, %s)"
            cursor.execute(insert_query, (email, id_cognito, name, lastname, profile_image))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({'message': f'An error occurred: {str(e)}'})
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({'message': 'Send verification code', 'user': email})
    }
