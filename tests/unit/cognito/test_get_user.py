import unittest
from unittest.mock import patch, MagicMock, ANY
import json
import base64
from cognito.get_user.app import lambda_handler, get_jwt_claims, get_into_user
from cognito.get_user.database import get_connection, close_connection, handle_response


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
