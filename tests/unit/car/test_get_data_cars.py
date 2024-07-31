import unittest
from unittest.mock import patch, MagicMock
import json
import pymysql
from car.get_data_cars.app import lambda_handler
from car.get_data_cars.connection import get_secret, get_connection, handle_response, handle_response_success, headers_cors
from botocore.exceptions import ClientError


class TestGetDataCars(unittest.TestCase):
    @patch('car.get_data_cars.app.get_connection')
    @patch('car.get_data_cars.app.handle_response_success')
    def test_lambda_handler(self, mock_handle_response_success, mock_get_connection):
        # Simulación de la conexión
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        # Simulación de los resultados de las consultas
        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2021, 35000, 'SUV', 'Gasoline', 4, 'V6', 1700, 2000, 4500, 'A great car', 'Available'),
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',),
            ],
            [
                (5,),
                (4,),
                (3,),
            ]
        ]

        mock_handle_response_success.return_value = {'statusCode': 200, 'body': 'Mocked response'}

        event = {}
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], 'Mocked response')

        expected_cars = [{
            'id_auto': 1,
            'model': 'Model X',
            'brand': 'Brand Y',
            'year': 2021,
            'price': "$35,000.00",
            'type': 'SUV',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': 'V6',
            'height': 1700,
            'width': 2000,
            'length': 4500,
            'description': 'A great car',
            'status': 'Available',
            'images': [
                'http://example.com/image1.jpg',
                'http://example.com/image2.jpg'
            ],
            'average_rating': 4.0
        }]
        mock_handle_response_success.assert_called_once_with(200, 'Autos obtenidos correctamente', expected_cars)


    @patch("car.get_data_cars.app.get_connection")
    @patch("car.get_data_cars.app.handle_response_success")
    def test_lambda_handler_no_data(self, mock_handle_response_success, mock_get_connection):
        # Simulación de la conexión y el cursor de la base de datos
        mock_conn = mock_get_connection.return_value
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        # Simulación de resultados vacíos de las consultas
        mock_cursor.fetchall.side_effect = [[], [], [], []]

        # Llamada a la función lambda_handler
        event = {}
        context = {}
        response = lambda_handler(event, context)

        # Verificación de los resultados esperados
        mock_handle_response_success.assert_called_once_with(200, 'Autos obtenidos correctamente', [])
        self.assertEqual(response, mock_handle_response_success.return_value)

    @patch("car.get_data_cars.app.get_connection")
    def test_lambda_handler_connection_fail(self, mock_get_connection):
        # Simulación de un error en la conexión a la base de datos
        mock_get_connection.side_effect = Exception("Connection error")

        # Llamada a la función lambda_handler
        event = {}
        context = {}
        with self.assertRaises(Exception) as context:
            lambda_handler(event, context)

        self.assertTrue('Connection error' in str(context.exception))

    # Test for connection.py

    @patch('car.get_data_cars.connection.boto3.session.Session.client')
    def test_get_secret(self, mock_boto_client):
        mock_client = mock_boto_client.return_value
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'test_host',
                'USERNAME': 'test_user',
                'PASSWORD': 'test_password',
                'DB_NAME': 'test_db'
            })
        }

        secret = get_secret()
        self.assertEqual(secret['HOST'], 'test_host')
        self.assertEqual(secret['USERNAME'], 'test_user')
        self.assertEqual(secret['PASSWORD'], 'test_password')
        self.assertEqual(secret['DB_NAME'], 'test_db')

    @patch('car.get_data_cars.connection.pymysql.connect')
    @patch('car.get_data_cars.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_pymysql_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }

        mock_connection = mock_pymysql_connect.return_value

        connection = get_connection()
        mock_pymysql_connect.assert_called_once_with(
            host='test_host',
            user='test_user',
            password='test_password',
            database='test_db'
        )
        self.assertEqual(connection, mock_connection)

    def test_handle_response(self):
        response = handle_response('TestError', 'TestMessage', 400)
        expected_response = {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 400,
                'message': 'TestMessage',
                'error': 'TestError'
            })
        }
        self.assertEqual(response, expected_response)

    def test_handle_response_success(self):
        response = handle_response_success(200, 'TestMessage', {'key': 'value'})
        expected_response = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'TestMessage',
                'data': {'key': 'value'}
            })
        }
        self.assertEqual(response, expected_response)

    @patch('car.get_data_cars.connection.pymysql.connect')
    @patch('car.get_data_cars.connection.get_secret')
    def test_get_connection_exception(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }
        mock_connect.side_effect = pymysql.MySQLError("Connection error")

        with self.assertRaises(pymysql.MySQLError):
            get_connection()

    @patch('car.get_data_cars.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
