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
            cursor.execute("SELECT id_rate, value, comment, u.name, u.lastname, r.id_user, r.id_auto FROM rate r INNER JOIN user u ON r.id_user=u.id_user;")
            result = cursor.fetchall()

            for rate in result:
                rates.append({
                    'id_rate': rate[0],
                    'value': rate[1],
                    'comment': rate[2],
                    'user': rate[3] + ' ' + rate[4],
                    'id_user': rate[5],
                    'id_auto': rate[6]
                })
                cursor.execute("SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status WHERE id_auto = {id_auto}")
                result = cursor.fetchall()
                cars = []
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

                rates.append({
                    'cars': cars
                })

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
