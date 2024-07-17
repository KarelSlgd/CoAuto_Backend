import unittest
from unittest.mock import patch, MagicMock
import json
from rate.get_data_rate.app import lambda_handler, get_connection, handle_response, headers_cors
from rate.get_data_rate.database import get_secret
from botocore.exceptions import ClientError


class TestGetRate(unittest.TestCase):

    @patch('rate.get_data_rate.app.get_connection')
    @patch('rate.get_data_rate.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            (1, 5, 'Great car!', 'Model S', 'Tesla', 'John', 'Doe', 101, 'profile.jpg', 'active')
        ]
        mock_get_connection.return_value = mock_connection

        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_body = {
            'statusCode': 200,
            "message": "Reseñas obtenidas correctamente.",
            "data": [
                {
                    'id_rate': 1,
                    'value': 5,
                    'comment': 'Great car!',
                    'model': 'Model S',
                    'brand': 'Tesla',
                    'name': 'John',
                    'lastname': 'Doe',
                    'id_auto': 101,
                    'profile_image': 'profile.jpg',
                    'status': 'active'
                }
            ]
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertEqual(json.loads(response['body']), expected_body)

    @patch('rate.get_data_rate.app.get_connection')
    @patch('rate.get_data_rate.app.handle_response')
    def test_lambda_handler_exception(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_connection.cursor.side_effect = Exception('Database error')
        mock_get_connection.return_value = mock_connection

        event = {}
        context = {}

        mock_handle_response.return_value = {
            "statusCode": 500,
            'headers': headers_cors,
            "body": json.dumps({
                'statusCode': 500,
                "message": "Ocurrió un error al obtener la reseña"
            }),
        }

        response = lambda_handler(event, context)

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['headers']['Access-Control-Allow-Origin'], '*')
        self.assertIn('Ocurrió un error al obtener la reseña', response_body['message'])

    # Test for connection.py

    @patch('rate.get_data_rate.database.boto3.session.Session')
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

    @patch('rate.get_data_rate.database.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('rate.get_data_rate.database.pymysql.connect')
    @patch('rate.get_data_rate.database.get_secret')
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

    @patch('rate.get_data_rate.database.pymysql.connect')
    @patch('rate.get_data_rate.database.get_secret')
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
