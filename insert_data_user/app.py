import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

rds_host = os.getenv('SONAR_TOKEN', 'default_value')
if not rds_host:
    raise ValueError("RDS_HOST environment variable is not set.")


def lambda_handler(event, context):
   return {
        'statusCode': rds_host,
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