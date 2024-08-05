import unittest
from unittest.mock import patch
import pymysql
import base64
import json
from car.update_data_car.app import lambda_handler, update_car, get_existing_image_urls
from car.update_data_car.connection import get_connection, handle_response, headers_cors, get_secret, \
    handle_response_success, get_jwt_claims
from botocore.exceptions import ClientError


class TestUpdateCar(unittest.TestCase):
    @patch('car.update_data_car.app.get_connection')
    def test_update_car_db_error(self, mock_get_connection):
        # Setup mocks
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_cursor.execute.side_effect = Exception("Database error")

        # Call the function
        response = update_car(
            id_auto=1,
            model='Test Model',
            brand='Test Brand',
            year=2022,
            price=25000.0,
            type='SUV',
            fuel='Gasoline',
            doors=4,
            engine='V6',
            height=1.5,
            width=2.0,
            length=4.5,
            description='Test Description',
            image_urls=['new_image1.jpg', 'existing_image1.jpg']
        )

        # Assertions
        self.assertEqual(response, handle_response(Exception("Database error"), 'Ocurrió un error al actualizar el auto.', 500))

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.get_existing_image_urls')
    def test_update_car_success(self, mock_get_existing_image_urls, mock_get_connection):
        # Setup mocks
        mock_connection = mock_get_connection.return_value
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value

        mock_get_existing_image_urls.return_value = ['existing_image1.jpg', 'existing_image2.jpg']

        # Call the function
        response = update_car(
            id_auto=1,
            model='Test Model',
            brand='Test Brand',
            year=2022,
            price=25000.0,
            type='SUV',
            fuel='Gasoline',
            doors=4,
            engine='V6',
            height=1.5,
            width=2.0,
            length=4.5,
            description='Test Description',
            image_urls=['new_image1.jpg', 'existing_image1.jpg']
        )

        # Assertions
        self.assertEqual(response, handle_response_success(200, 'Auto actualizado correctamente.', None))

        # Check that the update query was executed
        mock_cursor.execute.assert_any_call(
            "UPDATE auto SET model=%s, brand=%s, year=%s, price=%s, type=%s, fuel=%s, doors=%s, engine=%s, height=%s, width=%s, length=%s, description=%s WHERE id_auto=%s",
            (
            'Test Model', 'Test Brand', 2022, 25000.0, 'SUV', 'Gasoline', 4, 'V6', 1.5, 2.0, 4.5, 'Test Description', 1)
        )

        # Check that the new image URL was inserted
        mock_cursor.execute.assert_any_call(
            "INSERT INTO auto_image (url, id_auto) VALUES (%s, %s)",
            ('new_image1.jpg', 1)
        )

        # Check that the old image URL was deleted
        mock_cursor.execute.assert_any_call(
            "DELETE FROM auto_image WHERE url = %s AND id_auto = %s",
            ('existing_image2.jpg', 1)
        )

        # Ensure that the connection commit was called
        mock_connection.commit.assert_called_once()
    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_price_not_float(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': 'not_a_float',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El precio debe ser un decimal.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_doors_not_integer(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': 'not_an_integer',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'Las puertas deben ser un entero.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_height_not_float(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': 'not_a_float',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'La altura debe ser un decimal.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_width_not_float(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': 'not_a_float',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El ancho debe ser un decimal.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_length_not_float(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': 'not_a_float',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'La longitud debe ser un decimal.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_brand_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'a' * 51,
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo marca excede los 50 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_type_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'a' * 31,
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo tipo excede los 30 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_fuel_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'a' * 31,
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo combustible excede los 30 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_engine_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'a' * 31,
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo motor excede los 30 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_description_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'a' * 256,
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo descripción excede los 255 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_year_not_integer(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': 'not_an_integer',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El año debe ser un entero.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_missing_parameters(self, mock_get_jwt_claims):
        required_fields = ['id_auto', 'model', 'brand', 'year', 'price', 'type', 'fuel', 'doors', 'engine', 'height', 'width', 'length']
        for field in required_fields:
            event = {
                'headers': {'Authorization': 'fake_token'},
                'body': json.dumps({
                    'id_auto': '123',
                    'model': 'TestModel',
                    'brand': 'TestBrand',
                    'year': '2020',
                    'price': '25000.00',
                    'type': 'Sedan',
                    'fuel': 'Gasoline',
                    'doors': '4',
                    'engine': 'V8',
                    'height': '1.5',
                    'width': '2.0',
                    'length': '4.5',
                    'description': 'A test description',
                    'image_urls': []
                })
            }
            body = json.loads(event['body'])
            del body[field]
            event['body'] = json.dumps(body)
            response = lambda_handler(event, None)
            self.assertEqual(response, handle_response(None, 'Faltan parámetros.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["AdminGroup"]})
    def test_model_length_exceeded(self, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'a' * 51,
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response(None, 'El campo modelo excede los 50 caracteres.', 400))

    @patch('car.update_data_car.app.get_jwt_claims', return_value={"cognito:groups": ["ClientUserGroup"]})
    @patch('car.update_data_car.app.update_car', return_value={"statusCode": 200, "body": "Success"})
    def test_client_user_group(self, mock_update_car, mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'fake_token'},
            'body': json.dumps({
                'id_auto': '123',
                'model': 'TestModel',
                'brand': 'TestBrand',
                'year': '2020',
                'price': '25000.00',
                'type': 'Sedan',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response, handle_response('Acceso denegado. El rol no puede ser cliente.', 'Acceso denegado.', 401))

    @patch('car.update_data_car.app.get_connection')
    def test_get_existing_image_urls(self, mock_get_connection):
        mock_connection = patch('car.update_data_car.app.get_connection').start()
        mock_cursor = mock_connection.cursor().return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [('url1',), ('url2',)]

        result = get_existing_image_urls(mock_cursor, 1)
        self.assertEqual(result, ['url1', 'url2'])
        mock_connection.stop()

    @patch('car.update_data_car.app.get_jwt_claims')
    @patch('car.update_data_car.app.handle_response')
    def test_lambda_handler_missing_token(self, mock_handle_response, mock_get_jwt_claims):
        event = {'headers': {}}
        context = {}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with('Missing token.', 'Faltan parámetros.', 401)

    @patch('car.update_data_car.app.get_jwt_claims')
    @patch('car.update_data_car.app.handle_response')
    def test_lambda_handler_invalid_body(self, mock_handle_response, mock_get_jwt_claims):
        event = {'headers': {'Authorization': 'valid_token'}, 'body': 'invalid_body'}
        context = {}
        mock_get_jwt_claims.return_value = {'cognito:groups': ['SomeGroup']}

        lambda_handler(event, context)
        mock_handle_response.assert_called_once_with(None, 'Cuerpo de la petición inválido.', 400)

    @patch('car.update_data_car.app.get_jwt_claims')
    @patch('car.update_data_car.app.update_car')
    @patch('car.update_data_car.app.handle_response')
    @patch('car.update_data_car.app.handle_response_success')
    def test_lambda_handler_success(self, mock_handle_response_success, mock_handle_response, mock_update_car,
                                    mock_get_jwt_claims):
        event = {
            'headers': {'Authorization': 'valid_token'},
            'body': json.dumps({
                'id_auto': 1, 'model': 'TestModel', 'brand': 'TestBrand', 'year': 2020, 'price': 10000.0,
                'type': 'SUV', 'fuel': 'Gasoline', 'doors': 4, 'engine': 'V6', 'height': 1.5, 'width': 2.0,
                'length': 4.5,
                'description': 'Test Description', 'image_urls': []
            })
        }
        context = {}
        mock_get_jwt_claims.return_value = {'cognito:groups': ['SomeGroup']}
        mock_update_car.return_value = mock_handle_response_success(200, 'Auto actualizado correctamente.', None)

        response = lambda_handler(event, context)
        self.assertTrue(mock_handle_response_success.called)

    # Test for connection.py

    @patch('car.update_data_car.connection.boto3.session.Session.client')
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

    @patch('car.update_data_car.connection.pymysql.connect')
    @patch('car.update_data_car.connection.get_secret')
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

    @patch('car.update_data_car.connection.pymysql.connect')
    @patch('car.update_data_car.connection.get_secret')
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

    @patch('car.update_data_car.connection.boto3.session.Session.client')
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
