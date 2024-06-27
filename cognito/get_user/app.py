import json
import boto3
import pymysql
from database import get_connection, close_connection, get_secret


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
    except (TypeError, KeyError, json.JSONDecodeError):
        return {
            'statusCode': 400,
            'body': 'Invalid request body.'
        }

    token = body.get('token')

    try:
        response = get_info(token)
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }


def get_info(token):
    try:
        client = boto3.client('cognito-idp')
        response = client.get_user(
            AccessToken=token
        )

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(f'An error occurred: {str(e)}')
        }

    user = get_into_user(response['Username'])

    secrets = get_secret()
    response_role = client.admin_list_groups_for_user(
        Username=user['email'],
        UserPoolId=secrets['COGNITO_USER_POOL_ID']
    )
    groups = [group['GroupName'] for group in response_role['Groups']]

    return {
        'statusCode': 200,
        'body': json.dumps({
            'userAttributes': response['UserAttributes'],
            'user': user,
            'groups': groups
        })
    }


def get_into_user(token):
    connection = get_connection()
    try:
        query = """SELECT 
                        id_user, 
                        id_cognito, 
                        email,
                        u.name AS nameUser,
                        lastname, 
                        r.name AS nameRole,
                        s.value 
                    FROM user u
                    INNER JOIN role r 
                        ON u.id_role = r.id_role 
                    INNER JOIN status s 
                        ON u.id_status = s.id_status
                    WHERE id_cognito = '{token}';""".format(token=token)

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(query)
            result = cursor.fetchone()
            user = {
                'idUser': result['id_user'],
                'idCognito': result['id_cognito'],
                'email': result['email'],
                'name': result['nameUser'],
                'lastname': result['lastname'],
                'role': result['nameRole'],
                'status': result['value']
            }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'An error occurred: {str(e)}'
            })
        }

    finally:
        close_connection(connection)

    return user
