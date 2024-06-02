import pymysql

rds_host = 'integradora-desarrollo.cd4gi2og06nk.us-east-2.rds.amazonaws.com'
name = 'root'
password2 = 'superroot'
db_name = 'coauto'


def lambda_handler(event, __):
    email = event['pathParameters'].get('email')
    name = event['pathParameters'].get('name')
    phone_number = event['pathParameters'].get('phone_number')
    profile_image_url = event['pathParameters'].get('profile_image_url')
    role = event['pathParameters'].get('role')
    password = event['pathParameters'].get('password')

    insert_into_user(name, email, phone_number, profile_image_url, role, password)

    return {
        "statusCode": 200,
        "body": "User inserted successfully."
    }


def insert_into_user(name, email, phone_number, profile_image_url, role, password):
    connection = pymysql.connect(
        host=rds_host,
        user=name,
        password=password2,
        database=db_name
    )
    try:
        with connection.cursor() as cursor:
            insert_query = """
                INSERT INTO user (name, email, phone_number, profile_image_url, role, password) VALUES (%s, %s, %s, %s, %s, %s)
                """
            cursor.execute(insert_query, (name, email, phone_number, profile_image_url, role, password))
            connection.commit()
    finally:
        connection.close()
