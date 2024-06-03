import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']

def lambda_handler(event, context):
    id = event['id']
    status = event['status']

    if not id or not status:
        return {
            'statusCode': 400,
            'body': 'Missing parameters.'
        }

    response = delete_user(id, status)

    return response

def delete_user(id, status):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE user SET status=%s WHERE id=%s", (status, id))
            connection.commit()

    except Exception as e:
        return {
            'statusCode': 500,
            'body': 'Failed to delete user.'
        }

    finally:
        connection.close()

    return {
        'statusCode': 200,
        'body': 'User deleted successfully.'
    }