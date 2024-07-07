import json
import boto3
from database import get_secret, calculate_secret_hash, handle_response
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

    email = body.get('email')
    code = body.get('code')
    password = body.get('password')

    try:
        secret = get_secret()
        response = confirm_password(email, code, password, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar la contraseña.', 500)


def confirm_password(email, code, password, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        response = client.confirm_forgot_password(
            ClientId=secret['COGNITO_CLIENT_ID'],
            Username=email,
            ConfirmationCode=code,
            Password=password,
            SecretHash=secret_hash
        )

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al confirmar la contraseña.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Contraseña confirmada correctamente.',
            'response': response
        })
    }
