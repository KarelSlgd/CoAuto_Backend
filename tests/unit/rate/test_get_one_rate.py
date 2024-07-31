import unittest
from unittest.mock import patch, MagicMock
import json
from rate.get_one_data_rate.app import lambda_handler, get_connection, handle_response
from rate.get_one_data_rate.database import headers_cors, get_secret, execute_query, close_connection
from botocore.exceptions import ClientError


class TestGetOneRate(unittest.TestCase):

    @patch('rate.get_one_data_rate.app.get_connection')
    @patch('rate.get_one_data_rate.app.close_connection')
    @patch('rate.get_one_data_rate.app.execute_query')
    @patch('rate.get_one_data_rate.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_execute_query, mock_close_connection,
                                    mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_execute_query.return_value = [
            (1, 5, 'Great car!', 'Model X', 'Brand Y', 'John', 'Doe',"20213tn076@utez.edu.mx", 1, 'Active')
        ]

        event = {
            'queryStringParameters': {
                'id_auto': '1'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body['statusCode'], 200)
        self.assertEqual(response_body['message'], 'Reseñas obtenidas correctamente.')
        self.assertEqual(len(response_body['data']), 1)
        self.assertEqual(response_body['data'][0]['id_rate'], 1)

    @patch('rate.get_one_data_rate.app.get_connection')
    @patch('rate.get_one_data_rate.app.close_connection')
    @patch('rate.get_one_data_rate.app.execute_query')
    @patch('rate.get_one_data_rate.app.handle_response')
    def test_lambda_handler_no_id_auto(self, mock_handle_response, mock_execute_query, mock_close_connection,
                                       mock_get_connection):
        mock_handle_response.side_effect = lambda e, msg, code: {
            'statusCode': code,
            'headers': headers_cors,
            'body': json.dumps({'message': msg})
        }

        event = {
            'queryStringParameters': {}
        }
        context = {}

        response = lambda_handler(event, context)

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body['message'], 'Faltan parámetros.')

    @patch('rate.get_one_data_rate.app.get_connection')
    @patch('rate.get_one_data_rate.app.close_connection')
    @patch('rate.get_one_data_rate.app.execute_query')
    @patch('rate.get_one_data_rate.app.handle_response')
    def test_lambda_handler_exception(self, mock_handle_response, mock_execute_query, mock_close_connection,
                                      mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_execute_query.side_effect = Exception('Database error')

        mock_handle_response.side_effect = lambda e, msg, code: {
            'statusCode': code,
            'headers': headers_cors,
            'body': json.dumps({'message': msg})
        }

        event = {
            'queryStringParameters': {
                'id_auto': '1'
            }
        }
        context = {}

        response = lambda_handler(event, context)

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response_body['message'], 'Ocurrió un error al obtener la reseña.')

    @patch('rate.get_one_data_rate.app.get_connection')
    @patch('rate.get_one_data_rate.app.close_connection')
    @patch('rate.get_one_data_rate.app.execute_query')
    @patch('rate.get_one_data_rate.app.handle_response')
    def test_lambda_handler_body(self, mock_handle_response, mock_execute_query, mock_close_connection,
                                 mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_execute_query.return_value = [
            (1, 5, 'Great car!', 'Model X', 'Brand Y', 'John', 'Doe','20213tn076@utez.edu.mx', 1, 'Active')
        ]

        event = {
            'body': json.dumps({'id_auto': '1'})
        }
        context = {}

        response = lambda_handler(event, context)

        response_body = json.loads(response['body'])

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response_body['statusCode'], 200)
        self.assertEqual(response_body['message'], 'Reseñas obtenidas correctamente.')
        self.assertEqual(len(response_body['data']), 1)
        self.assertEqual(response_body['data'][0]['id_rate'], 1)

    # Test for connection.py

    @patch('rate.get_one_data_rate.database.boto3.session.Session')
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

    @patch('rate.get_one_data_rate.database.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('rate.get_one_data_rate.database.pymysql.connect')
    @patch('rate.get_one_data_rate.database.get_secret')
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

    @patch('rate.get_one_data_rate.database.pymysql.connect')
    @patch('rate.get_one_data_rate.database.get_secret')
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

    @patch('rate.get_one_data_rate.database.execute_query')
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

    @patch('rate.get_one_data_rate.database.execute_query')
    def test_execute_query_exception(self, mock_connection):
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        query = "SELECT * FROM table"
        with self.assertRaises(Exception) as context:
            execute_query(mock_connection, query)

        self.assertTrue('Database error' in str(context.exception))
        mock_cursor.execute.assert_called_once_with(query)

    @patch('rate.get_one_data_rate.database.close_connection')
    def test_close_connection_successful(self, mock_close_connection):
        mock_connection = MagicMock()

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

    @patch('rate.get_one_data_rate.database.close_connection')
    def test_close_connection_none(self, mock_close_connection):
        close_connection(None)
        self.assertEqual(mock_close_connection.call_count, 0)
