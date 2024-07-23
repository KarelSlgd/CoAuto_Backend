import unittest
from unittest.mock import patch, MagicMock, ANY
import json
import base64
from rate.insert_data_rate.app import lambda_handler, insert_into_rate, verify_user, verify_auto, check_existing_review, get_jwt_claims
from rate.insert_data_rate.database import get_secret, get_connection, execute_query, close_connection, headers_cors, \
    handle_response
from botocore.exceptions import ClientError


class TestInsertRate(unittest.TestCase):
    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_invalid_token(self, mock_handle_response, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'invalid_token'}}
        context = {}

        exception_instance = Exception("Invalid token")
        mock_get_jwt_claims.side_effect = exception_instance
        lambda_handler(event, context)

        args, kwargs = mock_handle_response.call_args
        exception_arg, error_message, status_code = args
        self.assertEqual(error_message, 'Error al decodificar token.')
        self.assertEqual(status_code, 401)
        self.assertIsInstance(exception_arg, Exception)
        self.assertEqual(str(exception_arg), str(exception_instance))

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_invalid_body(self, mock_handle_response, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'valid_token'}, 'body': 'invalid_json'}
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(ANY, 'Cuerpo de la petición inválido.', 400)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_missing_parameters(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({'comment': 'Good car'})
        }
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(
            None, 'Faltan parámetros.', 400
        )

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_lambda_handler_invalid_value(self, mock_handle_response, mock_get_connection, mock_get_jwt_claims):
        event = {'body': json.dumps({'value': 'invalid', 'comment': 'test', 'id_auto': 1, 'id_user': 1})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El valor de la reseña debe ser un número entero.', 400)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    def test_value_out_of_range(self, mock_get_jwt_claims):
        event = {
            'body': json.dumps({
                'value': '7',
                'comment': 'Buen servicio',
                'id_auto': '123',
                'id_user': '456'
            })
        }
        context = {}
        response = lambda_handler(event, context)
        body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El valor de la reseña debe estar entre 1 y 5.', body['message'])

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.verify_user', return_value=True)
    @patch('rate.insert_data_rate.app.handle_response')
    def test_error_getting_user_id(self, mock_handle_response, mock_verify_user, mock_get_connection, mock_get_jwt_claims):
        mock_connection = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value.execute.side_effect = Exception('DB error')
        mock_get_connection.return_value = mock_connection
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({'value': '5', 'comment': 'Good car', 'id_auto': '1'})
        }
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(
            unittest.mock.ANY, 'Error al obtener el id del usuario.', 500
        )

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.verify_user')
    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_lambda_handler_user_not_found(self, mock_handle_response, mock_get_connection, mock_verify_user, mock_get_jwt_claims):
        mock_verify_user.return_value = False
        event = {'body': json.dumps({'value': '4', 'comment': 'test', 'id_auto': 1, 'id_user': 1})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El usuario no fue encontrado.', 400)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.verify_user')
    @patch('rate.insert_data_rate.app.verify_auto')
    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_lambda_handler_auto_not_found(self, mock_handle_response, mock_get_connection, mock_verify_auto, mock_verify_user, mock_get_jwt_claims):
        mock_verify_user.return_value = True
        mock_verify_auto.return_value = False
        event = {'body': json.dumps({'value': '4', 'comment': 'test', 'id_auto': 1, 'id_user': 1})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El auto no fue encontrado.', 400)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_comment_too_long(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({'value': '5', 'comment': 'a' * 101, 'id_auto': '1'})
        }
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(
            None, 'El comentario no debe exceder los 100 caracteres.', 400
        )

    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_insert_into_rate_exception(self, mock_handle_response, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("DB Error")

        mock_handle_response.return_value = {
            'statusCode': 500,
            'body': 'Error al insertar la reseña.'
        }

        response = insert_into_rate(4, 'test', 1, 1)

        mock_handle_response.assert_called_with(ANY, 'Error al insertar la reseña.', 500)
        self.assertEqual(response['statusCode'], 500)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.verify_user')
    @patch('rate.insert_data_rate.app.verify_auto')
    @patch('rate.insert_data_rate.app.check_existing_review')
    @patch('rate.insert_data_rate.app.insert_into_rate')
    @patch('rate.insert_data_rate.app.get_connection')
    @patch('rate.insert_data_rate.app.handle_response')
    def test_lambda_handler_existing_review(self, mock_handle_response, mock_get_connection, mock_insert_into_rate, mock_check_existing_review, mock_verify_auto, mock_verify_user, mock_get_jwt_claims):
        mock_verify_user.return_value = True
        mock_verify_auto.return_value = True
        mock_check_existing_review.return_value = True
        event = {'body': json.dumps({'value': '4', 'comment': 'test', 'id_auto': 1, 'id_user': 1})}
        context = {}
        lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El usuario ya ha reseñado este auto.', 400)

    @patch('rate.insert_data_rate.app.get_jwt_claims')
    @patch('rate.insert_data_rate.app.verify_user')
    @patch('rate.insert_data_rate.app.verify_auto')
    @patch('rate.insert_data_rate.app.check_existing_review')
    @patch('rate.insert_data_rate.app.get_connection')
    def test_lambda_handler_successful(self, mock_get_connection, mock_check_existing_review, mock_verify_auto, mock_verify_user, mock_get_jwt_claims):
        mock_verify_user.return_value = True
        mock_verify_auto.return_value = True
        mock_check_existing_review.return_value = False
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        event = {'body': json.dumps({'value': '4', 'comment': 'test', 'id_auto': 1, 'id_user': 1})}
        context = {}
        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 200)

    @patch('rate.insert_data_rate.app.get_connection')
    def test_insert_into_rate(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        response = insert_into_rate(4, 'test', 1, 1)
        self.assertEqual(response['statusCode'], 200)

    @patch('rate.insert_data_rate.app.get_connection')
    def test_verify_user(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = True
        self.assertTrue(verify_user(1))

    @patch('rate.insert_data_rate.app.get_connection')
    def test_verify_auto(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = True
        self.assertTrue(verify_auto(1))

    @patch('rate.insert_data_rate.app.get_connection')
    def test_check_existing_review(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.fetchone.return_value = True
        self.assertTrue(check_existing_review(1, 1))

    @patch('rate.insert_data_rate.app.get_connection')
    def test_verify_user_exception(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("DB Error")

        result = verify_user(1)

        self.assertFalse(result)

    @patch('rate.insert_data_rate.app.get_connection')
    def test_verify_auto_exception(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("DB Error")

        result = verify_auto(1)

        self.assertFalse(result)

    @patch('rate.insert_data_rate.app.get_connection')
    def test_check_existing_review_exception(self, mock_get_connection):
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
        mock_cursor.execute.side_effect = Exception("DB Error")

        result = check_existing_review(1, 1)

        self.assertFalse(result)

    # Test for connection.py

    @patch('rate.insert_data_rate.database.boto3.session.Session')
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

    @patch('rate.insert_data_rate.database.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('rate.insert_data_rate.database.pymysql.connect')
    @patch('rate.insert_data_rate.database.get_secret')
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

    @patch('rate.insert_data_rate.database.pymysql.connect')
    @patch('rate.insert_data_rate.database.get_secret')
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

    @patch('rate.insert_data_rate.database.execute_query')
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

    @patch('rate.insert_data_rate.database.execute_query')
    def test_execute_query_exception(self, mock_connection):
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception("Database error")

        query = "SELECT * FROM table"
        with self.assertRaises(Exception) as context:
            execute_query(mock_connection, query)

        self.assertTrue('Database error' in str(context.exception))
        mock_cursor.execute.assert_called_once_with(query)

    @patch('rate.insert_data_rate.database.close_connection')
    def test_close_connection_successful(self, mock_close_connection):
        mock_connection = MagicMock()

        close_connection(mock_connection)

        mock_connection.close.assert_called_once()

    @patch('rate.insert_data_rate.database.close_connection')
    def test_close_connection_none(self, mock_close_connection):
        close_connection(None)
        self.assertEqual(mock_close_connection.call_count, 0)

    def test_valid_token(self):
        # Crear un token JWT válido
        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().strip("=")
        payload = base64.b64encode(json.dumps({"cognito:username": "test_user"}).encode()).decode().strip("=")
        signature = "signature"
        token = f"{header}.{payload}.{signature}"

        expected_claims = {"cognito:username": "test_user"}
        self.assertEqual(get_jwt_claims(token), expected_claims)

    def test_invalid_token_format(self):
        token = "invalid.token.format.asdasd"
        with self.assertRaises(ValueError) as context:
            get_jwt_claims(token)
        self.assertEqual(str(context.exception), "Token inválido")

    def test_token_invalid(self):
        header = base64.b64encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode()).decode().strip("=")
        payload = base64.b64encode(b"invalid_payload").decode().strip("=")
        signature = "signature"
        token = f"{header}.{payload}.{signature}"

        with self.assertRaises(json.JSONDecodeError):
            get_jwt_claims(token)