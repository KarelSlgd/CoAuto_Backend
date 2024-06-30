import json
from connection import get_connection


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
                        s.value 
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
                    'idUser': row['idUser'],
                    'idCognito': row['idCognito'],
                    'email': row['email'],
                    'name': row['nameUser'],
                    'lastname': row['lastname'],
                    'role': row['nameRole'],
                    'status': row['value']
                }
                users.append(user)

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get users",
            "data": users
        }),
    }
