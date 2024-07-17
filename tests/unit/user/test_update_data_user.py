import unittest
from unittest.mock import patch, MagicMock
import json
from user.update_data_user.app import lambda_handler, update_user, headers_cors
from user.update_data_user.connection import get_connection, get_secret, handle_response
from botocore.exceptions import ClientError


class TestUpdateUser(unittest.TestCase):
    def test_invalid_request_body(self):
        event = {
            'body': 'invalid json'
        }
        response = lambda_handler(event, None)
        expected_response = handle_response(None, 'Cuerpo de la solicitud no válido.', 400)
        self.assertEqual(response, expected_response)

    def test_missing_parameters(self):
        event = {
            'body': json.dumps({})
        }
        response = lambda_handler(event, None)
        expected_response = handle_response(None, 'Faltan parámetros.', 400)
        self.assertEqual(response, expected_response)

    def test_name_too_long(self):
        event = {
            'body': json.dumps({'id_user': '123', 'name': 'a' * 51})
        }
        response = lambda_handler(event, None)
        expected_response = handle_response(None, 'El nombre no debe exceder los 50 caracteres.', 400)
        self.assertEqual(response, expected_response)

    def test_lastname_too_long(self):
        event = {
            'body': json.dumps({'id_user': '123', 'lastname': 'a' * 101})
        }
        response = lambda_handler(event, None)
        expected_response = handle_response(None, 'El apellido no debe exceder los 100 caracteres.', 400)
        self.assertEqual(response, expected_response)

    @patch('user.update_data_user.app.get_connection')
    def test_successful_update(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        mock_cursor.execute.return_value = None
        mock_connection.commit.return_value = None

        event = {
            'body': json.dumps({'id_user': '123', 'name': 'John', 'lastname': 'Doe'})
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Usuario actualizado correctamente')

    @patch('user.update_data_user.app.get_connection')
    def test_update_user_successful(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_get_connection.return_value = mock_connection

        response = update_user('123', 'John', 'Doe')
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Usuario actualizado correctamente')
        mock_cursor.execute.assert_called_once_with(
            "UPDATE user SET name=%s, lastname=%s WHERE id_user=%s",
            ('John', 'Doe', '123')
        )
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('user.update_data_user.app.get_connection')
    def test_update_user_failure(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception('Database error')
        mock_get_connection.return_value = mock_connection

        response = update_user('123', 'John', 'Doe')
        expected_response = handle_response(Exception('Database error'), 'Ocurrió un error al actualizar usuario.', 500)
        self.assertEqual(response, expected_response)
        mock_connection.close.assert_called_once()

    # Test for connection

    @patch('user.update_data_user.connection.boto3.session.Session')
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

    @patch('user.update_data_user.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('user.update_data_user.connection.pymysql.connect')
    @patch('user.update_data_user.connection.get_secret')
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

    @patch('user.update_data_user.connection.pymysql.connect')
    @patch('user.update_data_user.connection.get_secret')
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
