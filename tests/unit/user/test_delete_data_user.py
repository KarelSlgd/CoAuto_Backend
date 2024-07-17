import unittest
from unittest.mock import patch, MagicMock
import json

from botocore.exceptions import ClientError
from user.delete_data_user.app import lambda_handler, get_username_by_id, get_status_value
from user.delete_data_user.connection import get_connection, get_secret, handle_response

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


class TestDeleteUser(unittest.TestCase):

    @patch('user.delete_data_user.app.get_connection')
    @patch('user.delete_data_user.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_get_connection):
        event = {'body': 'invalid_json'}
        context = {}

        mock_handle_response.return_value = {'statusCode': 400,
                                             'body': json.dumps({'message': 'Cuerpo de la solicitud no válido.'})}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'Cuerpo de la solicitud no válido.', 400)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Cuerpo de la solicitud no válido.', json.loads(response['body'])['message'])

    @patch('user.delete_data_user.app.get_connection')
    @patch('user.delete_data_user.app.handle_response')
    def test_lambda_handler_missing_parameters(self, mock_handle_response, mock_get_connection):
        event = {'body': json.dumps({'id_user': '123'})}
        context = {}

        mock_handle_response.return_value = {'statusCode': 400, 'body': json.dumps({'message': 'Faltan parámetros.'})}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'Faltan parámetros.', 400)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Faltan parámetros.', json.loads(response['body'])['message'])

    @patch('user.delete_data_user.app.get_status_value')
    @patch('user.delete_data_user.app.update_user_status')
    @patch('user.delete_data_user.app.get_connection')
    @patch('user.delete_data_user.app.handle_response')
    def test_lambda_handler_valid_request(self, mock_handle_response, mock_get_connection, mock_update_user_status,
                                          mock_get_status_value):
        event = {'body': json.dumps({'id_user': '123', 'id_status': '456'})}
        context = {}

        mock_get_status_value.return_value = 1
        mock_update_user_status.return_value = {'statusCode': 200,
                                                'body': json.dumps({'message': 'Usuario actualizado correctamente.'})}

        response = lambda_handler(event, context)

        mock_update_user_status.assert_called_with('123', '456', 1)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Usuario actualizado correctamente.', json.loads(response['body'])['message'])

    @patch('user.delete_data_user.app.get_connection')
    def test_get_username_by_id(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ['user@example.com']

        username = get_username_by_id('123')

        mock_cursor.execute.assert_called_with("SELECT email FROM user WHERE id_user=%s", ('123',))
        self.assertEqual(username, 'user@example.com')

    @patch('user.delete_data_user.app.get_connection')
    def test_get_status_value(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [1]

        value = get_status_value('456')

        mock_cursor.execute.assert_called_with("SELECT value FROM status WHERE id_status=%s AND description='to_user'",
                                               ('456',))
        self.assertEqual(value, 1)

    #Tests for connection.py
    @patch('user.delete_data_user.connection.boto3.session.Session')
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

    @patch('user.delete_data_user.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('user.delete_data_user.connection.pymysql.connect')
    @patch('user.delete_data_user.connection.get_secret')
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

    @patch('user.delete_data_user.connection.pymysql.connect')
    @patch('user.delete_data_user.connection.get_secret')
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
