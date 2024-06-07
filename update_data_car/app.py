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
    brand = body.get('model')
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

    # Validate mandatory parameters
    if not id_auto or not model or not brand or not year or not price or not category or not fuel or not doors or not motor or not height or not length or not weight or not id_status:
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

    if len(category) > 20:
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

    try:
        weight = float(weight)
    except ValueError:
        return {
            'statusCode': 400,
            'body': 'Weight must be a float.'
        }

    response = update_car(id_auto, model, year, price, category, fuel, doors, motor, height, weight, length, details, id_status)

    return response

def update_car(id_auto, model, year, price, category, fuel, doors, motor, height, weight, length, details, id_status):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE user SET model=%s, year=%s, price=%s, category=%s, fuel=%s, doors=%s, motor=%s, height=%s, width=%s, length=%s, detais=%s, id_status=%s WHERE id_auto=%s",
                (model, year, price, category, fuel, doors, motor, height, weight, length, details, id_status, id_auto)
            )

            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Failed to update user: {str(e)}'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'Car updated successfully.'
    }