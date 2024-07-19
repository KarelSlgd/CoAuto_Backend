import unittest
from unittest.mock import patch, MagicMock
import json
import boto3
from cognito.confirm_sign_up.app import lambda_handler, confirmation_registration, handle_response
from cognito.confirm_sign_up.database import get_secret
from botocore.stub import Stubber
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
    def test_lambda_handler_confirmation_error(self, mock_handle_response, mock_get_secret,
                                               mock_confirmation_registration):
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

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_alias_exists_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'AliasExistsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 409)
        self.assertIn('El alias ya existe.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_code_mismatch_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'CodeMismatchException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('El código proporcionado no coincide.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_expired_code_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'ExpiredCodeException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 410)
        self.assertIn('El código ha expirado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_forbidden_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'ForbiddenException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Solicitud no permitida por AWS WAF.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'InternalErrorException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno del servidor.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_invalid_lambda_response_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'InvalidLambdaResponseException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Respuesta inválida de AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'InvalidParameterException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_limit_exceeded_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'LimitExceededException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Límite excedido para el recurso solicitado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'NotAuthorizedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Usuario no autorizado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_resource_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'ResourceNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Recurso no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_too_many_failed_attempts_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'TooManyFailedAttemptsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiados intentos fallidos.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'TooManyRequestsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiadas solicitudes.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_unexpected_lambda_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'UnexpectedLambdaException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Excepción inesperada con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_user_lambda_validation_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'UserLambdaValidationException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción de validación de usuario con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'UserNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Usuario no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.confirm_sign_up.app.get_secret')
    def test_confirm_password_generic_exception(self, mock_get_secret):
        email = 'test@example.com'
        code = 'validcode'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('confirm_sign_up', 'ServiceError')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.confirm_sign_up.app.boto3.client', return_value=client):
            response = confirmation_registration(email, code, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error al confirmar el registro.', json.loads(response['body'])['message'])

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