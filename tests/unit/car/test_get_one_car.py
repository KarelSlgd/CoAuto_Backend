import unittest
from unittest.mock import patch, MagicMock
import json
from car.get_one_car.app import lambda_handler, headers_cors
from car.get_one_car.connection import get_connection, handle_response, close_connection, execute_query, get_secret
from botocore.exceptions import ClientError


class TestGetOneCar(unittest.TestCase):

    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    @patch('car.get_one_car.app.close_connection')
    def test_lambda_handler_no_id_auto(self, mock_close, mock_handle_response, mock_get_connection):
        event = {'queryStringParameters': None, 'body': json.dumps({})}
        context = {}

        mock_handle_response.return_value = {'statusCode': 400, 'body': json.dumps({'message': 'Falta un parametro.'})}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Falta un parametro.', response['body'])
        mock_handle_response.assert_called_once()
        mock_close.assert_not_called()
        mock_get_connection.assert_not_called()

    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    @patch('car.get_one_car.app.close_connection')
    def test_lambda_handler_with_id_auto(self, mock_close, mock_handle_response, mock_get_connection):
        event = {'queryStringParameters': {'id_auto': '123'}}
        context = {}

        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.side_effect = [
            [(1, 'Model X', 'Brand Y', 2020, 30000, 'SUV', 'Gasoline', 4, 'V6', 150, 200, 450, 'Description',
              'Available')],
            [('https://image1.com',), ('https://image2.com',)],
            [(5,), (4,), (3,)]
        ]

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Informacion del auto obtenida correctamente.')
        self.assertEqual(len(body['data']), 1)
        self.assertEqual(body['data'][0]['id_auto'], 1)
        self.assertEqual(body['data'][0]['model'], 'Model X')
        self.assertEqual(body['data'][0]['images'], ['https://image1.com', 'https://image2.com'])
        self.assertEqual(body['data'][0]['average_rating'], 4.0)

        mock_cursor.execute.assert_any_call(
            "SELECT url FROM auto_image WHERE id_auto = %s", (1,))
        mock_cursor.execute.assert_any_call(
            "SELECT value FROM rate WHERE id_auto = %s", (1,))

        mock_close.assert_called_once_with(mock_connection)

    @patch('car.get_one_car.app.get_connection')
    @patch('car.get_one_car.app.handle_response')
    @patch('car.get_one_car.app.close_connection')
    def test_lambda_handler_with_error(self, mock_close, mock_handle_response, mock_get_connection):
        event = {'queryStringParameters': {'id_auto': '123'}}
        context = {}

        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception('DB Error')
        mock_handle_response.return_value = {'statusCode': 500, 'body': json.dumps(
            {'message': 'Ocurrió un error al obtener la información del auto.'})}

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertIn('Ocurrió un error al obtener la información del auto.', body['message'])

        mock_handle_response.assert_called_once()
        args, kwargs = mock_handle_response.call_args
        self.assertIsInstance(args[0], Exception)
        self.assertEqual(str(args[0]), 'DB Error')
        self.assertEqual(args[1], 'Ocurrió un error al obtener la información del auto.')
        self.assertEqual(args[2], 500)

    # Test for connection.py

    @patch('car.get_one_car.connection.boto3.session.Session')
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

    @patch('car.get_one_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.get_one_car.connection.pymysql.connect')
    @patch('car.get_one_car.connection.get_secret')
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

    @patch('car.get_one_car.connection.pymysql.connect')
    @patch('car.get_one_car.connection.get_secret')
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

    @patch('car.get_one_car.connection.execute_query')
    def test_execute_query_successful(self, mock_execute_query):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [('row1',), ('row2',)]

        query = "SELECT * FROM test_table"

        result = execute_query(mock_connection, query)

        mock_cursor.execute.assert_called_once_with(query)
        mock_cursor.fetchall.assert_called_once()
        self.assertEqual(result, [('row1',), ('row2',)])

    @patch('car.get_one_car.connection.execute_query')
    def test_execute_query_exception(self, mock_execute_query):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Query execution error")

        query = "SELECT * FROM test_table"

        result = execute_query(mock_connection, query)

        mock_cursor.execute.assert_called_once_with(query)
        self.assertIsNone(result)

    @patch('car.get_one_car.connection.close_connection')
    def test_close_connection_successful(self, mock_close_connection):
        mock_connection = MagicMock()

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

    @patch('car.get_one_car.connection.close_connection')
    def test_close_connection_none(self, mock_close_connection):
        close_connection(None)
        self.assertEqual(mock_close_connection.call_count, 0)