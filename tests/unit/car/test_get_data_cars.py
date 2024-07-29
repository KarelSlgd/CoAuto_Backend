import unittest
from unittest.mock import patch, MagicMock
import json
from car.get_data_cars.app import lambda_handler, headers_cors
from car.get_data_cars.connection import get_secret, get_connection, handle_response
from botocore.exceptions import ClientError


class TestGetDataCars(unittest.TestCase):

    @patch('car.get_data_cars.app.get_connection')
    def test_lambda_handler_success(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model S', 'Tesla', 2020, 80000, 'Sedan', 'Electric', 4, 'Dual Motor', 1445, 1964, 4970, 'Electric car', 'Available')
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',)
            ],
            [
                (5,),
                (4,)
            ]
        ]

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_body = json.dumps({
            'statusCode': 200,
            'message': 'get cars',
            'data': [
                {
                    'id_auto': 1,
                    'model': 'Model S',
                    'brand': 'Tesla',
                    'year': 2020,
                    'price': "$80,000.00",
                    'type': 'Sedan',
                    'fuel': 'Electric',
                    'doors': 4,
                    'engine': 'Dual Motor',
                    'height': 1445,
                    'width': 1964,
                    'length': 4970,
                    'description': 'Electric car',
                    'status': 'Available',
                    'images': [
                        'http://example.com/image1.jpg',
                        'http://example.com/image2.jpg'
                    ],
                    'average_rating': 4.5
                }
            ]
        })

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers'], headers_cors)
        self.assertEqual(response['body'], expected_body)

    @patch('car.get_data_cars.app.get_connection')
    def test_lambda_handler_no_ratings(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model X', 'Brand Y', 2020, 30000, 'SUV', 'Petrol', 4, 'V6', 1500, 2000, 4500, 'Description',
                 'Available')
            ],
            [],
            []
        ]

        event = {}
        context = {}
        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'get cars')
        self.assertEqual(len(body['data']), 1)
        self.assertEqual(body['data'][0]['average_rating'], 0)

        self.assertEqual(mock_cursor.fetchall.call_count, 3)

    @patch('car.get_data_cars.app.get_connection')
    def test_lambda_handler_no_cars(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        mock_cursor.fetchall.side_effect = [
            [],
            [],
            []
        ]

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_body = json.dumps({
            'statusCode': 200,
            'message': 'get cars',
            'data': []
        })

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers'], headers_cors)
        self.assertEqual(response['body'], expected_body)

    # Test for connection.py

    @patch('car.get_data_cars.connection.boto3.session.Session')
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

    @patch('car.get_data_cars.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.get_data_cars.connection.pymysql.connect')
    @patch('car.get_data_cars.connection.get_secret')
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

    @patch('car.get_data_cars.connection.pymysql.connect')
    @patch('car.get_data_cars.connection.get_secret')
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
