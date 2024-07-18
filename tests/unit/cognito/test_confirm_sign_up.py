import unittest
from unittest.mock import patch, MagicMock
import json
import boto3
from cognito.confirm_sign_up.app import lambda_handler, confirmation_registration
from botocore.exceptions import ClientError


class TestConfirmSignUp(unittest.TestCase):

    @patch('cognito.confirm_sign_up.app.get_secret')
    @patch('cognito.confirm_sign_up.app.calculate_secret_hash')
    @patch('cognito.confirm_sign_up.app.boto3.client')
    @patch('cognito.confirm_sign_up.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_boto_client, mock_calculate_secret_hash,
                                    mock_get_secret):
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'confirmation_code': '123456'
            })
        }
        context = {}

        mock_get_secret.return_value = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        mock_calculate_secret_hash.return_value = 'calculated_secret_hash'

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Registro confirmado correctamente.',
            })
        }

        result = lambda_handler(event, context)
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body'])['message'], 'Registro confirmado correctamente.')

    @patch('cognito.confirm_sign_up.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response):
        event = {
            'body': 'invalid json'
        }
        context = {}

        result = lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'Cuerpo de la solicitud inválido.', 400)

    @patch('cognito.confirm_sign_up.app.handle_response')
    def test_lambda_handler_missing_parameters(self, mock_handle_response):
        event = {
            'body': json.dumps({
                'email': 'test@example.com'
            })
        }
        context = {}

        result = lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros en la solicitud.', 400)

    @patch('cognito.confirm_sign_up.app.confirmation_registration')
    @patch('cognito.confirm_sign_up.app.get_secret')
    @patch('cognito.confirm_sign_up.app.handle_response')
    def test_lambda_handler_confirmation_error(self, mock_handle_response, mock_get_secret, mock_confirmation_registration):
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'confirmation_code': '123456'
            })
        }
        context = {}

        mock_get_secret.side_effect = Exception('Test Exception')

        lambda_handler(event, context)
        mock_handle_response.assert_called_once()
        args, kwargs = mock_handle_response.call_args
        self.assertIsInstance(args[0], Exception)
        self.assertEqual(args[1], 'Ocurrió un error al confirmar el registro.')
        self.assertEqual(args[2], 500)

    @patch('cognito.confirm_sign_up.app.calculate_secret_hash')
    @patch('cognito.confirm_sign_up.app.boto3.client')
    def test_confirmation_registration_success(self, mock_boto_client, mock_calculate_secret_hash):
        email = 'test@example.com'
        confirmation_code = '123456'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        mock_calculate_secret_hash.return_value = 'calculated_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        response = confirmation_registration(email, confirmation_code, secret)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Registro confirmado correctamente.')
