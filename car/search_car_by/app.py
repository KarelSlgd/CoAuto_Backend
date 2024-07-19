import json
from .connection import get_connection


def build_query(filters):
    base_query = "SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status"
    conditions = []
    parameters = []

    if 'year' in filters:
        conditions.append("year = %s")
        parameters.append(filters['year'])
    if 'price' in filters:
        conditions.append("price <= %s")
        parameters.append(filters['price'])
    if 'model' in filters:
        conditions.append("model = %s")
        parameters.append(filters['model'])
    if 'brand' in filters:
        conditions.append("brand = %s")
        parameters.append(filters['brand'])
    if 'doors' in filters:
        conditions.append("doors = %s")
        parameters.append(filters['doors'])

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    return base_query, parameters


def lambda_handler(event, context):
    filters = event.get('queryStringParameters', {})
    connection = get_connection()
    cars = []

    try:
        query, params = build_query(filters)
        with connection.cursor() as cursor:
            cursor.execute(query, params)
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

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        },
        "body": json.dumps({
            'statusCode': 200,
            'message': 'Carros encontrados',
            'data': cars
        }),
    }
