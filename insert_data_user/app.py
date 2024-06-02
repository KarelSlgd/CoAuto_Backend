import pymysql

rds_host = 'integradora-desarrollo.cd4gi2og06nk.us-east-2.rds.amazonaws.com'
rds_user = 'root'
rds_password = 'superroot'
rds_db = 'coauto'

def lambda_handler(event, __):
    email = event['pathParameters'].get('email')
    name = event['pathParameters'].get('name')
    phone_number = event['pathParameters'].get('phone_number')
    profile_image_url = event['pathParameters'].get('profile_image_url')
    role = event['pathParameters'].get('role')
    password = event['pathParameters'].get('password')

    if not email or not name or not phone_number or not phone_number or not role or not password:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    insert_into_user(name, email, phone_number, profile_image_url, role, password)

    return {
        "statusCode": 200,
        "body": "User inserted successfully."
    }


def insert_into_user(name, email, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        db=rds_db
    )

    try:
        with connection.cursor() as cursor:
            insert_query = """INSERT INTO user (name, email, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (name, email, phone_number, profile_image_url, role, password))
            connection.commit()
    finally:
        connection.close()
