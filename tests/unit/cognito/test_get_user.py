import unittest
from unittest.mock import patch, MagicMock, ANY
import json
import base64
from cognito.get_user.app import lambda_handler, get_jwt_claims, get_into_user
from cognito.get_user.database import get_connection, close_connection, handle_response, get_secret, calculate_secret_hash
from botocore.exceptions import ClientError
import hmac
import hashlib


class TestGetUser(unittest.TestCase):

    @patch('cognito.get_user.app.get_jwt_claims')
    @patch('cognito.get_user.app.get_into_user')
    def test_lambda_handler_success(self, mock_get_into_user, mock_get_jwt_claims):
        event = {
            'headers': {
                'Authorization': 'Bearer token'
            }
        }
        context = {}

        decoded_token = {'cognito:username': 'user123'}
        user_info = {
            'id_user': 1,
            'id_cognito': 'user123',
            'email': 'user@example.com',
            'nameUser': 'User',
            'lastname': 'Test',
            'nameRole': 'Admin',
            'value': 'Active',
            'profile_image': 'image_url'
        }

        mock_get_jwt_claims.return_value = decoded_token
        mock_get_into_user.return_value = user_info

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {
            'tokenDecode': decoded_token,
            'userInfo': user_info
        })

    def test_lambda_handler_no_token(self):
        event = {'headers': {}}
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 401)
        self.assertEqual(json.loads(response['body']), {
            'statusCode': 401,
            'message': 'Se requiere un token de autorización.',
            'error': 'None'
        })

    @patch('cognito.get_user.app.get_jwt_claims', side_effect=Exception('Error decoding token'))
    def test_lambda_handler_exception(self, mock_get_jwt_claims):
        event = {
            'headers': {
                'Authorization': 'Bearer token'
            }
        }
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['message'],
                         'Ocurrió un error al obtener la información del usuario.')

    def test_get_jwt_claims_success(self):
        token = 'header.payload.signature'
        payload = {'sub': '1234567890', 'name': 'John Doe', 'iat': 1516239022}
        encoded_payload = base64.b64encode(json.dumps(payload).encode()).decode().strip("=")

        token = f'header.{encoded_payload}.signature'
        claims = get_jwt_claims(token)
        self.assertEqual(claims, payload)

    def test_get_jwt_claims_invalid_token(self):
        token = 'invalid.token'
        claims = get_jwt_claims(token)
        self.assertIsNone(claims)

    @patch('cognito.get_user.app.get_connection')
    @patch('cognito.get_user.app.close_connection')
    @patch('cognito.get_user.app.handle_response')
    def test_get_into_user_success(self, mock_handle_response, mock_close_connection, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        user_info = (
            1, 'user123', 'user@example.com', 'User', 'Test', 'Admin', 'Active', 'image_url'
        )
        mock_cursor.fetchone.return_value = user_info
        mock_cursor.description = [
            ('id_user',), ('id_cognito',), ('email',), ('nameUser',), ('lastname',), ('nameRole',), ('value',),
            ('profile_image',)
        ]

        result = get_into_user('user123')
        self.assertEqual(result, {
            'id_user': 1,
            'id_cognito': 'user123',
            'email': 'user@example.com',
            'nameUser': 'User',
            'lastname': 'Test',
            'nameRole': 'Admin',
            'value': 'Active',
            'profile_image': 'image_url'
        })

    @patch('cognito.get_user.app.get_connection')
    @patch('cognito.get_user.app.close_connection')
    @patch('cognito.get_user.app.handle_response')
    def test_get_into_user_exception(self, mock_handle_response, mock_close_connection, mock_get_connection):
        # Simulación de conexión y cursor de la base de datos
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simulación de excepción al ejecutar la consulta
        mock_cursor.execute.side_effect = Exception("Database error")

        token = "test_cognito_id"
        user_info = get_into_user(token)

        mock_handle_response.assert_called_once_with(ANY, 'Ocurrió un error al obtener la información del usuario.',
                                                     500)

    @patch('cognito.get_user.app.get_connection')
    @patch('cognito.get_user.app.close_connection')
    @patch('cognito.get_user.app.handle_response')
    def test_get_into_user_no_user(self, mock_handle_response, mock_close_connection, mock_get_connection):
        # Simulación de conexión y cursor de la base de datos
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simulación de resultado vacío
        mock_cursor.fetchone.return_value = None

        token = "non_existing_cognito_id"
        user_info = get_into_user(token)

        self.assertIsNone(user_info)

    def test_get_jwt_claims_value_error(self):
        # Token con carga útil que no es JSON
        token = "header.invalid_payload.signature"
        claims = get_jwt_claims(token)
        self.assertIsNone(claims)

    # Test connection to the database

    @patch('boto3.session.Session.client')
    def test_get_secret_success(self, mock_client):
        secret_name = "COAUTO"
        secret_value = {"key": "value"}

        mock_client_instance = MagicMock()
        mock_client_instance.get_secret_value.return_value = {
            'SecretString': json.dumps(secret_value)
        }
        mock_client.return_value = mock_client_instance

        result = get_secret()
        self.assertEqual(result, secret_value)

    @patch('boto3.session.Session.client')
    def test_get_secret_not_found(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException"}}, "GetSecretValue"
        )
        mock_client.return_value = mock_client_instance

        with self.assertRaises(ClientError):
            get_secret()

    @patch('boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = MagicMock()
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {"Error": {"Code": "DecryptionFailure"}}, "GetSecretValue"
        )
        mock_client.return_value = mock_client_instance

        with self.assertRaises(ClientError):
            get_secret()

    @patch('cognito.get_user.database.pymysql.connect')
    @patch('cognito.get_user.database.get_secret')
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

    @patch('cognito.get_user.database.pymysql.connect')
    @patch('cognito.get_user.database.get_secret')
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

    @patch('cognito.get_user.database.close_connection')
    def test_close_connection_successful(self, mock_close_connection):
        mock_connection = MagicMock()

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

    @patch('cognito.get_user.database.close_connection')
    def test_close_connection_none(self, mock_close_connection):
        close_connection(None)
        self.assertEqual(mock_close_connection.call_count, 0)

    def test_calculate_secret_hash(self):
        client_id = "test_client_id"
        secret_key = "test_secret_key"
        username = "test_username"

        message = username + client_id
        dig = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        expected_hash = base64.b64encode(dig).decode()

        result = calculate_secret_hash(client_id, secret_key, username)

        self.assertEqual(result, expected_hash)