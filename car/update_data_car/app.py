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
        return handle_response(None, 'Cuerpo de la petición inválido.', 400)

    id_auto = body.get('id_auto')
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

    if not id_auto or not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length:
        return handle_response(None, 'Faltan parámetros.', 400)

    if len(model) > 50:
        return handle_response(None, 'El campo modelo excede los 50 caracteres.', 400)

    if len(brand) > 50:
        return handle_response(None, 'El campo marca excede los 50 caracteres.', 400)

    if len(type) > 30:
        return handle_response(None, 'El campo tipo excede los 30 caracteres.', 400)

    if len(fuel) > 30:
        return handle_response(None, 'El campo combustible excede los 30 caracteres.', 400)

    if len(engine) > 30:
        return handle_response(None, 'El campo motor excede los 30 caracteres.', 400)

    if description is not None and len(description) > 255:
        return handle_response(None, 'El campo descripción excede los 255 caracteres.', 400)

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
        return handle_response(e, 'Ocurrió un error al actualizar el auto.', 500)

    finally:
        connection.close()

    return handle_response_success(200, 'Auto actualizado correctamente.', None)


def get_existing_image_urls(cursor, id_auto):
    cursor.execute("SELECT url FROM auto_image WHERE id_auto = %s", (id_auto,))
    return [row[0] for row in cursor.fetchall()]
