import pymysql
import os
import re
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
    value = body.get('value')
    comment = body.get('comment')
    id_auto = body.get('id_auto')
    id_user = body.get('id_user')
    value_n = 0
    try:
        value_n = int(value)
    except:
        return {
            'statusCode': 400,
            'body': 'Invalid rate value format.'
        }
    if not value or not id_auto or not id_user:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }
    if value_n > 5 or value_n < 1:
        return {
            'statusCode': 400,
            'body': 'Rate value out of range.'
        }
    comment_regex = r'^[a-zA-Z0-9]+$'
    if not re.match(comment_regex, comment):
        return {
            'statusCode': 400,
            'body': 'Invalid comment format.'
        }
    if len(comment) > 100:
        return {
            'statusCode': 400,
            'body': 'Comment exceeds 100 characters.'
        }
    if not (verify_user(id_user)):
        return {
            'statusCode': 400,
            'body': 'User does not exist.'
        }
    if not(verify_auto(id_auto)):
        return {
            'statusCode': 400,
            'body': 'Auto does not exist.'
        }
    response = insert_into_rate(value_n, comment, id_auto, id_user)
    return response
def insert_into_rate(value, comment, id_auto, id_user):
    connection = pymysql.connect(
        host = rds_host,
        user = rds_user,
        password = rds_password,
        database = rds_db
    )
    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO rate (value, comment, id_auto, id_user) VALUES (%s, %s, %s, %s)"
            cursor.execute(insert_query, (value, comment, id_auto, id_user))
            connection.commit()
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'An error has occurred: {str(e)}'
        }
    finally:
        connection.close()

def verify_user(id_user):
    connection = pymysql.connect(
        host = rds_host,
        user = rds_user,
        password = rds_password,
        database = rds_db
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_user FROM user WHERE id_user = %s", id_user)
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        return False
    finally:
        connection.close()
def verify_auto(id_auto):
    connection = pymysql.connect(
        host = rds_host,
        user = rds_user,
        password = rds_password,
        database = rds_db
    )
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_auto FROM auto WHERE id_auto = %s", id_auto)
            result = cursor.fetchone()
            return result is not None
    except:
        return False
    finally:
        connection.close()
