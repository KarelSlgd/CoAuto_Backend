import unittest
from unittest.mock import patch, MagicMock
import json
from cognito.forgot_password.app import lambda_handler, forgot_pass, headers_cors
from cognito.forgot_password.database import get_secret
from botocore.exceptions import ClientError
from botocore.stub import Stubber
import boto3


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

    @patch('cognito.forgot_password.app.get_secret')
    def test_confirm_password_code_delivery_failure_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'CodeDeliveryFailureException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Fallo en la entrega del código de verificación.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_forbidden_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'ForbiddenException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Solicitud no permitida por AWS WAF.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InternalErrorException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_invalid_email_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InvalidEmailRoleAccessPolicyException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Amazon Cognito no tiene permitido usar tu identidad de correo electrónico.',
                      json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_invalid_lambda_response_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InvalidLambdaResponseException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Respuesta inválida de AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InvalidParameterException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido proporcionado.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_invalid_sms_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InvalidSmsRoleAccessPolicyException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('El rol proporcionado para la configuración de SMS no tiene permiso para publicar usando Amazon SNS.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_invalid_sms_role_trust_relationship_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'InvalidSmsRoleTrustRelationshipException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('La relación de confianza no es válida para el rol proporcionado para la configuración de SMS.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_limit_exceeded_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'LimitExceededException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Se ha excedido el límite para el recurso solicitado.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'NotAuthorizedException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('No está autorizado para realizar esta acción.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_resource_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'ResourceNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Recurso no encontrado en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'TooManyRequestsException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Se han realizado demasiadas solicitudes para esta operación.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_unexpected_lambda_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'UnexpectedLambdaException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 502)
        self.assertIn('Excepción inesperada con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_user_lambda_validation_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'UserLambdaValidationException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción de validación del usuario con el servicio AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'UserNotFoundException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Usuario no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    def test_general_exception(self, mock_get_secret):
        email = 'test@example.com'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error('forgot_password', 'SomeOtherException')
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.forgot_password.app.boto3.client', return_value=client):
            response = forgot_pass(email, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Ocurrió un error al solicitar el cambio de contraseña.', json.loads(response['body'])['message'])

    @patch('cognito.forgot_password.app.get_secret')
    @patch('cognito.forgot_password.app.forgot_pass')
    @patch('cognito.forgot_password.app.handle_response')
    def test_lambda_handler_exception(self, mock_handle_response, mock_forgot_pass, mock_get_secret):
        # Configurar el mock para que forgot_pass lance una excepción
        error_message = 'Some error'
        mock_forgot_pass.side_effect = Exception(error_message)

        # Crear un evento de prueba
        event = {
            'body': json.dumps({'email': 'test@example.com'})
        }

        # Llamar a la función lambda_handler
        lambda_handler(event, None)

        # Verificar que handle_response fue llamado con los parámetros correctos
        args, kwargs = mock_handle_response.call_args
        exception_instance = args[0]
        self.assertIsInstance(exception_instance, Exception)
        self.assertEqual(str(exception_instance), error_message)
        self.assertEqual(args[1], 'Ocurrió un error al solicitar el cambio de contraseña.')
        self.assertEqual(args[2], 500)

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