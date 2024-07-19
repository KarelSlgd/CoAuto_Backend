import json
try:
    from connection import get_connection, handle_response
except ImportError:
    from .connection import get_connection, handle_response

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
    name = body.get('name')
    lastname = body.get('lastname')

    if not id_user:
        return handle_response(None, 'Faltan parámetros.', 400)

    if name is not None and len(name) > 50:
        return handle_response(None, 'El nombre no debe exceder los 50 caracteres.', 400)

    if lastname is not None and len(lastname) > 100:
        return handle_response(None, 'El apellido no debe exceder los 100 caracteres.', 400)

    response = update_user(id_user, name, lastname)

    return response


def update_user(id_user, name, lastname):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user SET name=%s, lastname=%s WHERE id_user=%s",
                (name, lastname, id_user)
            )
            connection.commit()

    except Exception as e:
        return handle_response(e,'Ocurrió un error al actualizar usuario.', 500)

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Usuario actualizado correctamente'
        })
    }
