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
    id_status = body.get('id_status')
    image_urls = body.get('image_urls', [])

    if not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length or not id_status:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Missing parameters.'
        }

    if len(model) > 30:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Model exceeds 50 characters.'
        }

    if len(brand) > 30:
        return {
            'statusCode': 400,
            'headers': headers_cors,
            'body': 'Brand exceeds 50 characters.'
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

    response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status, image_urls)

    return response


def insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status, image_urls):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            insert_query = """INSERT INTO auto (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status))
            auto_id = cursor.lastrowid

            for image_url in image_urls:
                insert_image_query = "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)"
                cursor.execute(insert_image_query, (auto_id, image_url))

            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': f'An error occurred: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'headers': headers_cors,
        'body': 'Record inserted successfully.'
    }
