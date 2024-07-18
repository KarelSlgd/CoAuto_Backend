import unittest
from unittest.mock import patch, MagicMock
import json
from cognito.forgot_password.app import lambda_handler, forgot_pass, get_secret, calculate_secret_hash, handle_response, headers_cors


class TestForgotPassword(unittest.TestCase):

    @patch('cognito.forgot_password.app.get_secret')
    @patch('cognito.forgot_password.app.forgot_pass')
    def test_lambda_handler_success(self, mock_forgot_pass, mock_get_secret):
        event = {
            'body': json.dumps({'email': 'test@example.com'})
        }
        context = {}

        mock_get_secret.return_value = {'COGNITO_CLIENT_ID': 'dummy_client_id', 'SECRET_KEY': 'dummy_secret_key'}
        mock_forgot_pass.return_value = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Solicitud de cambio de contraseña enviada correctamente.'
            })
        }

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Solicitud de cambio de contraseña enviada correctamente.',
                      json.loads(response['body'])['message'])

    def test_lambda_handler_invalid_body(self):
        event = {
            'body': 'invalid json'
        }
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Cuerpo de la solicitud inválido.', json.loads(response['body'])['message'])

    def test_lambda_handler_missing_email(self):
        event = {
            'body': json.dumps({})
        }
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Faltan parámetros en la solicitud.', json.loads(response['body'])['message'])


    @patch('cognito.forgot_password.app.boto3.client')
    @patch('cognito.forgot_password.app.calculate_secret_hash')
    def test_forgot_pass_success(self, mock_calculate_secret_hash, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        secret = {'COGNITO_CLIENT_ID': 'dummy_client_id', 'SECRET_KEY': 'dummy_secret_key'}
        email = 'test@example.com'
        mock_calculate_secret_hash.return_value = 'dummy_secret_hash'
        mock_client.forgot_password.return_value = {'CodeDeliveryDetails': {'Destination': 'email@example.com'}}

        response = forgot_pass(email, secret)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Solicitud de cambio de contraseña enviada correctamente.', json.loads(response['body'])['message'])

