import json

try:
    from connection import get_connection, handle_response, handle_response_success, get_jwt_claims
except ImportError:
    from .connection import get_connection, handle_response, handle_response_success, get_jwt_claims


def lambda_handler(event, context):
    headers = event.get('headers', {})
    token = headers.get('Authorization')

    if not token:
        return handle_response('Missing token.', 'Faltan parámetros.', 401)

    try:
        decoded_token = get_jwt_claims(token)
        role = decoded_token.get('cognito:groups')
        if 'ClientUserGroup' in role:
            return handle_response('Acceso denegado. El rol no puede ser cliente.', 'Acceso denegado.', 401)

    except Exception as e:
        return handle_response(e, 'Error al decodificar token.', 401)

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

    response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description,
                               image_urls)

    return response


def insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description,
                    image_urls):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = """INSERT INTO auto (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 3)"""
            cursor.execute(insert_query,
                           (model, brand, year, price, type, fuel, doors, engine, height, width, length, description))
            auto_id = cursor.lastrowid

            for image_url in image_urls:
                insert_image_query = "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)"
                cursor.execute(insert_image_query, (auto_id, image_url))

            connection.commit()

    except Exception as e:
        return handle_response(e, 'Error al insertar auto.', 500)

    finally:
        connection.close()

    return handle_response_success(200, 'Auto guardado correctamente.', None)
