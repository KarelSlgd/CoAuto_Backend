import unittest
from unittest.mock import patch, MagicMock
import json
from car.get_data_car.app import lambda_handler, get_jwt_claims
from car.get_data_car.connection import get_connection, get_secret, handle_response, headers_cors
from botocore.exceptions import ClientError


class TestGetCar(unittest.TestCase):

    @patch('car.get_data_car.app.get_connection')
    @patch('car.get_data_car.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [
                (1, 'Model S', 'Tesla', 2020, 79999, 'Sedan', 'Electric', 4, 'Dual Motor', 1445, 1960, 4970,
                 'A luxury electric car', 'Available'),
            ],
            [
                ('http://example.com/image1.jpg',),
                ('http://example.com/image2.jpg',)
            ]
        ]

        event = {}
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers'], {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
        })

        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'get cars')
        self.assertTrue('data' in body)
        self.assertEqual(len(body['data']), 1)
        self.assertEqual(body['data'][0]['model'], 'Model S')
        self.assertEqual(body['data'][0]['brand'], 'Tesla')
        self.assertEqual(body['data'][0]['images'], [
            'http://example.com/image1.jpg',
            'http://example.com/image2.jpg'
        ])

    def test_get_jwt_claims_success(self):
        token = "header.payload.signature"
        payload = {
            "cognito:groups": ["UserGroup"]
        }
        with patch('base64.b64decode', return_value=json.dumps(payload).encode('utf-8')):
            claims = get_jwt_claims(token)
            self.assertEqual(claims['cognito:groups'], ["UserGroup"])

    def test_get_jwt_claims_invalid_token(self):
        token = "invalid.token"

        with self.assertRaises(ValueError) as context:
            get_jwt_claims(token)

        self.assertEqual(str(context.exception), "Token inválido")

    # Test for connection.py

    @patch('car.get_data_car.connection.boto3.session.Session')
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

    @patch('car.get_data_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.get_data_car.connection.pymysql.connect')
    @patch('car.get_data_car.connection.get_secret')
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

    @patch('car.get_data_car.connection.pymysql.connect')
    @patch('car.get_data_car.connection.get_secret')
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
