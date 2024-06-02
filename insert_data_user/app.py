import json
import pymysql
import bcrypt

rds_host = 'integradora-desarrollo.cd4gi2og06nk.us-east-2.rds.amazonaws.com'
name = 'root'
db_password = 'superroot'
db_name = 'coauto'

def lambda_handler(event, __):
    body = json.loads(event["body"])

    email = body.get("email")
    phone_number = body.get("phone_number")
    profile_image_url = body.get("profile_image_url")
    role = body.get("role")
    password = body.get("password")

    if not email or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    hashed_password = hash_password(password)
    insert_into_user(email, phone_number, profile_image_url, role, hashed_password)

    return {
        'statusCode': 200,
        'body': 'User inserted successfully.'
    }

def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed

def insert_into_user(email, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=name,
        password=db_password,
        database=db_name
    )

    try:
        with connection.cursor() as cursor:
            insert_query = """
            INSERT INTO user (email, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (email, phone_number, profile_image_url, role, password))
            connection.commit()
    finally:
        connection.close()
