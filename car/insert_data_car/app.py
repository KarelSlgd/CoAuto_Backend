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

    model = body.get('model')
    brand = body.get('brand')
    year = body.get('year')
    price = body.get('price')
    category = body.get('category')
    fuel = body.get('fuel')
    doors = body.get('doors')
    motor = body.get('motor')
    height = body.get('height')
    width = body.get('width')
    length = body.get('length')
    weight = body.get('weight')
    details = body.get('details')
    id_status = body.get('id_status')
    image_urls = body.get('image_urls', [])

    if not model or not brand or not year or not price or not category or not fuel or not doors or not motor or not height or not width or not length or not weight or not id_status:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    if len(model) > 30:
        return {
            'statusCode': 400,
            'body': 'Model exceeds 50 characters.'
        }

    if len(brand) > 30:
        return {
            'statusCode': 400,
            'body': 'Brand exceeds 50 characters.'
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

    try:
        weight = float(weight)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Weight must be a float.'
        }

    response = insert_into_car(model, brand, year, price, category, fuel, doors, motor, height, width, length, weight, details, id_status, image_urls)

    return response


def insert_into_car(model, brand, year, price, category, fuel, doors, motor, height, width, length, weight, details, id_status, image_urls):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            insert_query = """INSERT INTO auto (model, brand, year, price, category, fuel, doors, motor, height, width, length, weight, details, id_status)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (model, brand, year, price, category, fuel, doors, motor, height, width, length, weight, details, id_status))
            auto_id = cursor.lastrowid

            for image_url in image_urls:
                insert_image_query = "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)"
                cursor.execute(insert_image_query, (auto_id, image_url))

            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'An error occurred: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Record inserted successfully.'
    }
