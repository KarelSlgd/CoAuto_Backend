import json
from database import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    connection = get_connection()

    rates = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT r.id_rate, r.value, comment, a.model, a.brand, u.name, u.lastname, a.id_auto, a.profile_image, s.value AS status FROM rate r INNER JOIN auto a ON r.id_auto=a.id_auto INNER JOIN user u ON r.id_user=u.id_user INNER JOIN status s ON r.id_status=s.id_status;")
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
                    'status': rate[8]
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
