import unittest
from unittest.mock import patch, Mock, MagicMock
from cognito.confirm_forgot_password.app import lambda_handler, confirm_password
from cognito.confirm_forgot_password.database import get_secret, calculate_secret_hash, handle_response
from botocore.exceptions import ClientError
import hmac
import hashlib
import base64
import json
import boto3
from botocore.stub import Stubber


class TestConfirmForgotPassword(unittest.TestCase):
    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_generic_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'ServiceError')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error al confirmar la contraseña.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'UserNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Usuario no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_user_not_confirmed_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'UserNotConfirmedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Usuario no confirmado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_user_lambda_validation_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'UserLambdaValidationException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción de validación de usuario con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_unexpected_lambda_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'UnexpectedLambdaException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Excepción inesperada con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'TooManyRequestsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiadas solicitudes.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_too_many_failed_attempts_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'TooManyFailedAttemptsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiados intentos fallidos.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_resource_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'ResourceNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Recurso no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'NotAuthorizedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('No autorizado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_limit_exceeded_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'LimitExceededException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Se excedió el límite para el recurso solicitado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_invalid_password_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'InvalidPasswordException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Contraseña inválida.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'InvalidParameterException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_invalid_lambda_response_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'InvalidLambdaResponseException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Respuesta inválida de AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'InternalErrorException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_expired_code(self, mock_get_secret):
        email = 'test@example.com'
        code = 'expiredcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'ExpiredCodeException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El código ha expirado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    def test_confirm_password_forbidden_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        password = 'newpassword'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_forgot_password', 'ForbiddenException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_forgot_password.app.boto3.client', return_value=client):
            response = confirm_password(email, code, password, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Solicitud no permitida por AWS WAF.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.get_secret')
    @patch('cognito.confirm_forgot_password.app.calculate_secret_hash')
    @patch('boto3.client')
    def test_confirm_password_success(self, mock_boto_client, mock_calculate_secret_hash, mock_get_secret):
        # Mocks
        mock_client_instance = Mock()
        mock_boto_client.return_value = mock_client_instance
        mock_calculate_secret_hash.return_value = 'mock_secret_hash'
        mock_get_secret.return_value = {'COGNITO_CLIENT_ID': 'mock_client_id', 'SECRET_KEY': 'mock_secret_key'}
        mock_client_instance.confirm_forgot_password.return_value = 'mock_response'

        response = confirm_password('test@example.com', '123456', 'new_password', mock_get_secret.return_value)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Contraseña confirmada correctamente.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.confirm_password')
    @patch('cognito.confirm_forgot_password.app.get_secret')
    @patch('cognito.confirm_forgot_password.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_secret, mock_confirm_password):
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'code': '123456',
                'password': 'new_password'
            })
        }
        context = {}
        mock_get_secret.return_value = {'COGNITO_CLIENT_ID': 'mock_client_id', 'SECRET_KEY': 'mock_secret_key'}
        mock_confirm_password.return_value = {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps({
                'message': 'Contraseña confirmada correctamente.'
            })
        }

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Contraseña confirmada correctamente.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_forgot_password.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response):
        event = {
            'body': 'invalid_json'
        }
        context = {}

        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'Cuerpo de la solicitud inválido.', 400)

    def test_invalid_json_body(self):
        event = {
            'body': 'invalid json'
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['message'], 'Cuerpo de la solicitud inválido.')

    def test_missing_parameters(self):
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'new_password'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(json.loads(response['body'])['message'], 'Faltan parámetros en la solicitud.')

    @patch('cognito.confirm_forgot_password.app.get_secret', side_effect=Exception('Error getting secret'))
    def test_exception_in_get_secret(self, mock_get_secret):
        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'code': '123456',
                'password': 'new_password'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(json.loads(response['body'])['message'], 'Ocurrió un error al confirmar la contraseña.')

    @patch('cognito.confirm_forgot_password.app.boto3.client')
    def test_code_mismatch_exception(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        class MockCodeMismatchException(Exception):
            pass

        mock_client.exceptions.CodeMismatchException = MockCodeMismatchException
        mock_client.confirm_forgot_password.side_effect = MockCodeMismatchException(
            "El código proporcionado no coincide")

        response = confirm_password('email', 'code', 'password',
                                    {'COGNITO_CLIENT_ID': 'client_id', 'SECRET_KEY': 'secret_key'})

        self.assertEqual(response['statusCode'], 400)

        body = json.loads(response['body'])

        self.assertIn('El código proporcionado no coincide.', body['message'])

    # Test connection

    @patch('cognito.confirm_forgot_password.app.boto3.session.Session.client')
    def test_get_secret(self, mock_client):
        mock_secret_value_response = {
            'SecretString': json.dumps({"key": "value"})
        }
        mock_client.return_value.get_secret_value.return_value = mock_secret_value_response

        result = get_secret()

        self.assertEqual(result, {"key": "value"})
        mock_client.return_value.get_secret_value.assert_called_once_with(SecretId="COAUTO")

    def test_calculate_secret_hash(self):
        client_id = "test_client_id"
        secret_key = "test_secret_key"
        username = "test_username"

        message = username + client_id
        dig = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        expected_hash = base64.b64encode(dig).decode()

        result = calculate_secret_hash(client_id, secret_key, username)

        self.assertEqual(result, expected_hash)

    def test_handle_response(self):
        error = "Test error"
        message = "Test message"
        status_code = 400

        expected_response = {
            'statusCode': status_code,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': status_code,
                'message': message,
                'error': str(error)
            })
        }

        result = handle_response(error, message, status_code)

        self.assertEqual(result, expected_response)

    @patch('cognito.confirm_forgot_password.app.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client.return_value.get_secret_value.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            operation_name='GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()
