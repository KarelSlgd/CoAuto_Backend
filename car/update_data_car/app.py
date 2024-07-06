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
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Solicitud no válida.', 400)

    id_auto = body.get('id_auto')
    model = body.get('brand')
    brand = body.get('brand')
    year = body.get('year')
    price = body.get('price')
    type = body.get('type')
    fuel = body.get('fuel')
    doors = body.get('doors')
    engine = body.get('engine')
    height = body.get('height')
    width = body.get('width')
    length = body.get('length')
    description = body.get('description')
    image_urls = body.get('image_urls', [])

    if not id_auto or not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length:
        return handle_response(None, 'Faltan parámetros.', 400)

    if len(model) > 30:
        return handle_response(None, 'El campo modelo excede los 30 caracteres.', 400)

    if len(brand) > 30:
        return handle_response(None, 'El campo marca excede los 30 caracteres.', 400)

    if len(type) > 20:
        return handle_response(None, 'El campo tipo excede los 20 caracteres.', 400)

    if len(fuel) > 20:
        return handle_response(None, 'El campo combustible excede los 20 caracteres.', 400)

    try:
        year = int(year)
    except ValueError:
        return handle_response(None, 'El año debe ser un entero.', 400)

    try:
        price = float(price)
    except ValueError:
        return handle_response(None, 'El precio debe ser un decimal.', 400)

    try:
        doors = int(doors)
    except ValueError:
        return handle_response(None, 'Las puertas deben ser un entero.', 400)

    try:
        height = float(height)
    except ValueError:
        return handle_response(None, 'La altura debe ser un decimal.', 400)

    try:
        width = float(width)
    except ValueError:
        return handle_response(None, 'El ancho debe ser un decimal.', 400)

    try:
        length = float(length)
    except ValueError:
        return handle_response(None, 'La longitud debe ser un decimal.', 400)

    response = update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length,
                          description, image_urls)

    return response


def update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, description,
               image_urls):
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auto SET model=%s, brand=%s, year=%s, price=%s, type=%s, fuel=%s, doors=%s, engine=%s, height=%s, width=%s, length=%s, description=%s WHERE id_auto=%s",
                (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_auto)
            )

            existing_image_urls = get_existing_image_urls(cursor, id_auto)

            new_image_urls = set(image_urls) - set(existing_image_urls)
            for url in new_image_urls:
                cursor.execute(
                    "INSERT INTO auto_image (url, id_auto) VALUES (%s, %s)",
                    (url, id_auto)
                )

            removed_image_urls = set(existing_image_urls) - set(image_urls)
            for url in removed_image_urls:
                cursor.execute(
                    "DELETE FROM auto_image WHERE url = %s AND id_auto = %s",
                    (url, id_auto)
                )

            connection.commit()

    except Exception as e:
        return handle_response(e, f'Failed to update car: {str(e)}', 500)

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Car updated successfully.'
        })
    }


def get_existing_image_urls(cursor, id_auto):
    cursor.execute("SELECT url FROM auto_image WHERE id_auto = %s", (id_auto,))
    return [row[0] for row in cursor.fetchall()]
