import json
import boto3
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}
from connection import get_connection


def lambda_handler(event, context):

    headers = event.get('headers', {})
    token = headers.get('Authorization')

    if not token:
        return {
            'statusCode': 401,
            'headers': headers_cors,
            'body': json.dumps('Missing token.')
        }

    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({
                'message': 'Invalid request body.'
            })
        }

    profile_image = body.get('profile_image')

    if not photo:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({
                'message': 'Missing parameters.'
            })
        }

    response = update_photo(profile_image)

    return response


def update_photo(profile_image):
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
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({
                'message': f'Failed to update user in Cognito: {str(e)}'
            })
        }

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
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
