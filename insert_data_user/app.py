import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']

def lambda_handler(event, context):
    email = event['pathParameters'].get('email')
    name = event['pathParameters'].get('name')
    phone_number = event['pathParameters'].get('phone_number')
    profile_image_url = event['pathParameters'].get('profile_image_url')
    role = event['pathParameters'].get('role')
    password = event['pathParameters'].get('password')

    if not email or not name or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    insert_into_user(email, name, phone_number, profile_image_url, role, password)

    return {
        'statusCode': 200,
        'body': 'Record inserted successfully.'
    }


def insert_into_user(email, name, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(host=rds_host, user=rds_user, passwd=rds_password, db=rds_db)

    try:
        with connection.cursor() as cursor:
            insert_query = "INSERT INTO user (email, name, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (email, name, phone_number, profile_image_url, role, password))
            connection.commit()
    finally:
        connection.close()