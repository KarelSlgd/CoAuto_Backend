import json
from connection import get_connection
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
                        id_user AS idUser,
                        id_cognito AS idCognito,
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
                    'idUser': row[0],
                    'idCognito': row[1],
                    'email': row[2],
                    'name': row[3],
                    'lastname': row[4],
                    'role': row[5],
                    'status': row[6],
                    'profile_image': row[7]
                }
                users.append(user)

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers_cors,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        connection.close()

    return {
        "statusCode": 200,
        'headers': headers_cors,
        "body": json.dumps({
            "data": users
        }),
    }
