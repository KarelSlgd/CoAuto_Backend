
try:
    from connection import get_connection, handle_response, handle_response_success
except ImportError:
    from .connection import get_connection, handle_response, handle_response_success


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

    return handle_response_success(200, 'Todos los autos obtenidos correctamente.', cars)

