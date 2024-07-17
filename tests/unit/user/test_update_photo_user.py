import unittest
from unittest.mock import patch, Mock, ANY, MagicMock
import json
import base64
from user.update_photo_user.app import lambda_handler, update_photo, get_jwt_claims, headers_cors
from user.update_photo_user.connection import get_connection, get_secret, handle_response
from botocore.exceptions import ClientError


class TestUpdatePhotoUser(unittest.TestCase):

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    def test_lambda_handler_missing_token(self, mock_handle_response, mock_get_jwt_claims, mock_get_connection):
        event = {
            'headers': {}
        }
        context = {}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'Falta token de autorización.', 401)

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_get_jwt_claims, mock_get_connection):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': 'invalid_json'
        }
        context = {}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(ANY, 'Cuerpo de la solicitud no válido.', 400)

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    def test_lambda_handler_missing_profile_image(self, mock_handle_response, mock_get_jwt_claims, mock_get_connection):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': json.dumps({})
        }
        context = {}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    def test_lambda_handler_image_too_large(self, mock_handle_response, mock_get_jwt_claims, mock_get_connection):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': json.dumps({'profile_image': 'a' * 251})
        }
        context = {}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'La imagen no debe exceder los 250 caracteres.', 400)

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    @patch('user.update_photo_user.app.update_photo')
    def test_lambda_handler_success(self, mock_update_photo, mock_handle_response, mock_get_jwt_claims,
                                    mock_get_connection):
        event = {
            'headers': {'Authorization': 'some_token'},
            'body': json.dumps({'profile_image': 'a' * 250})
        }
        context = {}

        mock_update_photo.return_value = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Usuario actualizado correctamente'
            })
        }

        response = lambda_handler(event, context)
        mock_update_photo.assert_called_once_with('a' * 250, 'some_token')
        self.assertEqual(response['statusCode'], 200)

    @patch('user.update_photo_user.app.get_connection')
    def test_update_photo_success(self, mock_get_connection):
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=False)

        mock_get_connection.return_value = mock_connection

        mock_cursor.execute.return_value = None
        mock_connection.commit.return_value = None

        token = 'some_valid_token'
        profile_image = 'image_data'
        id_user = 'test_user'

        with patch('user.update_photo_user.app.get_jwt_claims') as mock_get_jwt_claims:
            mock_get_jwt_claims.return_value = {'cognito:username': id_user}

            response = update_photo(profile_image, token)
            mock_cursor.execute.assert_called_once_with(
                "UPDATE user SET profile_image=%s WHERE id_cognito=%s",
                (profile_image, id_user)
            )
            self.assertEqual(response['statusCode'], 200)

    def test_get_jwt_claims_invalid_token(self):
        invalid_token = 'invalid.token'
        claims = get_jwt_claims(invalid_token)
        self.assertIsNone(claims)

    def test_get_jwt_claims_valid_token(self):
        valid_token = 'header.' + base64.b64encode(
            json.dumps({'cognito:username': 'test_user'}).encode()).decode() + '.signature'
        claims = get_jwt_claims(valid_token)
        self.assertEqual(claims, {'cognito:username': 'test_user'})

    @patch('user.update_photo_user.app.get_connection')
    @patch('user.update_photo_user.app.get_jwt_claims')
    @patch('user.update_photo_user.app.handle_response')
    def test_update_photo_db_error(self, mock_handle_response, mock_get_jwt_claims, mock_get_connection):
        mock_get_jwt_claims.return_value = {'cognito:username': 'test_user'}
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('DB error')
        mock_get_connection.return_value = mock_conn

        update_photo('valid_image', 'valid_token')
        mock_handle_response.assert_called_with(unittest.mock.ANY, 'Ocurrió un error al actualizar usuario.', 500)

    def test_get_jwt_claims_invalid_token_value_error(self):
        invalid_token = 'invalid.token.part'
        with patch('user.update_photo_user.app.base64.b64decode', side_effect=ValueError):
            claims = get_jwt_claims(invalid_token)
            self.assertIsNone(claims)

    def test_get_jwt_claims_invalid_token_exception(self):
        invalid_token = 'invalid_token'
        with patch('user.update_photo_user.app.base64.b64decode', side_effect=Exception('General error')):
            claims = get_jwt_claims(invalid_token)
            self.assertIsNone(claims)

    # Test for connection.py

    @patch('user.update_photo_user.connection.boto3.session.Session')
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

    @patch('user.update_photo_user.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('user.update_photo_user.connection.pymysql.connect')
    @patch('user.update_photo_user.connection.get_secret')
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

    @patch('user.update_photo_user.connection.pymysql.connect')
    @patch('user.update_photo_user.connection.get_secret')
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
