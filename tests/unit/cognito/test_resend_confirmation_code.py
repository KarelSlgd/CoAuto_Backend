import unittest
from unittest.mock import patch, MagicMock
import json
from cognito.resend_confirmation_code.app import lambda_handler, resend_code, get_secret, handle_response, headers_cors
from botocore.stub import Stubber
import boto3
from botocore.exceptions import ClientError


class TestResendConfirmationCode(unittest.TestCase):
    def test_lambda_handler_invalid_body(self):
        event = {
            'body': 'invalid json'
        }
        context = {}
        response = lambda_handler(event, context)
        expected_response = handle_response(None, 'Cuerpo de la solicitud inválido.', 400)

        self.assertEqual(response, expected_response)

    def test_lambda_handler_missing_parameters(self):
        event = {
            'body': json.dumps({
                'previous_password': 'oldPassword'
            })
        }
        context = {}
        response = lambda_handler(event, context)
        expected_response = handle_response(None, 'Faltan parámetros en la solicitud.', 400)

        self.assertEqual(response, expected_response)

    @patch('cognito.resend_confirmation_code.app.get_secret')
    @patch('cognito.resend_confirmation_code.app.resend_code')
    def test_lambda_handler_exception(self, mock_resend_code, mock_get_secret):
        # Configura el mock para que lance una excepción
        mock_get_secret.side_effect = Exception("Test Exception")

        # Define un evento de ejemplo con un cuerpo válido
        event = {
            'body': json.dumps({'email': 'test@example.com'})
        }

        context = {}

        # Ejecuta la función lambda_handler
        response = lambda_handler(event, context)

        # Verifica que la respuesta sea la esperada
        expected_response = handle_response(Exception("Test Exception"),
                                            'Ocurrió un error al solicitar el reenvío del código de confirmación.', 500)
        self.assertEqual(response, expected_response)

    @patch('cognito.resend_confirmation_code.app.get_secret')
    @patch('cognito.resend_confirmation_code.app.resend_code')
    @patch('json.loads')
    def test_lambda_handler_success(self, mock_json_loads, mock_resend_code, mock_get_secret):
        event = {
            'body': json.dumps({'email': 'test@example.com'})
        }
        context = {}
        mock_json_loads.return_value = {'email': 'test@example.com'}
        mock_get_secret.return_value = {'COGNITO_CLIENT_ID': 'dummy_client_id', 'SECRET_KEY': 'dummy_secret_key'}
        mock_resend_code.return_value = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Código de confirmación reenviado correctamente.'
            })
        }

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)

    @patch('cognito.resend_confirmation_code.app.boto3.client')
    @patch('cognito.resend_confirmation_code.app.calculate_secret_hash')
    def test_resend_code_success(self, mock_calculate_secret_hash, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_calculate_secret_hash.return_value = 'dummy_secret_hash'
        secret = {'COGNITO_CLIENT_ID': 'dummy_client_id', 'SECRET_KEY': 'dummy_secret_key'}
        email = 'test@example.com'

        response = resend_code(email, secret)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Código de confirmación reenviado correctamente', response_body['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_client_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='CodeDeliveryFailureException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Error al enviar el código de verificación.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_forbidden_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='ForbiddenException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Solicitud no permitida por AWS WAF.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InternalErrorException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_invalid_email_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InvalidEmailRoleAccessPolicyException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Amazon Cognito no tiene permiso para usar su identidad de correo electrónico.',
                      json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_invalid_lambda_response_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InvalidLambdaResponseException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Respuesta inválida de AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InvalidParameterException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido en la solicitud.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_invalid_sms_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InvalidSmsRoleAccessPolicyException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Rol no tiene permiso para publicar usando Amazon SNS.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_invalid_sms_role_trust_relationship_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='InvalidSmsRoleTrustRelationshipException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Relación de confianza inválida para el rol proporcionado para la configuración de SMS.',
                      json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_limit_exceeded_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='LimitExceededException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Límite de recursos de AWS excedido.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='NotAuthorizedException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Usuario no autorizado.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_resource_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='ResourceNotFoundException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Recurso no encontrado en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='TooManyRequestsException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiadas solicitudes en un período corto.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_unexpected_lambda_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='UnexpectedLambdaException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción inesperada con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_user_lambda_validation_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='UserLambdaValidationException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción de validación de usuario con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.resend_confirmation_code.app.get_secret')
    def test_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'resend_confirmation_code',
            service_error_code='UserNotFoundException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.resend_confirmation_code.app.boto3.client', return_value=client):
            response = resend_code(email, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Usuario no encontrado.', json.loads(response['body'])['message'])

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
