import json
from connection import get_connection, handle_response
headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


def lambda_handler(event, context):
    connection = get_connection()
    users = []
    try:
        query = """SELECT 
                        id_user,
                        id_cognito,
                        email,
                        u.name AS nameUser,
                        lastname, 
                        r.name AS nameRole,
                        s.value,
                        profile_image
                    FROM user u
                    INNER JOIN role r 
                        ON u.id_role = r.id_role 
                    INNER JOIN status s 
                        ON u.id_status = s.id_status;"""
        with connection.cursor() as cursor:
            cursor.execute(query)
            result = cursor.fetchall()
            for row in result:
                user = {
                    'id_user': row[0],
                    'id_cognito': row[1],
                    'email': row[2],
                    'name': row[3],
                    'lastname': row[4],
                    'role': row[5],
                    'status': row[6],
                    'profile_image': row[7]
                }
                users.append(user)

    except Exception as e:
        return handle_response(e, 'Error al obtener usuarios', 500)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            "data": users,
            'statusCode': 200,
            'message': 'Usuarios obtenidos correctamente'
        }),
    }