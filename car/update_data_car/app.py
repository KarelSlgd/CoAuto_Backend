import json
from connection import get_connection

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Invalid request body.'
        }

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

    # Validate mandatory parameters
    if not id_auto or not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    # Perform necessary validations
    if len(model) > 30:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Model exceeds 30 characters'
        }

    if len(brand) > 30:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Brand exceeds 30 characters'
        }

    if len(type) > 20:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Category exceeds 20 characters'
        }

    if len(fuel) > 20:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Fuel exceeds 20 characters'
        }

    try:
        year = int(year)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Year must be an integer.'
        }

    try:
        price = float(price)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Price must be a float.'
        }

    try:
        doors = int(doors)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Doors must be an integer.'
        }

    try:
        height = float(height)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Height must be a float.'
        }

    try:
        width = float(width)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Width must be a float.'
        }

    try:
        length = float(length)
    except ValueError:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Length must be a float.'
        }

    response = update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length,
                          description, image_urls)

    return response


def update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, description, image_urls):
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

            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'Failed to update car: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'Car updated successfully.'
    }


def get_existing_image_urls(cursor, id_auto):
    cursor.execute("SELECT url FROM auto_image WHERE id_auto = %s", (id_auto,))
    return [row['url'] for row in cursor.fetchall()]