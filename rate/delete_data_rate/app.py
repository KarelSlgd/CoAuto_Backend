import json
from connection import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError) as e:
        return handle_response(e, 'Parametros inválidos', 400)

    id_rate = body.get('id_rate')
    id_status = body.get('id_status')

    if id_rate is None or id_status is None:
        return handle_response(None, 'Faltan parámetros.', 400)

    response = delete_car(id_rate, id_status)

    return response


def delete_car(id_auto, id_status):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM status WHERE id_status=%s AND name='to_rate'", (id_status,))
            result = cursor.fetchone()

            if not result:
                return handle_response(None, 'El status no es válido para las reseñas.', 400)

            cursor.execute("UPDATE auto SET id_status=%s WHERE id_auto=%s", (id_status, id_auto))
            connection.commit()

    except Exception as e:
        return handle_response(e, 'Error al actualizar las reseñas.', 500)
    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Reseña actualizada correctamente.'
        }),
    }
