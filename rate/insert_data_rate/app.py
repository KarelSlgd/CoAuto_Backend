import json
from database import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return handle_response(e, 'Cuerpo de la petición inválido.', 400)

    value = body.get('value')
    comment = body.get('comment')
    id_auto = body.get('id_auto')
    id_user = body.get('id_user')

    if not value or not id_auto or not id_user:
        return handle_response(None, 'Faltan parámetros.', 400)

    value_n = 0
    try:
        value_n = int(value)
    except ValueError:
        return handle_response(None, 'El valor de la reseña debe ser un número entero.', 400)

    if value_n >= 5 or value_n <= 1:
        return handle_response(None, 'El valor de la reseña debe estar entre 1 y 5.', 400)

    if len(comment) > 100:
        return handle_response(None, 'El comentario no debe exceder los 100 caracteres.', 400)

    if not (verify_user(id_user)):
        return handle_response(None, 'El usuario no fue encontrado.', 400)

    if not (verify_auto(id_auto)):
        return handle_response(None, 'El auto no fue encontrado.', 400)

    if check_existing_review(id_user, id_auto):
        return handle_response(None, 'El usuario ya ha reseñado este auto.', 400)

    response = insert_into_rate(value_n, comment, id_auto, id_user)

    return response


def insert_into_rate(value, comment, id_auto, id_user):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO rate (value, comment, id_auto, id_user, id_status) VALUES (%s, %s, %s, %s, 5)"
            cursor.execute(insert_query, (value, comment, id_auto, id_user))
            connection.commit()
    except Exception as e:
        return handle_response(e, 'Error al insertar la reseña.', 500)
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Reseña guardada correctamente.'
        })
    }


def verify_user(id_user):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user FROM user WHERE id_user = %s", id_user)
            result = cursor.fetchone()
            return result is not None
    except Exception:
        return False
    finally:
        connection.close()


def verify_auto(id_auto):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_auto FROM auto WHERE id_auto = %s", id_auto)
            result = cursor.fetchone()
            return result is not None
    except Exception:
        return False
    finally:
        connection.close()


def check_existing_review(id_user, id_auto):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            check_query = "SELECT 1 FROM rate WHERE id_user = %s AND id_auto = %s"
            cursor.execute(check_query, (id_user, id_auto))
            result = cursor.fetchone()
            return result is not None
    except Exception:
        return False
    finally:
        connection.close()
