import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from cognito.change_password.app import lambda_handler, change, handle_response

headers_cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
}


class TestChangePassword(unittest.TestCase):
    @patch('cognito.change_password.app.change')
    @patch('cognito.change_password.app.handle_response')
    def test_valid_request(self, mock_handle_response, mock_change):
        event = {
            'body': json.dumps({
                'previous_password': 'old_password',
                'new_password': 'new_password',
                'access_token': 'valid_token'
            })
        }
        context = {}

        mock_change.return_value = {
            'statusCode': 200,
            'body': json.dumps({'message': 'Password changed successfully'})
        }

        response = lambda_handler(event, context)

        mock_change.assert_called_once_with('old_password', 'new_password', 'valid_token')

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Password changed successfully')

    @patch('cognito.change_password.app.boto3.client')
    def test_change_password_success(self, mock_boto3_client):
        # Mock the client response
        mock_client = MagicMock()
        mock_client.change_password.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        mock_boto3_client.return_value = mock_client

        previous_password = 'oldPassword'
        new_password = 'newPassword'
        token = 'validToken'

        response = change(previous_password, new_password, token)
        expected_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Contraseña cambiada correctamente.',
                'response': {"ResponseMetadata": {"HTTPStatusCode": 200}}
            })
        }

        self.assertEqual(response, expected_response)

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

    @patch('cognito.change_password.app.change')
    def test_lambda_handler_change_exception(self, mock_change):
        mock_change.side_effect = Exception('Unknown error')
        event = {
            'body': json.dumps({
                'previous_password': 'oldPassword',
                'new_password': 'newPassword',
                'access_token': 'validToken'
            })
        }
        context = {}
        response = lambda_handler(event, context)
        expected_response = handle_response(Exception('Unknown error'), 'Ocurrió un error al cambiar la contraseña.',
                                            500)

        self.assertEqual(response, expected_response)

    @patch('cognito.change_password.app.boto3.client')
    def test_change_success(self, mock_boto_client):
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        mock_client.change_password.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}

        response = change('old_password', 'new_password', 'valid_token')

        expected_response = {
            'statusCode': 200,
            'message': 'Contraseña cambiada correctamente.',
            'response': {'ResponseMetadata': {'HTTPStatusCode': 200}}
        }

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), expected_response)

    @patch('cognito.change_password.app.boto3.client')
    def test_cognito_exceptions(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        class MockForbiddenException(Exception): pass
        class MockInternalErrorException(Exception): pass
        class MockInvalidParameterException(Exception): pass
        class MockInvalidPasswordException(Exception): pass
        class MockLimitExceededException(Exception): pass
        class MockNotAuthorizedException(Exception): pass
        class MockPasswordResetRequiredException(Exception): pass
        class MockResourceNotFoundException(Exception): pass
        class MockTooManyRequestsException(Exception): pass
        class MockUserNotConfirmedException(Exception): pass
        class MockUserNotFoundException(Exception): pass
        class MockGenericException(Exception): pass

        mock_client.exceptions.ForbiddenException = MockForbiddenException
        mock_client.exceptions.InternalErrorException = MockInternalErrorException
        mock_client.exceptions.InvalidParameterException = MockInvalidParameterException
        mock_client.exceptions.InvalidPasswordException = MockInvalidPasswordException
        mock_client.exceptions.LimitExceededException = MockLimitExceededException
        mock_client.exceptions.NotAuthorizedException = MockNotAuthorizedException
        mock_client.exceptions.PasswordResetRequiredException = MockPasswordResetRequiredException
        mock_client.exceptions.ResourceNotFoundException = MockResourceNotFoundException
        mock_client.exceptions.TooManyRequestsException = MockTooManyRequestsException
        mock_client.exceptions.UserNotConfirmedException = MockUserNotConfirmedException
        mock_client.exceptions.UserNotFoundException = MockUserNotFoundException

        exceptions_and_responses = [
            (MockInternalErrorException, 'Amazon Cognito encontró un error interno.', 500),
            (MockInvalidParameterException, 'Amazon Cognito encontró un parámetro inválido.', 400),
            (MockInvalidPasswordException, 'Amazon Cognito encontró una contraseña inválida.', 400),
            (MockLimitExceededException, 'Se ha excedido el límite para un recurso solicitado de AWS.', 429),
            (MockNotAuthorizedException, 'No estás autorizado.', 401),
            (MockPasswordResetRequiredException, 'Se requiere un restablecimiento de contraseña.', 412),
            (MockResourceNotFoundException, 'Amazon Cognito no puede encontrar el recurso solicitado.', 404),
            (MockTooManyRequestsException, 'Has realizado demasiadas solicitudes para una operación dada.', 429),
            (MockUserNotConfirmedException, 'El usuario no fue confirmado exitosamente.', 412),
            (MockUserNotFoundException, 'El usuario no fue encontrado.', 404),
            (MockGenericException, 'Ocurrió un error al cambiar la contraseña.', 500)
        ]

        for exception, message, status_code in exceptions_and_responses:
            with self.subTest(exception=exception):
                mock_client.change_password.side_effect = exception("Error")
                response = change('old_pass', 'new_pass', 'token')
                response_body = json.loads(response['body'])
                self.assertEqual(response['statusCode'], status_code)
                self.assertIn(message, response_body['message'])

    @patch('cognito.change_password.app.boto3.client')
    def test_forbidden_exception(self, mock_boto_client):
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        class MockForbiddenException(Exception):
            pass

        mock_client.exceptions.ForbiddenException = MockForbiddenException
        mock_client.change_password.side_effect = MockForbiddenException("User is forbidden")

        response = change('old_pass', 'new_pass', 'token')
        self.assertEqual(response['statusCode'], 403)
        self.assertIn('AWS WAF no permite tu solicitud basado en un ACL web asociado a tu grupo de usuarios.',
                      response['body'])
