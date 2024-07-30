import unittest
from unittest.mock import patch
import json
from rate.search_rate_by.app import lambda_handler, handle_response
from botocore.exceptions import ClientError
from rate.search_rate_by.connection import get_secret, headers_cors, get_connection


class TestSearchRateBy(unittest.TestCase):

    @patch('rate.search_rate_by.app.get_connection')
    @patch('rate.search_rate_by.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': {'type': 'modelo', 'value': 'Civic'}
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [
            (1, 5, 'Great car!', 'Civic', 'Honda', 'John', 'Doe', 1, 'profile_image_url', 'Active', 2020,
             'john@example.com')
        ]

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Reseñas obtenidas correctamente.')
        self.assertTrue(len(body['data']) > 0)
        mock_connection.close.assert_called_once()

    @patch('rate.search_rate_by.connection.pymysql.connect')
    @patch('rate.search_rate_by.connection.get_secret')
    def test_lambda_handler_missing_parameters(self, mock_get_secret, mock_connect):
        event = {
            'queryStringParameters': {'type': 'modelo'}
        }
        context = {}

        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }

        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        mock_cursor.execute.assert_not_called()
        mock_connect.assert_called_once()

    @patch('rate.search_rate_by.connection.pymysql.connect')
    @patch('rate.search_rate_by.connection.get_secret')
    def test_lambda_handler_invalid_type(self, mock_get_secret, mock_connect):
        event = {
            'queryStringParameters': {'type': 'color', 'value': 'red'}
        }
        context = {}

        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }

        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        mock_cursor.execute.assert_not_called()
        mock_connect.assert_called_once()

    @patch('rate.search_rate_by.app.get_connection')
    @patch('rate.search_rate_by.app.handle_response')
    def test_lambda_handler_exception(self, mock_handle_response, mock_get_connection):
        event = {
            'queryStringParameters': {'type': 'modelo', 'value': 'Civic'}
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception('Database error')

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(unittest.mock.ANY, 'Ocurrió un error al obtener la reseña', 500)
        mock_connection.close.assert_called_once()

    @patch('rate.search_rate_by.connection.pymysql.connect')
    @patch('rate.search_rate_by.connection.get_secret')
    def test_lambda_handler_no_query_params(self, mock_get_secret, mock_connect):
        event = {
            'body': json.dumps({})
        }
        context = {}

        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }

        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Debe proporcionar los parámetros: type y value', json.loads(response['body'])['message'])
        mock_cursor.execute.assert_not_called()
        mock_connect.assert_called_once()

    @patch('rate.search_rate_by.connection.boto3.session.Session')
    def test_get_secret(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
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

    @patch('rate.search_rate_by.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('rate.search_rate_by.connection.pymysql.connect')
    @patch('rate.search_rate_by.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        connection = mock_connect.return_value

        result = get_connection()

        self.assertEqual(result, connection)
        mock_connect.assert_called_with(
            host='localhost',
            user='user',
            password='pass',
            database='database'
        )

    @patch('rate.search_rate_by.connection.pymysql.connect')
    @patch('rate.search_rate_by.connection.get_secret')
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
