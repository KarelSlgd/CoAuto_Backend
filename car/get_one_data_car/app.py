import json
from connection import get_connection, close_connection, handle_response

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
        return handle_response(None, 'Falta un parametro.', 400)

    connection = get_connection()
    query = f"SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status WHERE id_auto = {id_auto}"
    cars = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()

            for row in result:
                car = {
                    'id_auto': row[0],
                    'model': row[1],
                    'brand': row[2],
                    'year': row[3],
                    'price': row[4],
                    'type': row[5],
                    'fuel': row[6],
                    'doors': row[7],
                    'engine': row[8],
                    'height': row[9],
                    'width': row[10],
                    'length': row[11],
                    'description': row[12],
                    'status': row[13],
                    'images': []
                }
                cursor.execute(
                    "SELECT url FROM auto_image WHERE id_auto = %s", (row[0],))
                image_results = cursor.fetchall()

                for image_row in image_results:
                    car['images'].append(image_row[0])

                cars.append(car)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al obtener la reseña.', 500)

    finally:
        close_connection(connection)

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Informacion del auto obtenida correctamente.',
            'data': cars
        })
    }
