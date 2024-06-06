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
            cursor.execute("SELECT id_auto, model, brand, year,price, category, fuel,doors,motor,height,width,length,weight,detais,id_status FROM auto")
            result = cursor.fetchall()

            for row in result:
                car = {
                    'id_auto': row[0],
                    'model': row[1],
                    'brand': row[2],
                    'price':row[3],
                    'year': row[4],
                    'category': row[5],
                    'fuel': row[6],
                    'doors':row[7],
                    'motor':row[8],
                    'height':row[9],
                    'width':row[10],
                    'length':row[11],
                    'weight':row[12],
                    'detais':row[13],
                    'id_Status':row[14]
                }
                cars.append(car)

    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "get cars",
            "data": cars
        }),
    }
