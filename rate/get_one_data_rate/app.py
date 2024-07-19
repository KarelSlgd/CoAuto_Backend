from dotenv import load_dotenv
import json
from .database import get_connection, close_connection, execute_query, handle_response

load_dotenv()
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    if 'queryStringParameters' in event:
        id_auto = event['queryStringParameters'].get('id_auto')
    else:
        body = json.loads(event.get('body', '{}'))
        id_auto = body.get('id_auto')

    if not id_auto:
        return handle_response(None, 'Faltan parámetros.', 400)

    connection = get_connection()
    query = f"SELECT r.id_rate, r.value, comment, a.model, a.brand, u.name, u.lastname, a.id_auto, s.value AS status FROM rate r INNER JOIN auto a ON r.id_auto=a.id_auto INNER JOIN user u ON r.id_user=u.id_user INNER JOIN status s ON r.id_status=s.id_status WHERE r.id_auto = {id_auto}"
    rates = []

    try:
        result = execute_query(connection, query)

        for row in result:
            rate = {
                'id_rate': row[0],
                'value': row[1],
                'comment': row[2],
                'model': row[3],
                'brand': row[4],
                'name': row[5],
                'lastname': row[6],
                'id_auto': row[7],
                'status': row[8]
            }
            rates.append(rate)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al obtener la reseña.', 500)

    finally:
        close_connection(connection)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Reseñas obtenidas correctamente.',
            'data': rates
        })
    }
