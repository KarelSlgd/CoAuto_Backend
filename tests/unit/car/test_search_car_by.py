import unittest
from unittest.mock import patch, MagicMock
import json
from car.search_car_by.app import build_query, lambda_handler
from car.search_car_by.connection import headers_cors, get_connection, get_secret, handle_response
from botocore.exceptions import ClientError


class TestMyModule(unittest.TestCase):

    def test_build_query_no_filters(self):
        filters = {}
        expected_query = "SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status"
        expected_params = []

        query, params = build_query(filters)

        self.assertEqual(query, expected_query)
        self.assertEqual(params, expected_params)

    def test_build_query_with_filters(self):
        filters = {'year': 2020, 'price': 20000, 'model': 'Civic', 'brand': 'Honda', 'doors': 4}
        expected_query = (
            "SELECT id_auto, model, brand, year, price, type, fuel, doors, engine, height, width, length, "
            "a.description, s.value FROM auto a INNER JOIN status s ON a.id_status = s.id_status WHERE year = %s "
            "AND price <= %s AND model = %s AND brand = %s AND doors = %s")
        expected_params = [2020, 20000, 'Civic', 'Honda', 4]

        query, params = build_query(filters)

        self.assertEqual(query, expected_query)
        self.assertEqual(params, expected_params)

    @patch('car.search_car_by.app.get_connection')
    def test_lambda_handler(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        event = {
            'queryStringParameters': {
                'year': '2020'
            }
        }
        context = {}

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Civic', 'Honda', 2020, 20000, 'Sedan', 'Gasoline', 4, '2.0L', 140, 70, 180, 'A good car',
                 'Available')
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',)
            ]
        ]

        response = lambda_handler(event, context)
        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body['statusCode'], 200)
        self.assertEqual(response_body['message'], 'Carros encontrados')
        self.assertEqual(len(response_body['data']), 1)
        self.assertEqual(response_body['data'][0]['model'], 'Civic')
        self.assertEqual(response_body['data'][0]['images'],
                         ['http://example.com/image1.jpg', 'http://example.com/image2.jpg'])

    # Test for connection.py

    @patch('car.search_car_by.connection.boto3.session.Session')
    def test_get_secret(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'localhost',
                'USERNAME': 'user',
                'PASSWORD': 'pass',
                'DB_NAME': 'database'
            })
        }

        secret = get_secret()

        self.assertEqual(secret['HOST'], 'localhost')
        self.assertEqual(secret['USERNAME'], 'user')
        self.assertEqual(secret['PASSWORD'], 'pass')
        self.assertEqual(secret['DB_NAME'], 'database')
        mock_client.get_secret_value.assert_called_with(SecretId='COAUTO')

    @patch('car.search_car_by.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.search_car_by.connection.pymysql.connect')
    @patch('car.search_car_by.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        connection = MagicMock()
        mock_connect.return_value = connection

        result = get_connection()

        self.assertEqual(result, connection)
        mock_connect.assert_called_with(
            host='localhost',
            user='user',
            password='pass',
            database='database'
        )

    @patch('car.search_car_by.connection.pymysql.connect')
    @patch('car.search_car_by.connection.get_secret')
    def test_get_connection_error(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        mock_connect.side_effect = Exception('Connection error')

        with self.assertRaises(Exception) as context:
            get_connection()

        self.assertTrue('Connection error' in str(context.exception))

    def test_handle_response(self):
        error = Exception('Test Error')
        message = 'Test Message'
        status_code = 400

        response = handle_response(error, message, status_code)

        expected_response = {
            'statusCode': status_code,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': status_code,
                'message': message,
                'error': str(error)
            })
        }

        self.assertEqual(response, expected_response)
