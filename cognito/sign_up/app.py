import json
import boto3
from database import get_secret, calculate_secret_hash, get_connection, handle_response

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Cuerpo de la solicitud inválido.', 400)

    password = body.get('password')
    email = body.get('email')
    profile_image = body.get('profile_image')
    name = body.get('name')
    lastname = body.get('lastname')

    if not password or not email or not profile_image or not name or not lastname:
        return handle_response(None, 'Faltan parámetros.', 400)

    if len(name) > 50:
        return handle_response(None, 'El nombre no puede exceder los 50 caracteres.', 400)

    if len(lastname) > 100:
        return handle_response(None, 'El apellido no puede exceder los 100 caracteres.', 400)

    try:
        secret = get_secret()
        response = register_user(email, password, profile_image, name, lastname, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al registrar el usuario.', 500)


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
                }
            ]
        )
        client.admin_add_user_to_group(
            UserPoolId=secret['COGNITO_USER_POOL_ID'],
            Username=email,
            GroupName=secret['COGNITO_GROUP_NAME']
        )

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al registrar el usuario.', 500)

    insert_into_user(email, response['UserSub'], name, lastname, profile_image)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Se ha enviado un correo de confirmación.',
            'response': response['UserSub']
        })
    }


def insert_into_user(email, id_cognito, name, lastname, profile_image):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, id_cognito, name, lastname, id_role, id_status, profile_image) VALUES (%s, %s, %s, %s, 2, 1, %s)"
            cursor.execute(insert_query, (email, id_cognito, name, lastname, profile_image))
            connection.commit()

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al registrar el usuario.', 500)

    finally:
        connection.close()
