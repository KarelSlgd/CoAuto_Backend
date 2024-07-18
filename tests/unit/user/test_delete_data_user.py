import unittest
from unittest.mock import patch, MagicMock, Mock
import json

from botocore.exceptions import ClientError
from user.delete_data_user.app import lambda_handler, get_username_by_id, get_status_value, update_user_status
from user.delete_data_user.connection import get_connection, get_secret, handle_response

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


class TestDeleteUser(unittest.TestCase):
    @patch('user.delete_data_user.app.get_connection')
    def test_get_username_by_id_success(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ['test@example.com']
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = get_username_by_id(1)

        self.assertEqual(result, 'test@example.com')
        mock_cursor.execute.assert_called_once_with("SELECT email FROM user WHERE id_user=%s", (1,))

    @patch('user.delete_data_user.app.get_connection')
    def test_get_username_by_id_failure(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception('DB error')
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        with self.assertRaises(Exception) as context:
            get_username_by_id(1)

        self.assertEqual(str(context.exception), 'DB error')

    @patch('user.delete_data_user.app.get_connection')
    def test_get_status_value_success(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = get_status_value(1)

        self.assertEqual(result, 1)
        mock_cursor.execute.assert_called_once_with(
            "SELECT value FROM status WHERE id_status=%s AND description='to_user'", (1,))

    @patch('user.delete_data_user.app.get_connection')
    def test_get_status_value_failure(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception('DB error')
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        with self.assertRaises(Exception) as context:
            get_status_value(1)

        self.assertEqual(str(context.exception), 'DB error')

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

    @patch('user.delete_data_user.app.get_status_value')
    def test_lambda_handler_invalid_status(self, mock_get_status_value):
        mock_get_status_value.return_value = None

        event = {
            'body': json.dumps({'id_user': '123', 'id_status': '456'})
        }

        context = {}
        response = lambda_handler(event, context)

        mock_get_status_value.assert_called_once_with('456')

        self.assertEqual(response['statusCode'], 400)
        response_body = json.loads(response['body'])
        self.assertIn('El status proporcionado no es válido.', response_body['message'])

    @patch('user.delete_data_user.app.get_connection')
    def test_get_status_value_valid(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = ('some_value',)

        result = get_status_value('456')

        self.assertEqual(result, 'some_value')

        mock_cursor.execute.assert_called_once_with(
            "SELECT value FROM status WHERE id_status=%s AND description='to_user'", ('456',)
        )

    @patch('user.delete_data_user.app.get_connection')
    def test_get_status_value_invalid(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        result = get_status_value('456')

        self.assertIsNone(result)

        mock_cursor.execute.assert_called_once_with(
            "SELECT value FROM status WHERE id_status=%s AND description='to_user'", ('456',)
        )

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

    @patch('user.delete_data_user.app.update_user_status')
    @patch('user.delete_data_user.app.get_status_value', return_value=1)
    @patch('user.delete_data_user.app.get_secret', return_value={'COGNITO_USER_POOL_ID': 'test_pool_id'})
    def test_lambda_handler_success(self, mock_get_secret, mock_get_status_value, mock_update_user_status):
        event = {
            'body': json.dumps({'id_user': 'test_user', 'id_status': 'test_status'})
        }
        context = {}

        mock_update_user_status.return_value = {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps({'statusCode': 200, 'message': 'Usuario actualizado correctamente.'})
        }

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Usuario actualizado correctamente.', response['body'])
        mock_update_user_status.assert_called_once_with('test_user', 'test_status', 1)

    @patch('user.delete_data_user.app.get_connection')
    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_secret')
    @patch('user.delete_data_user.app.boto3.client')
    def test_update_user_status_success(self, mock_boto_client, mock_get_secret, mock_get_username_by_id,
                                        mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        mock_get_username_by_id.return_value = 'test_username'
        mock_get_secret.return_value = {'COGNITO_USER_POOL_ID': 'test_pool_id'}
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        response = update_user_status('test_user', 'test_status', 1)

        mock_cursor.execute.assert_called_once_with("UPDATE user SET id_status=%s WHERE id_user=%s",
                                                    ('test_status', 'test_user'))
        mock_client.admin_enable_user.assert_called_once_with(UserPoolId='test_pool_id', Username='test_username')
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Usuario actualizado correctamente.', response['body'])

    @patch('user.delete_data_user.app.get_connection')
    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_secret')
    @patch('user.delete_data_user.app.boto3.client')
    def test_update_user_status_user_not_found(self, mock_boto_client, mock_get_secret, mock_get_username_by_id,
                                               mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection
        mock_get_username_by_id.return_value = None

        response = update_user_status('test_user', 'test_status', 1)
        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('No se encontró el usuario.', response_body['message'])
        mock_connection.close.assert_called_once()

    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_connection')
    @patch('boto3.client')
    @patch('user.delete_data_user.app.get_secret')
    def test_update_user_status_general_exception(self, mock_get_secret, mock_boto_client, mock_get_connection,
                                                  mock_get_username_by_id):
        mock_get_connection.return_value = MagicMock()
        mock_get_username_by_id.return_value = 'testuser'
        mock_boto_client.return_value.admin_disable_user.side_effect = Exception('General error')
        mock_get_secret.return_value = {'COGNITO_USER_POOL_ID': 'test_pool_id'}

        response = update_user_status(1, 2, 0)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error al actualizar el usuario', json.loads(response['body'])['message'])

    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_connection')
    @patch('boto3.client')
    @patch('user.delete_data_user.app.get_secret')
    def test_update_user_status_enable(self, mock_get_secret, mock_boto_client, mock_get_connection,
                                       mock_get_username_by_id):
        mock_get_connection.return_value = MagicMock()
        mock_get_username_by_id.return_value = 'testuser'
        mock_boto_client.return_value.admin_enable_user.return_value = None
        mock_get_secret.return_value = {'COGNITO_USER_POOL_ID': 'test_pool_id'}

        response = update_user_status(1, 2, 1)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Usuario actualizado correctamente.', response['body'])

    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_connection')
    @patch('boto3.client')
    @patch('user.delete_data_user.app.get_secret')
    def test_update_user_status_disable(self, mock_get_secret, mock_boto_client, mock_get_connection,
                                        mock_get_username_by_id):
        mock_get_connection.return_value = MagicMock()
        mock_get_username_by_id.return_value = 'testuser'
        mock_boto_client.return_value.admin_disable_user.return_value = None
        mock_get_secret.return_value = {'COGNITO_USER_POOL_ID': 'test_pool_id'}

        response = update_user_status(1, 2, 0)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Usuario actualizado correctamente.', response['body'])

    @patch('user.delete_data_user.app.get_connection')
    def test_get_username_by_id_found(self, mock_get_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ['test@example.com']
        mock_get_connection.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        username = get_username_by_id(1)

        self.assertEqual(username, 'test@example.com')

    @patch('user.delete_data_user.app.get_connection')
    def test_get_username_by_id_not_found(self, mock_get_connection):
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_get_connection.return_value.cursor.return_value.__enter__.return_value = mock_cursor

        username = get_username_by_id(1)

        self.assertIsNone(username)

    @patch('user.delete_data_user.app.get_username_by_id')
    @patch('user.delete_data_user.app.get_connection')
    @patch('boto3.client')
    @patch('user.delete_data_user.app.get_secret')
    def test_update_user_status_client_error(self, mock_get_secret, mock_boto_client, mock_get_connection,
                                             mock_get_username_by_id):
        mock_get_connection.return_value = MagicMock()
        mock_get_username_by_id.return_value = 'testuser'
        mock_boto_client.return_value.admin_disable_user.side_effect = ClientError(
            error_response={'Error': {'Code': '500', 'Message': 'Internal Server Error'}},
            operation_name='AdminDisableUser'
        )
        mock_get_secret.return_value = {'COGNITO_USER_POOL_ID': 'test_pool_id'}

        response = update_user_status(1, 2, 0)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error al actualizar el usuario', json.loads(response['body'])['message'])

    # Tests for connection.py
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
