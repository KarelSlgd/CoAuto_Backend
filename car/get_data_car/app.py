import json
import base64

from connection import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    connection = get_connection()

    #headers = event.get('headers', {})
    #token = headers.get('Authorization')

    #if not token:
    #    return handle_response('Missing token.', 'Faltan parámetros.', 401)

    #try:
    #    decoded_token = get_jwt_claims(token)
    #    role = decoded_token.get('cognito:groups')
    #    if 'ClientUserGroup' in role:
    #        return handle_response('Acceso denegado. El rol no puede ser cliente.', 'Acceso denegado.', 401)


    #except Exception as e:
    #    return handle_response(e, 'Error al decodificar token.', 401)

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

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            'statusCode': 200,
            'message': 'get cars',
            'data': cars
        }),
    }


def get_jwt_claims(token):
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Token inválido")

        payload_encoded = parts[1]
        payload_decoded = base64.b64decode(payload_encoded + "==")
        claims = json.loads(payload_decoded)

        return claims

    except ValueError as e:
        raise e
