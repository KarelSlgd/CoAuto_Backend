import json
from connection import get_connection, handle_response
import base64
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):

    headers = event.get('headers', {})
    token = headers.get('Authorization')

    if not token:
        return handle_response(None, 'Falta token.', 401)

    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Cuerpo de la solicitud no válido.', 400)

    profile_image = body.get('profile_image')

    if not profile_image:
        return handle_response(None, 'Faltan parámetros.', 400)

    response = update_photo(profile_image, token)

    return response


def update_photo(profile_image, token):
    connection = get_connection()
    decoded_token = get_jwt_claims(token)
    id_user = decoded_token.get('cognito:username')
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user SET profile_image=%s WHERE id_cognito=%s",
                (profile_image, id_user)
            )
            connection.commit()

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al actualizar usuario.', 500)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'User updated successfully.'

        })
    }


def get_jwt_claims(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None

        payload_encoded = parts[1]
        payload_decoded = base64.b64decode(payload_encoded + "==")
        claims = json.loads(payload_decoded)

        return claims

    except ValueError:
        return None
