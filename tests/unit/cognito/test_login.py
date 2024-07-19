import unittest
from unittest.mock import patch, MagicMock
import json
from cognito.login.app import lambda_handler, login_auth
from cognito.login.database import get_secret
import boto3
from botocore.stub import Stubber
from botocore.exceptions import ClientError


class TestLogin(unittest.TestCase):

    @patch('cognito.login.app.get_secret')
    @patch('cognito.login.app.json.loads')
    @patch('cognito.login.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_json_loads, mock_get_secret):
        mock_json_loads.side_effect = json.JSONDecodeError("Expecting value", "document", 0)
        event = {'body': 'invalid body'}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(mock_json_loads.side_effect, 'Cuerpo de la solicitud inválido.', 400)

    @patch('cognito.login.app.get_secret')
    @patch('cognito.login.app.json.loads')
    @patch('cognito.login.app.handle_response')
    def test_lambda_handler_missing_params(self, mock_handle_response, mock_json_loads, mock_get_secret):
        mock_json_loads.return_value = {}
        event = {'body': json.dumps({})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'Faltan parámetros en la solicitud.', 400)

    @patch('cognito.login.app.get_secret')
    @patch('cognito.login.app.login_auth')
    @patch('cognito.login.app.json.loads')
    @patch('cognito.login.app.handle_response')
    def test_lambda_handler_login_auth_exception(self, mock_handle_response, mock_json_loads, mock_login_auth,
                                                 mock_get_secret):
        mock_json_loads.return_value = {'email': 'test@example.com', 'password': 'password'}
        mock_get_secret.return_value = {'dummy': 'secret'}
        mock_login_auth.side_effect = Exception("Some error")
        event = {'body': json.dumps({'email': 'test@example.com', 'password': 'password'})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(mock_login_auth.side_effect, 'Ocurrió un error', 500)

    @patch('cognito.login.app.get_secret')
    @patch('cognito.login.app.calculate_secret_hash')
    @patch('boto3.client')
    def test_lambda_handler_success(self, mock_boto_client, mock_calculate_secret_hash, mock_get_secret):
        mock_get_secret.return_value = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id'
        }
        mock_calculate_secret_hash.return_value = 'test_secret_hash'
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': 'test_auth_result'
        }
        mock_client.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'test_group'}]
        }

        event = {
            'body': json.dumps({
                'email': 'test@example.com',
                'password': 'test_password'
            })
        }
        context = {}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['response'], 'test_auth_result')
        self.assertEqual(body['role'], 'test_group')

    @patch('cognito.login.app.get_secret')
    def test_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'UserNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Usuario no encontrado', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'NotAuthorizedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('No autorizado', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_user_not_confirmed_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'UserNotConfirmedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 412)
        self.assertIn('Usuario no confirmado', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_password_reset_required_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'PasswordResetRequiredException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 428)
        self.assertIn('Se requiere restablecimiento de contraseña', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'TooManyRequestsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiadas solicitudes', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'InvalidParameterException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'InternalErrorException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_client_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'initiate_auth',
            service_error_code='ResourceNotFoundException',
            service_message='Resource not found'
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Solicitud inválida', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_unknown_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('initiate_auth', 'UnknownException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error desconocido', json.loads(response['body'])['message'])

    @patch('cognito.login.app.get_secret')
    def test_generic_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'test_password'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        mock_get_secret.return_value = secret

        with patch('cognito.login.app.boto3.client', return_value=client):
            with patch('cognito.login.app.login_auth', side_effect=Exception('Error genérico')):
                response = login_auth(email, password, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Solicitud inválida', json.loads(response['body'])['message'])

    @patch('cognito.login.app.boto3.client')
    @patch('cognito.login.app.get_secret')
    @patch('cognito.login.app.calculate_secret_hash')
    @patch('cognito.login.app.handle_response')
    def test_login_auth_general_exception(self, mock_handle_response, mock_calculate_secret_hash, mock_get_secret,
                                          mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        class CustomClientError(Exception):
            def __init__(self, message):
                self.message = message
        mock_client.exceptions = MagicMock()
        mock_client.exceptions.NotAuthorizedException = CustomClientError
        mock_client.exceptions.UserNotConfirmedException = CustomClientError
        mock_client.exceptions.PasswordResetRequiredException = CustomClientError
        mock_client.exceptions.UserNotFoundException = CustomClientError
        mock_client.exceptions.TooManyRequestsException = CustomClientError
        mock_client.exceptions.InvalidParameterException = CustomClientError
        mock_client.exceptions.InternalErrorException = CustomClientError

        general_exception = Exception("General error")
        mock_client.initiate_auth.side_effect = general_exception

        mock_get_secret.return_value = {
            'COGNITO_CLIENT_ID': 'fake_client_id',
            'SECRET_KEY': 'fake_secret_key',
            'COGNITO_USER_POOL_ID': 'fake_user_pool_id'
        }
        mock_calculate_secret_hash.return_value = 'fake_secret_hash'

        email = 'test@example.com'
        password = 'password123'

        response = login_auth(email, password, mock_get_secret.return_value)

        mock_handle_response.assert_called()

        args, kwargs = mock_handle_response.call_args
        self.assertEqual(args[0].args[0], 'General error')
        self.assertEqual(args[1], 'Ocurrió un error')
        self.assertEqual(args[2], 500)

        self.assertEqual(response, mock_handle_response.return_value)

    # Test connection
    @patch('boto3.session.Session.client')
    def test_get_secret_success(self, mock_client):
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