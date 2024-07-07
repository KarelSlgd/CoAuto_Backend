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

    try:
        secret = get_secret()
        response = resend_code(email, secret)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el reenvío del código de confirmación.', 500)


def resend_code(email, secret):
    try:
        client = boto3.client('cognito-idp')
        secret_hash = calculate_secret_hash(secret['COGNITO_CLIENT_ID'], secret['SECRET_KEY'], email)
        client.resend_confirmation_code(
            ClientId=secret['COGNITO_CLIENT_ID'],
            SecretHash=secret_hash,
            Username=email
        )

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al solicitar el reenvío del código de confirmación.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Código de confirmación reenviado correctamente.'
        })
    }
