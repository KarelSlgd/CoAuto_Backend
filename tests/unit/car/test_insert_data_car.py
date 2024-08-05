import unittest
from unittest.mock import patch
import json
import pymysql
import base64
from car.insert_data_car.app import lambda_handler, insert_into_car
from car.insert_data_car.connection import get_connection, handle_response, headers_cors, get_secret, \
    handle_response_success, get_jwt_claims
from botocore.exceptions import ClientError


class TestInsertCar(unittest.TestCase):
    @patch('car.insert_data_car.app.get_jwt_claims')
    def test_client_user_group(self, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'fake_token'}}
        context = {}
        mock_get_jwt_claims.return_value = {'cognito:groups': ['ClientUserGroup']}

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Acceso denegado. El rol no puede ser cliente.', response['body'])

    @patch('car.insert_data_car.app.get_jwt_claims')
    def test_token_decoding_error(self, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'fake_token'}}
        context = {}
        mock_get_jwt_claims.side_effect = Exception('Error decoding token')

        response = lambda_handler(event, context)
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Error decoding token', response['body'])

    @patch('car.insert_data_car.app.get_connection')
    @patch('car.insert_data_car.app.handle_response')
    def test_insert_into_car_exception(self, mock_handle_response, mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = Exception("Database error")

        mock_handle_response.return_value = {
            'statusCode': 500,
            'body': 'Error al insertar auto.'
        }

        model = 'Test Model'
        brand = 'Test Brand'
        year = 2021
        price = 10000.00
        type = 'SUV'
        fuel = 'Gasoline'
        doors = 4
        engine = 'V6'
        height = 1.75
        width = 2.00
        length = 4.50
        description = 'Test Description'
        image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']

        response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length, description, image_urls)

        mock_handle_response.assert_called_once()
        called_args = mock_handle_response.call_args[0]
        self.assertIsInstance(called_args[0], Exception)
        self.assertEqual(str(called_args[0]), "Database error")
        self.assertEqual(called_args[1], 'Error al insertar auto.')
        self.assertEqual(called_args[2], 500)
        self.assertEqual(response['statusCode'], 500)
        self.assertEqual(response['body'], 'Error al insertar auto.')

    @patch('car.insert_data_car.app.insert_into_car')
    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_jwt_claims, mock_insert_into_car):
        mock_get_jwt_claims.return_value = {'cognito:groups': ['AdminGroup']}

        mock_insert_into_car.return_value = {
            'statusCode': 200,
            'body': 'Auto guardado correctamente.'
        }

        event = {
            'headers': {
                'Authorization': 'Bearer token'
            },
            'body': json.dumps({
                'model': 'Test Model',
                'brand': 'Test Brand',
                'year': 2021,
                'price': 10000.00,
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': 4,
                'engine': 'V6',
                'height': 1.75,
                'width': 2.00,
                'length': 4.50,
                'description': 'Test Description',
                'image_urls': ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
            })
        }

        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], 'Auto guardado correctamente.')

    @patch('car.insert_data_car.app.get_connection')
    @patch('car.insert_data_car.app.handle_response_success')
    def test_insert_into_car_success(self, mock_handle_response_success, mock_get_connection):
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.lastrowid = 1

        mock_handle_response_success.return_value = {
            'statusCode': 200,
            'body': 'Auto guardado correctamente.'
        }

        model = 'Test Model'
        brand = 'Test Brand'
        year = 2021
        price = 10000.00
        type = 'SUV'
        fuel = 'Gasoline'
        doors = 4
        engine = 'V6'
        height = 1.75
        width = 2.00
        length = 4.50
        description = 'Test Description'
        image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']

        response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length,
                                   description, image_urls)

        # Verificaciones
        mock_cursor.execute.assert_any_call(
            """INSERT INTO auto (model, brand, year, price, type, fuel, doors, engine, height, width, length, description, id_status)  
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 3)""",
            (model, brand, year, price, type, fuel, doors, engine, height, width, length, description)
        )
        mock_cursor.execute.assert_any_call(
            "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)",
            (1, 'http://example.com/image1.jpg')
        )
        mock_cursor.execute.assert_any_call(
            "INSERT INTO auto_image (id_auto, url) VALUES (%s, %s)",
            (1, 'http://example.com/image2.jpg')
        )
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(response['body'], 'Auto guardado correctamente.')

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_type(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'Test Model',
            'brand': 'Test Brand',
            'year': 2020,
            'price': 20000,
            'type': 'a' * 31,
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': '2.0L',
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'Test Description',
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo tipo excede los 30 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_fuel(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'Test Model',
            'brand': 'Test Brand',
            'year': 2020,
            'price': 20000,
            'type': 'Sedan',
            'fuel': 'a' * 31,
            'doors': 4,
            'engine': '2.0L',
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'Test Description',
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo combustible excede los 30 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_description(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'Test Model',
            'brand': 'Test Brand',
            'year': 2020,
            'price': 20000,
            'type': 'Sedan',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': '2.0L',
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'a' * 256,
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo descripción excede los 255 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_brand(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'Test Model',
            'brand': 'a' * 51,
            'year': 2020,
            'price': 20000,
            'type': 'Sedan',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': '2.0L',
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'Test Description',
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo marca excede los 50 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_engine(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'Test Model',
            'brand': 'Test Brand',
            'year': 2020,
            'price': 20000,
            'type': 'Sedan',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': 'a' * 31,
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'Test Description',
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo motor excede los 30 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_length_exceeded_model(self, mock_handle_response, mock_get_jwt_claims):
        body = {
            'model': 'a' * 51,
            'brand': 'Test Brand',
            'year': 2020,
            'price': 20000,
            'type': 'Sedan',
            'fuel': 'Gasoline',
            'doors': 4,
            'engine': '2.0L',
            'height': 1.5,
            'width': 1.8,
            'length': 4.5,
            'description': 'Test Description',
            'image_urls': []
        }
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps(body)
        }
        lambda_handler(event, None)
        mock_handle_response.assert_called_with(None, 'El campo modelo excede los 50 caracteres.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_price(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': 'invalid_price',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V6',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo precio debe ser un decimal.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_doors(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': 'invalid_doors',
                'engine': 'V6',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo puertas debe ser un entero.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_height(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V6',
                'height': 'invalid_height',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo altura debe ser un decimal.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_width(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V6',
                'height': '1.5',
                'width': 'invalid_width',
                'length': '4.5',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo ancho debe ser un decimal.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_length(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V6',
                'height': '1.5',
                'width': '2.0',
                'length': 'invalid_length',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo largo debe ser un decimal.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims', return_value={'cognito:groups': ['UserGroup']})
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_year(self, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': 'invalid_year',
                'price': '25000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V6',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car',
                'image_urls': ['http://example.com/image1.jpg']
            })
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'El campo año debe ser un entero.', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    def test_invalid_body(self, mock_handle_response, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'valid_token'}, 'body': 'invalid_body'}
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_with(None, 'Parametros inválidos', 400)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    @patch('car.insert_data_car.app.insert_into_car')
    def test_lambda_handler_missing_token(self, mock_insert, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {}
        }
        context = {}

        lambda_handler(event, context)

        mock_handle_response.assert_called_once_with('Missing token.', 'Faltan parámetros.', 401)

    @patch('car.insert_data_car.app.get_jwt_claims')
    @patch('car.insert_data_car.app.handle_response')
    @patch('car.insert_data_car.app.insert_into_car')
    def test_lambda_handler_missing_parameters(self, mock_insert, mock_handle_response, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({})
        }
        context = {}

        mock_get_jwt_claims.return_value = {'cognito:groups': ['AdminGroup']}

        lambda_handler(event, context)

        mock_handle_response.assert_called_once_with(None, 'Faltan parámetros.', 400)

    # Test for connection.py

    @patch('car.insert_data_car.connection.boto3.session.Session.client')
    def test_get_secret(self, mock_boto_client):
        mock_client = mock_boto_client.return_value
        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'HOST': 'test_host',
                'USERNAME': 'test_user',
                'PASSWORD': 'test_password',
                'DB_NAME': 'test_db'
            })
        }

        secret = get_secret()
        self.assertEqual(secret['HOST'], 'test_host')
        self.assertEqual(secret['USERNAME'], 'test_user')
        self.assertEqual(secret['PASSWORD'], 'test_password')
        self.assertEqual(secret['DB_NAME'], 'test_db')

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
    def test_get_connection(self, mock_get_secret, mock_pymysql_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }

        mock_connection = mock_pymysql_connect.return_value

        connection = get_connection()
        mock_pymysql_connect.assert_called_once_with(
            host='test_host',
            user='test_user',
            password='test_password',
            database='test_db'
        )
        self.assertEqual(connection, mock_connection)

    def test_handle_response(self):
        response = handle_response('TestError', 'TestMessage', 400)
        expected_response = {
            'statusCode': 400,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 400,
                'message': 'TestMessage',
                'error': 'TestError'
            })
        }
        self.assertEqual(response, expected_response)

    def test_handle_response_success(self):
        response = handle_response_success(200, 'TestMessage', {'key': 'value'})
        expected_response = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'TestMessage',
                'data': {'key': 'value'}
            })
        }
        self.assertEqual(response, expected_response)

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
    def test_get_connection_exception(self, mock_get_secret, mock_connect):
        mock_get_secret.return_value = {
            'HOST': 'test_host',
            'USERNAME': 'test_user',
            'PASSWORD': 'test_password',
            'DB_NAME': 'test_db'
        }
        mock_connect.side_effect = pymysql.MySQLError("Connection error")

        with self.assertRaises(pymysql.MySQLError):
            get_connection()

    @patch('car.insert_data_car.connection.boto3.session.Session.client')
    def test_get_secret_client_error(self, mock_client):
        mock_client_instance = mock_client.return_value
        mock_client_instance.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Secret not found'}},
            'GetSecretValue'
        )

        with self.assertRaises(ClientError):
            get_secret()

    def test_get_jwt_claims_value_error(self):
        invalid_token = "invalid.token.part.trge"

        with self.assertRaises(ValueError) as context:
            get_jwt_claims(invalid_token)

        self.assertEqual(str(context.exception), "Token inválido")

    def test_valid_token(self):
        # creando un token válido
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
        signature = "b'123abc'"
        token = f"{base64.b64encode(json.dumps(header).encode()).decode()}.{base64.b64encode(json.dumps(payload).encode()).decode()}.{signature}"

        claims = get_jwt_claims(token)
        self.assertEqual(claims, payload)

    def test_invalid_token(self):
        # creando un token inválido
        token = "invalid.token"

        with self.assertRaises(ValueError) as context:
            get_jwt_claims(token)

        self.assertEqual(str(context.exception), "Token inválido")

    def test_non_string_token(self):
        # creando un token inválido
        token = 12345

        with self.assertRaises(AttributeError):
            get_jwt_claims(token)
