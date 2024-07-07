import json
from database import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    connection = get_connection()

    users = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_rate, value, comment, a.model, a.brand, u.name, u.lastname FROM rate r INNER JOIN auto a ON r.id_auto=a.id_auto INNER JOIN user u ON r.id_user=u.id_user;")
            result = cursor.fetchall()

            for row in result:
                user = {
                    'id_rate': row[0],
                    'value': row[1],
                    'comment': row[2],
                    'model': row[3],
                    'brand': row[4],
                    'name': row[5],
                    'lastname': row[6]
                }
                users.append(user)

    except Exception as e:
        return handle_response(e, 'Ocurrió un error al obtener la reseña', 500)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            'statusCode': 200,
            "message": "get rate",
            "data": users
        }),
    }
