import json
from .connection import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return handle_response(None, 'Parametros inválidos', 400)

    # SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status;
    model = body.get('model')
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

    if not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length:
        return handle_response(None, 'Faltan parámetros.', 400)

    if len(model) > 50:
        return handle_response(None, 'El campo modelo excede los 50 caracteres.', 400)

    if len(brand) > 50:
        return handle_response(None, 'El campo marca excede los 50 caracteres.', 400)

    if len(engine) > 30:
        return handle_response(None, 'El campo motor excede los 30 caracteres.', 400)

    if len(type) > 30:
        return handle_response(None, 'El campo tipo excede los 30 caracteres.', 400)

    if len(fuel) > 30:
        return handle_response(None, 'El campo combustible excede los 30 caracteres.', 400)

    if len(description) > 255:
        return handle_response(None, 'El campo descripción excede los 255 caracteres.', 400)

    try:
        year = int(year)
    except ValueError:
        return handle_response(None, 'El campo año debe ser un entero.', 400)

    try:
        price = float(price)
    except ValueError:
        return handle_response(None, 'El campo precio debe ser un decimal.', 400)

    try:
        doors = int(doors)
    except ValueError:
        return handle_response(None, 'El campo puertas debe ser un entero.', 400)

    try:
        height = float(height)
    except ValueError:
        return handle_response(None, 'El campo altura debe ser un decimal.', 400)

    try:
        width = float(width)
    except ValueError:
        return handle_response(None, 'El campo ancho debe ser un decimal.', 400)

    try:
        length = float(length)
    except ValueError:
        return handle_response(None, 'El campo largo debe ser un decimal.', 400)

    response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description, image_urls)

    return response


def insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description, image_urls):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = """INSERT INTO auto (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 3)"""
            cursor.execute(insert_query, (model, brand, year, price, type, fuel, doors, engine, height, width, length, description))
            auto_id = cursor.lastrowid

            for image_url in image_urls:
                insert_image_query = "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)"
                cursor.execute(insert_image_query, (auto_id, image_url))

            connection.commit()

    except Exception as e:
        return handle_response(e, 'Error al insertar auto.', 500)

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': json.dumps({
            'statusCode': 200,
            'message': 'Auto guardado correctamente.'
        })
    }
