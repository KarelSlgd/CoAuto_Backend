import unittest
from unittest.mock import patch, MagicMock
import json
from rate.delete_data_rate.app import lambda_handler, update_rate_status
from rate.delete_data_rate.connection import get_connection, handle_response, headers_cors, get_secret
from botocore.exceptions import ClientError


class TestLambdaHandler(unittest.TestCase):

    @patch('rate.delete_data_rate.app.get_connection')
    @patch('rate.delete_data_rate.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_get_connection):
        event = {'body': 'invalid json'}
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(
            unittest.mock.ANY, 'Cuerpo de la petición inválido.', 400
        )
        self.assertEqual(response, mock_handle_response.return_value)

    @patch('rate.delete_data_rate.app.get_connection')
    @patch('rate.delete_data_rate.app.handle_response')
    def test_lambda_handler_missing_parameters(self, mock_handle_response, mock_get_connection):
        event = {'body': json.dumps({'id_rate': 1})}
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(
            None, 'Faltan parámetros.', 400
        )
        self.assertEqual(response, mock_handle_response.return_value)

    @patch('rate.delete_data_rate.app.update_rate_status')
    def test_lambda_handler_success(self, mock_update_rate_status):
        event = {'body': json.dumps({'id_rate': 1, 'id_status': 2})}
        context = {}

        mock_update_rate_status.return_value = {
            'statusCode': 200,
            'headers': {},
            'body': json.dumps({'statusCode': 200, 'message': 'Reseña actualizada correctamente.'})
        }

        response = lambda_handler(event, context)

        mock_update_rate_status.assert_called_once_with(1, 2)
        self.assertEqual(response, mock_update_rate_status.return_value)

    @patch('rate.delete_data_rate.app.get_connection')
    @patch('rate.delete_data_rate.app.handle_response')
    def test_update_rate_status_invalid_status(self, mock_handle_response, mock_get_connection):
        # Simula la respuesta de la base de datos para un status no válido
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        response = update_rate_status(1, 2)

        cursor.execute.assert_any_call("SELECT * FROM status WHERE id_status=%s AND description='to_rate'", (2,))
        mock_handle_response.assert_called_once_with(None, 'El status no es válido para las reseñas.', 400)
        self.assertEqual(response, mock_handle_response.return_value)

    @patch('rate.delete_data_rate.app.get_connection')
    @patch('rate.delete_data_rate.app.handle_response')
    def test_update_rate_status_success(self, mock_handle_response, mock_get_connection):
        # Simula la respuesta de la base de datos para una actualización exitosa
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {'id_status': 2}

        response = update_rate_status(1, 2)

        cursor.execute.assert_any_call("SELECT * FROM status WHERE id_status=%s AND description='to_rate'", (2,))
        cursor.execute.assert_any_call("UPDATE rate SET id_status=%s WHERE id_rate=%s", (2, 1))
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

        expected_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': '*',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET,PUT,DELETE'
            },
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Reseña actualizada correctamente.'
            }),
        }
        self.assertEqual(response, expected_response)

    @patch('rate.delete_data_rate.app.get_connection')
    @patch('rate.delete_data_rate.app.handle_response')
    def test_update_rate_status_exception(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        cursor = mock_connection.cursor.return_value.__enter__.return_value
        cursor.execute.side_effect = Exception('Database error')

        response = update_rate_status(1, 2)

        mock_handle_response.assert_called_once_with(
            unittest.mock.ANY, 'Error al actualizar las reseñas.', 500
        )
        self.assertEqual(response, mock_handle_response.return_value)
        mock_connection.close.assert_called_once()

    # Test for connection.py

    @patch('rate.delete_data_rate.connection.boto3.session.Session')
    def test_get_secret(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'localhost',
                'USERNAME': 'user',
                'PASSWORD': 'pass',
                'DB_NAME': 'database'
            })
        }

        secret = get_secret()

        self.assertEqual(secret['HOST'], 'localhost')
        self.assertEqual(secret['USERNAME'], 'user')
        self.assertEqual(secret['PASSWORD'], 'pass')
        self.assertEqual(secret['DB_NAME'], 'database')
        mock_client.get_secret_value.assert_called_with(SecretId='COAUTO')

    @patch('rate.delete_data_rate.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('rate.delete_data_rate.connection.pymysql.connect')
    @patch('rate.delete_data_rate.connection.get_secret')
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

    @patch('rate.delete_data_rate.connection.pymysql.connect')
    @patch('rate.delete_data_rate.connection.get_secret')
    def test_get_connection_error(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        mock_connect.side_effect = Exception('Connection error')

        with self.assertRaises(Exception) as context:
            get_connection()

        self.assertTrue('Connection error' in str(context.exception))

    def test_handle_response(self):
        error = Exception('Test Error')
        message = 'Test Message'
        status_code = 400

        response = handle_response(error, message, status_code)

        expected_response = {
            'statusCode': status_code,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': status_code,
                'message': message,
                'error': str(error)
            })
        }

        self.assertEqual(response, expected_response)
