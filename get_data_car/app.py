import json
import pymysql
import os

rds_host = os.environ['RDS_HOST']
rds_user = os.environ['DB_USERNAME']
rds_password = os.environ['DB_PASSWORD']
rds_db = os.environ['DB_NAME']


def lambda_handler(event, context):
    connection = pymysql.connect(
        host=rds_host,
        user=rds_user,
        password=rds_password,
        database=rds_db
    )

    cars = []

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_auto, model, brand, year, category, fuel,doors,motor,heigth,width,length,weigth,detais,id_status FROM auto")
            result = cursor.fetchall()

            for row in result:
                car = {
                    'id_auto': row[0],
                    'model': row[1],
                    'brand': row[2],
                    'year': row[3],
                    'category': row[4],
                    'fuel': row[5],
                    'doors':row[6],
                    'motor':row[7],
                    'heigth':row[8],
                    'width':row[9],
                    'length':row[10],
                    'weigth':row[11],
                    'detais':row[12],
                    'id_Status':row[13]
                }
                cars.append(car)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get cars",
            "data": car
        }),
    }
