import json
import base64
from database import get_connection, close_connection
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


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
        decoded_token = get_jwt_claims(token)
        user_info = get_into_user(decoded_token['cognito:username'])
        return {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'tokenDecode': decoded_token,
                'userInfo': user_info
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps(f'An error occurred: {str(e)}')
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


def get_into_user(token):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            query = """SELECT 
                            id_user, 
                            id_cognito, 
                            email,
                            u.name AS nameUser,
                            lastname, 
                            r.name AS nameRole,
                            s.value,
                            profile_image
                        FROM user u
                        INNER JOIN role r 
                            ON u.id_role = r.id_role 
                        INNER JOIN status s 
                            ON u.id_status = s.id_status
                        WHERE id_cognito = %s;"""

            cursor.execute(query, (token,))

            row = cursor.fetchone()

            if row:
                columns = [desc[0] for desc in cursor.description]
                result = dict(zip(columns, row))
                return result
            else:
                return None

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        close_connection(connection)
