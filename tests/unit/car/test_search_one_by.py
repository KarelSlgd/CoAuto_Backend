import unittest
from unittest.mock import patch
import json
from car.search_one_by.app import lambda_handler, handle_response
from botocore.exceptions import ClientError
from car.search_one_by.connection import headers_cors, get_secret, execute_query, close_connection, get_connection


class TestSearchOneBy(unittest.TestCase):

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.close_connection')
    def test_lambda_handler_success(self, mock_close_connection, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'type': 'modelo', 'value': 'Civic'})
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.side_effect = [
            [(1, 'Civic', 'Honda', 2020, 20000, 'Sedan', 'Gasolina', 4, '2.0L', 1400, 2000, 4500, 'Buen auto',
              'Disponible')],
            [('http://image1.com',), ('http://image2.com',)]
        ]

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Información del auto obtenida correctamente.')
        self.assertTrue(len(body['data']) > 0)
        self.assertTrue('images' in body['data'][0])
        mock_close_connection.assert_called_once_with(mock_connection)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.close_connection')
    def test_lambda_handler_missing_parameters(self, mock_close_connection, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'type': 'modelo'})
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.close_connection')
    def test_lambda_handler_invalid_attribute_type(self, mock_close_connection, mock_handle_response,
                                                   mock_get_connection):
        event = {
            'body': json.dumps({'type': 'color', 'value': 'rojo'})
        }
        context = {}

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Tipo de atributo no válido.', 400)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.close_connection')
    def test_lambda_handler_exception(self, mock_close_connection, mock_handle_response, mock_get_connection):
        event = {
            'body': json.dumps({'type': 'modelo', 'value': 'Civic'})
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception('Database error')

        response = lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(unittest.mock.ANY,
                                                     'Ocurrió un error al obtener la información del auto.', 500)
        mock_close_connection.assert_called_once_with(mock_connection)

    @patch('car.search_one_by.app.get_connection')
    @patch('car.search_one_by.app.handle_response')
    @patch('car.search_one_by.app.close_connection')
    def test_lambda_handler_query_string_parameters(self, mock_close_connection, mock_handle_response,
                                                    mock_get_connection):
        event = {
            'queryStringParameters': {'type': 'modelo', 'value': 'Civic'}
        }
        context = {}

        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.side_effect = [
            [(1, 'Civic', 'Honda', 2020, 20000, 'Sedan', 'Gasolina', 4, '2.0L', 1400, 2000, 4500, 'Buen auto',
              'Disponible')],
            [('http://image1.com',), ('http://image2.com',)]
        ]

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Información del auto obtenida correctamente.')
        self.assertTrue(len(body['data']) > 0)
        self.assertTrue('images' in body['data'][0])
        mock_close_connection.assert_called_once_with(mock_connection)

    # Test connection.py

    @patch('car.search_one_by.connection.boto3.session.Session')
    def test_get_secret(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
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

    @patch('car.search_one_by.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = mock_session.return_value.client.return_value
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.search_one_by.connection.pymysql.connect')
    @patch('car.search_one_by.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'localhost',
            'USERNAME': 'user',
            'PASSWORD': 'pass',
            'DB_NAME': 'database'
        }
        connection = mock_connect.return_value

        result = get_connection()

        self.assertEqual(result, connection)
        mock_connect.assert_called_with(
            host='localhost',
            user='user',
            password='pass',
            database='database'
        )

    @patch('car.search_one_by.connection.pymysql.connect')
    @patch('car.search_one_by.connection.get_secret')
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

    @patch('car.search_one_by.connection.pymysql.connect')
    def test_execute_query_success(self, mock_connect):
        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [('row1', 'row2')]

        query = "SELECT * FROM table"
        result = execute_query(mock_connection, query)

        self.assertEqual(result, [('row1', 'row2')])
        mock_cursor.execute.assert_called_with(query)

    @patch('car.search_one_by.connection.pymysql.connect')
    def test_execute_query_failure(self, mock_connect):
        mock_connection = mock_connect.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("Query execution error")

        query = "SELECT * FROM table"
        result = execute_query(mock_connection, query)

        self.assertIsNone(result)

    @patch('car.search_one_by.connection.pymysql.connect')
    def test_close_connection(self, mock_connect):
        mock_connection = mock_connect.return_value

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

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