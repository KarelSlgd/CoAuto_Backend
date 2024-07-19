import json
import boto3
from botocore.exceptions import ClientError
try:
    from connection import get_connection, handle_response, get_secret
except ImportError:
    from .connection import get_connection, handle_response, get_secret

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Cuerpo de la solicitud no válido.', 400)

    id_user = body.get('id_user')
    id_status = body.get('id_status')

    if not id_user or not id_status:
        return handle_response(None, 'Faltan parámetros.', 400)

    value = get_status_value(id_status)
    if value is None:
        return handle_response(None, 'El status proporcionado no es válido.', 400)

    response = update_user_status(id_user, id_status, value)

    return response


def update_user_status(id_user, status, value):
    connection = get_connection()
    try:
        username = get_username_by_id(id_user)
        secrets = get_secret()

        if username is None:
            return handle_response(None, 'No se encontró el usuario.', 404)

        with connection.cursor() as cursor:
            cursor.execute("UPDATE user SET id_status=%s WHERE id_user=%s", (status, id_user))
            connection.commit()

        client = boto3.client('cognito-idp')

        if value == 1:
            client.admin_enable_user(
                UserPoolId=secrets['COGNITO_USER_POOL_ID'],
                Username=username
            )
        else:
            client.admin_disable_user(
                UserPoolId=secrets['COGNITO_USER_POOL_ID'],
                Username=username
            )

    except ClientError as e:
        return handle_response(e, 'Ocurrió un error al actualizar el usuario', 500)
    except Exception as e:
        return handle_response(e, 'Ocurrió un error al actualizar el usuario', 500)
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Usuario actualizado correctamente.'
        })
    }


def get_username_by_id(id_user):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM user WHERE id_user=%s", (id_user,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    except Exception as e:
        raise e
    finally:
        connection.close()


def get_status_value(id_status):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT value FROM status WHERE id_status=%s AND description='to_user'", (id_status,))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return None
    except Exception as e:
        raise e
    finally:
        connection.close()
