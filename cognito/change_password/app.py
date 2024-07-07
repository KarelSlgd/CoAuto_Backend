import json
import boto3
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

    previous_password = body.get('previous_password')
    new_password = body.get('new_password')
    token = body.get('access_token')

    try:
        response = change(previous_password, new_password, token)
        return response
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al cambiar la contraseña.', 500)


def change(previous_password, new_password, token):
    try:
        client = boto3.client('cognito-idp')
        response = client.change_password(
            PreviousPassword=previous_password,
            ProposedPassword=new_password,
            AccessToken=token
        )

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al cambiar la contraseña.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Contraseña cambiada correctamente.',
            'response': response
        })
    }


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
