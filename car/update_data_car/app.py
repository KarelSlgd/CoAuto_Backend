import pymysql
import os
import json

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
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
    id_status = body.get('id_status')
    image_urls = body.get('image_urls', [])

    # Validate mandatory parameters
    if not id_auto or not model or not brand or not year or not price or not type or not fuel or not doors or not engine or not height or not width or not length or not id_status:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    # Perform necessary validations
    if len(model) > 30:
        return {
            'statusCode': 400,
            'body': 'Model exceeds 30 characters'
        }

    if len(brand) > 30:
        return {
            'statusCode': 400,
            'body': 'Brand exceeds 30 characters'
        }

    if len(type) > 20:
        return {
            'statusCode': 400,
            'body': 'Category exceeds 20 characters'
        }

    if len(fuel) > 20:
        return {
            'statusCode': 400,
            'body': 'Fuel exceeds 20 characters'
        }

    try:
        year = int(year)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Year must be an integer.'
        }

    try:
        price = float(price)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Price must be a float.'
        }

    try:
        doors = int(doors)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Doors must be an integer.'
        }

    try:
        height = float(height)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Height must be a float.'
        }

    try:
        width = float(width)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Width must be a float.'
        }

    try:
        length = float(length)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Length must be a float.'
        }


    response = update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status, image_urls)

    return response


def update_car(id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status, image_urls):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE auto SET model=%s, brand=%s, year=%s, price=%s, type=%s, fuel=%s, doors=%s, engine=%s, height=%s, width=%s, length=%s, description=%s, id_status=%s WHERE id_auto=%s",
                (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status, id_auto)
            )

            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Failed to update car: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Car updated successfully.'
    }