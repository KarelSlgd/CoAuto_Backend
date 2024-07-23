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

    cars = []

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status")
            result = cursor.fetchall()

            for row in result:
                car = {
                    'id_auto': row[0],
                    'model': row[1],
                    'brand': row[2],
                    'year': row[3],
                    'price': "${:,.2f}".format(row[4]),
                    'type': row[5],
                    'fuel': row[6],
                    'doors': row[7],
                    'engine': row[8],
                    'height': row[9],
                    'width': row[10],
                    'length': row[11],
                    'description': row[12],
                    'status': row[13],
                    'images': [],
                    'average_rating': None
                }
                cursor.execute(
                    "SELECT url FROM auto_image WHERE id_auto = %s", (row[0],))
                image_results = cursor.fetchall()

                for image_row in image_results:
                    car['images'].append(image_row[0])

                cursor.execute(
                    "SELECT value FROM rate WHERE id_auto = %s", (row[0],))
                rate_results = cursor.fetchall()

                if rate_results:
                    average_rating = sum(rate[0] for rate in rate_results) / len(rate_results)
                else:
                    average_rating = 0

                car['average_rating'] = average_rating

                cars.append(car)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            'statusCode': 200,
            'message': 'get cars',
            'data': cars
        }),
    }
