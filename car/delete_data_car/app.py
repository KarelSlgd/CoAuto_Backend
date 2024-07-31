import json

try:
    from connection import get_connection, handle_response, handle_response_success, get_jwt_claims
except ImportError:
    from .connection import get_connection, handle_response, handle_response_success, get_jwt_claims


def lambda_handler(event, context):
    headers = event.get('headers', {})
    token = headers.get('Authorization')

    if not token:
        return handle_response('Missing token.', 'Faltan parámetros.', 401)

    try:
        decoded_token = get_jwt_claims(token)
        role = decoded_token.get('cognito:groups')
        if 'ClientUserGroup' in role:
            return handle_response('Acceso denegado. El rol no puede ser cliente.', 'Acceso denegado.', 401)

    except Exception as e:
        return handle_response(e, 'Error al decodificar token.', 401)

    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return handle_response(e, 'Parametros inválidos', 400)

    id_auto = body.get('id_auto')
    id_status = body.get('id_status')

    if id_auto is None or id_status is None:
        return handle_response(None, 'Faltan parámetros.', 400)

    response = delete_car(id_auto, id_status)

    return response


def delete_car(id_auto, id_status):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM status WHERE id_status=%s AND name='to_auto'", (id_status,))
            result = cursor.fetchone()

            if not result:
                return handle_response(None, 'El status no es válido para autos.', 400)

            cursor.execute("UPDATE auto SET id_status=%s WHERE id_auto=%s", (id_status, id_auto))
            connection.commit()

    except Exception as e:
        return handle_response(e, 'Error al actualizar auto.', 500)
    finally:
        connection.close()

    return handle_response_success(200, 'Auto actualizado correctamente.', None)
