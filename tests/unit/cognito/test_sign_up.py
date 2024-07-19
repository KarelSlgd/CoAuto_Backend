import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from cognito.sign_up.app import lambda_handler, register_user, insert_into_user
from cognito.sign_up.database import get_secret, get_connection, handle_response
from botocore.exceptions import ClientError
from botocore.stub import Stubber
import boto3


class TestSignUp(unittest.TestCase):
    @patch('cognito.sign_up.app.get_connection')
    @patch('cognito.sign_up.app.handle_response')
    def test_lambda_handler_missing_parameters(self, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'id_auto': 1})
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    @patch('cognito.sign_up.app.handle_response')
    def test_name_too_long(self, mock_handle_response):
        event = {'body': json.dumps({
            'password': 'password123',
            'email': 'test@example.com',
            'name': 'a' * 51,
            'lastname': 'Doe'
        })}
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El nombre no puede exceder los 50 caracteres.', 400)

    @patch('cognito.sign_up.app.handle_response')
    def test_lastname_too_long(self, mock_handle_response):
        event = {'body': json.dumps({
            'password': 'password123',
            'email': 'test@example.com',
            'name': 'John',
            'lastname': 'a' * 101
        })}
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El apellido no puede exceder los 100 caracteres.', 400)

    @patch('cognito.sign_up.app.get_secret')
    @patch('cognito.sign_up.app.register_user')
    @patch('cognito.sign_up.app.handle_response')
    def test_register_user_exception(self, mock_handle_response, mock_register_user, mock_get_secret):
        mock_get_secret.return_value = 'secret'
        mock_register_user.side_effect = Exception('Test Exception')

        event = {'body': json.dumps({
            'password': 'password123',
            'email': 'test@example.com',
            'name': 'John',
            'lastname': 'Doe'
        })}
        context = {}

        lambda_handler(event, context)

        args, kwargs = mock_handle_response.call_args
        self.assertIsInstance(args[0], Exception)
        self.assertEqual(args[0].args[0], 'Test Exception')
        self.assertEqual(args[1], 'Ocurrió un error al registrar el usuario.')
        self.assertEqual(args[2], 500)

    @patch('cognito.sign_up.app.get_secret')
    @patch('cognito.sign_up.app.register_user')
    @patch('cognito.sign_up.app.handle_response')
    def test_lambda_handler_valid_request(self, mock_handle_response, mock_register_user, mock_get_secret):
        mock_get_secret.return_value = {'COGNITO_CLIENT_ID': 'fake_id', 'SECRET_KEY': 'fake_key'}
        mock_register_user.return_value = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Se ha enviado un correo de confirmación.', 'response': 'fake_response'})
        }

        event = {
            'body': json.dumps({
                'password': 'ValidPass123!',
                'email': 'test@example.com',
                'name': 'John',
                'lastname': 'Doe'
            })
        }
        context = {}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)

    @patch('cognito.sign_up.app.handle_response')
    def test_lambda_handler_invalid_request(self, mock_handle_response):
        event = {'body': '{invalid_json'}
        context = {}

        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'Cuerpo de la solicitud inválido.', 400)

    @patch('cognito.sign_up.app.get_connection')
    @patch('cognito.sign_up.app.handle_response')
    def test_insert_into_user_success(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        insert_into_user('test@example.com', 'fake_sub', 'John', 'Doe')

        mock_cursor.execute.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('cognito.sign_up.app.get_connection')
    @patch('cognito.sign_up.app.handle_response', return_value=None)
    def test_insert_into_user_exception(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        mock_cursor.execute.side_effect = Exception("Database error")

        email = 'test@example.com'
        id_cognito = 'test_cognito_id'
        name = 'Test'
        lastname = 'User'

        response = insert_into_user(email, id_cognito, name, lastname)

        mock_handle_response.assert_called_with(
            mock_cursor.execute.side_effect,
            'Ocurrió un error al registrar el usuario.',
            500
        )

        mock_connection.close.assert_called_once()
        self.assertIsNone(response)

    @patch('cognito.sign_up.app.boto3.client')
    @patch('cognito.sign_up.app.calculate_secret_hash')
    @patch('cognito.sign_up.app.get_secret')
    @patch('cognito.sign_up.app.insert_into_user')
    @patch('cognito.sign_up.app.get_connection')
    def test_register_user_success(self, mock_get_connection, mock_insert_into_user, mock_get_secret, mock_calculate_secret_hash, mock_boto_client):
        # Mocking the secret
        mock_get_secret.return_value = {
            'COGNITO_CLIENT_ID': 'fake_client_id',
            'SECRET_KEY': 'fake_secret_key',
            'COGNITO_USER_POOL_ID': 'fake_user_pool_id',
            'COGNITO_GROUP_NAME': 'fake_group_name'
        }

        # Mocking the secret hash calculation
        mock_calculate_secret_hash.return_value = 'fake_secret_hash'

        # Mocking the boto3 client and its response
        mock_client_instance = MagicMock()
        mock_client_instance.sign_up.return_value = {'UserSub': 'fake_user_sub'}
        mock_boto_client.return_value = mock_client_instance

        response = register_user('test@example.com', 'Password123!', 'Test', 'User', mock_get_secret.return_value)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('Se ha enviado un correo de confirmación.', body['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_code_delivery_failure_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='CodeDeliveryFailureException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Error en la entrega del código de verificación.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_forbidden_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='ForbiddenException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Solicitud no permitida por AWS WAF.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_internal_error_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InternalErrorException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Error interno en Amazon Cognito.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_email_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidEmailRoleAccessPolicyException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('No se permite usar la identidad de correo electrónico.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_lambda_response_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidLambdaResponseException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Respuesta inválida de AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_parameter_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidParameterException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parámetro inválido en la solicitud.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_password_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidPasswordException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Contraseña inválida.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_sms_role_access_policy_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidSmsRoleAccessPolicyException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('El rol de SMS no tiene permiso para publicar usando Amazon SNS.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_invalid_sms_role_trust_relationship_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='InvalidSmsRoleTrustRelationshipException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Relación de confianza no válida para el rol de SMS.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_limit_exceeded_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='LimitExceededException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Se ha excedido el límite para el recurso solicitado.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_not_authorized_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='NotAuthorizedException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Usuario no autorizado.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_resource_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='ResourceNotFoundException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 404)
        self.assertIn('Recurso no encontrado.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_too_many_requests_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='TooManyRequestsException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 429)
        self.assertIn('Demasiadas solicitudes para la operación.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_unexpected_lambda_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='UnexpectedLambdaException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Excepción inesperada con AWS Lambda.', json.loads(response['body'])['message'])


    @patch('cognito.sign_up.app.get_secret')
    def test_user_not_found_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='CodeDeliveryFailureException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Error en la entrega del código de verificación.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_user_lambda_validation_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='UserLambdaValidationException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Excepción de validación del usuario con AWS Lambda.', json.loads(response['body'])['message'])

    @patch('cognito.sign_up.app.get_secret')
    def test_username_exists_exception(self, mock_get_secret):
        email = 'test@example.com'
        password = 'Password123!'
        name = 'Test'
        lastname = 'User'
        secret = {
            'COGNITO_CLIENT_ID': 'test_client_id',
            'COGNITO_USER_POOL_ID': 'test_user_pool_id',
            'SECRET_KEY': 'test_secret_key'
        }

        client = boto3.client('cognito-idp')
        stubber = Stubber(client)
        stubber.add_client_error(
            'sign_up',
            service_error_code='UsernameExistsException',
        )
        stubber.activate()

        mock_get_secret.return_value = secret

        with patch('cognito.sign_up.app.boto3.client', return_value=client):
            response = register_user(email, password, name, lastname, secret)

        self.assertEqual(response['statusCode'], 409)
        self.assertIn('El nombre de usuario ya existe en el grupo de usuarios.', json.loads(response['body'])['message'])

    # Test connection to the database
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

    @patch('cognito.sign_up.database.pymysql.connect')
    @patch('cognito.sign_up.database.get_secret')
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

    @patch('cognito.sign_up.database.get_secret')
    @patch('cognito.sign_up.database.handle_response')
    @patch('cognito.sign_up.database.pymysql.connect')
    def test_get_connection_failure(self, mock_connect, mock_handle_response, mock_get_secret):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }

        mock_connect.side_effect = Exception('Connection error')

        mock_handle_response.return_value = 'mock_error_response'

        result = get_connection()

        mock_get_secret.assert_called_once()
        mock_connect.assert_called_once_with(
            host='test_host',
            user='test_user',
            password='test_password',
            database='test_db'
        )

        called_args = mock_handle_response.call_args[0]
        self.assertEqual(len(called_args), 3)
        self.assertIsInstance(called_args[0], Exception)
        self.assertEqual(str(called_args[0]), 'Connection error')
        self.assertEqual(called_args[1], 'Ocurrió un error al conectar a la base de datos')
        self.assertEqual(called_args[2], 500)
        self.assertEqual(result, 'mock_error_response')

