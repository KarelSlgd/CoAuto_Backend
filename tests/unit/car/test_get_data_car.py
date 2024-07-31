import unittest
from unittest.mock import patch, MagicMock
import json
import pymysql
from car.get_data_car.app import lambda_handler
from car.get_data_car.connection import get_connection, get_secret, handle_response, headers_cors, \
    handle_response_success
from botocore.exceptions import ClientError


class TestGetCar(unittest.TestCase):
    @patch("car.get_data_car.app.get_connection")
    @patch("car.get_data_car.app.handle_response_success")
    def test_lambda_handler_success(self, mock_handle_response_success, mock_get_connection):
        mock_conn = mock_get_connection.return_value
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand A', 2020, 30000, 'SUV', 'Gasoline', 4, 'V8', 150, 200, 400, 'Description X',
                 'Available'),
                (2, 'Model Y', 'Brand B', 2021, 35000, 'Sedan', 'Diesel', 4, 'V6', 140, 190, 380, 'Description Y',
                 'Sold')
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',)
            ],
            [
                ('http://example.com/image3.jpg',)
            ]
        ]

        event = {}
        context = {}
        response = lambda_handler(event, context)

        expected_cars = [
            {
                'id_auto': 1,
                'model': 'Model X',
                'brand': 'Brand A',
                'year': 2020,
                'price': 30000,
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': 4,
                'engine': 'V8',
                'height': 150,
                'width': 200,
                'length': 400,
                'description': 'Description X',
                'status': 'Available',
                'images': ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
            },
            {
                'id_auto': 2,
                'model': 'Model Y',
                'brand': 'Brand B',
                'year': 2021,
                'price': 35000,
                'type': 'Sedan',
                'fuel': 'Diesel',
                'doors': 4,
                'engine': 'V6',
                'height': 140,
                'width': 190,
                'length': 380,
                'description': 'Description Y',
                'status': 'Sold',
                'images': ['http://example.com/image3.jpg']
            }
        ]

        mock_handle_response_success.assert_called_once_with(200, 'Todos los autos obtenidos correctamente.',
                                                             expected_cars)
        self.assertEqual(response, mock_handle_response_success.return_value)

    @patch("car.get_data_car.app.get_connection")
    @patch("car.get_data_car.app.handle_response_success")
    def test_lambda_handler_no_data(self, mock_handle_response_success, mock_get_connection):
        mock_conn = mock_get_connection.return_value
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value

        mock_cursor.fetchall.side_effect = [[], []]

        event = {}
        context = {}
        response = lambda_handler(event, context)

        mock_handle_response_success.assert_called_once_with(200, 'Todos los autos obtenidos correctamente.', [])
        self.assertEqual(response, mock_handle_response_success.return_value)

    @patch("car.get_data_car.app.get_connection")
    def test_lambda_handler_connection_fail(self, mock_get_connection):
        mock_get_connection.side_effect = Exception("Connection error")

        # Llamada a la función lambda_handler
        event = {}
        context = {}
        with self.assertRaises(Exception) as context:
            lambda_handler(event, context)

        self.assertTrue('Connection error' in str(context.exception))

    # Test for connection.py

    @patch('car.get_data_car.connection.boto3.session.Session.client')
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

    @patch('car.get_data_car.connection.pymysql.connect')
    @patch('car.get_data_car.connection.get_secret')
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

    @patch('car.get_data_car.connection.pymysql.connect')
    @patch('car.get_data_car.connection.get_secret')
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

    @patch('car.get_data_car.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
