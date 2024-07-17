import unittest
from unittest.mock import patch, MagicMock
import json
from car.delete_data_car.app import lambda_handler, delete_car
from car.delete_data_car.connection import get_secret, get_connection, handle_response, headers_cors
from botocore.exceptions import ClientError


class TestDeleteCar(unittest.TestCase):

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'id_auto': 1, 'id_status': 2})
        }
        context = {}

        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id_status': 2, 'name': 'to_auto'}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Auto actualizado correctamente', response['body'])

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_lambda_handler_missing_parameters(self, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'id_auto': 1})
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_get_connection):
        event = {
            'body': 'invalid json'
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(
            unittest.mock.ANY, 'Parametros inválidos', 400
        )

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_invalid_status(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        response = delete_car(1, 2)

        mock_handle_response.assert_called_once_with(None, 'El status no es válido para autos.', 400)

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_success(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {'id_status': 2, 'name': 'to_auto'}

        response = delete_car(1, 2)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Auto actualizado correctamente', response['body'])

    @patch('car.delete_data_car.app.get_connection')
    @patch('car.delete_data_car.app.handle_response')
    def test_delete_car_exception(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = Exception("Database error")

        response = delete_car(1, 2)

        mock_handle_response.assert_called_once_with(unittest.mock.ANY, 'Error al actualizar auto.', 500)

    # Test for connection.py

    @patch('car.delete_data_car.connection.boto3.session.Session')
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

    @patch('car.delete_data_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.delete_data_car.connection.pymysql.connect')
    @patch('car.delete_data_car.connection.get_secret')
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

    @patch('car.delete_data_car.connection.pymysql.connect')
    @patch('car.delete_data_car.connection.get_secret')
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
