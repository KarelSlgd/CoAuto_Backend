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
    connection = get_connection()

    rates = []

    query_params = event.get('queryStringParameters', {})
    type_param = query_params.get('type')
    value = query_params.get('value')

    if not type_param or not value:
        return handle_response("Falta un parámetro de búsqueda", 'Debe proporcionar los parámetros: type y value', 400)

    column_map = {
        'modelo': 'a.model',
        'año': 'a.year',
        'marca': 'a.brand'
    }

    if type_param not in column_map:
        return handle_response("Tipo de parámetro no válido",
                               'El parámetro type debe ser uno de los siguientes: model, year, brand', 400)

    column = column_map[type_param]

    try:
        with connection.cursor() as cursor:
            sql = f"""
                SELECT r.id_rate, r.value, comment, a.model, a.brand, u.name, u.lastname, a.id_auto, u.profile_image, s.value, a.year, u.email AS status
                FROM rate r
                INNER JOIN auto a ON r.id_auto=a.id_auto
                INNER JOIN user u ON r.id_user=u.id_user
                INNER JOIN status s ON r.id_status=s.id_status
                WHERE {column} = %s
            """

            cursor.execute(sql, (value,))
            result = cursor.fetchall()

            for rate in result:
                rate = {
                    'id_rate': rate[0],
                    'value': rate[1],
                    'comment': rate[2],
                    'model': rate[3],
                    'brand': rate[4],
                    'name': rate[5],
                    'lastname': rate[6],
                    'id_auto': rate[7],
                    'profile_image': rate[8],
                    'status': rate[9]
                }
                rates.append(rate)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al obtener la reseña', 500)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            'statusCode': 200,
            "message": "Reseñas obtenidas correctamente.",
            "data": rates
        }),
    }
