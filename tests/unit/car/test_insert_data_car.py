import unittest
from unittest.mock import patch, Mock, MagicMock
import json
from car.insert_data_car.app import lambda_handler, insert_into_car
from car.insert_data_car.connection import get_connection, handle_response, headers_cors, get_secret
from botocore.exceptions import ClientError


class TestInsertCar(unittest.TestCase):

    def test_missing_body(self):
        event = {}
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parametros inválidos', response_body['message'])

    def test_none_body(self):
        event = {'body': None}
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Parametros inválidos', response_body['message'])

    def test_missing_parameters(self):
        event = {'body': json.dumps({
            'model': 'Model',
            # Falta 'brand', 'year', 'price', 'type', 'fuel', 'doors', 'engine', 'height', 'width', 'length'
            'description': 'Description',
            'image_urls': []
        })}
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Faltan parámetros.', response_body['message'])

    def test_model_too_long(self):
        event = {
            'body': json.dumps({
                'model': 'A' * 51,
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo modelo excede los 50 caracteres', response['body'])

    def test_brand_too_long(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'B' * 51,
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo marca excede los 50 caracteres', response['body'])

    def test_engine_too_long(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'E' * 31,
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo motor excede los 30 caracteres', response['body'])

    def test_type_too_long(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'T' * 31,
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo tipo excede los 30 caracteres', response['body'])

    def test_fuel_too_long(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'F' * 31,
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo combustible excede los 30 caracteres', response['body'])

    def test_description_too_long(self):
        event = {'body': json.dumps({
            'model': 'Model',
            'brand': 'Brand',
            'year': '2020',
            'price': '10000',
            'type': 'Type',
            'fuel': 'Fuel',
            'doors': '4',
            'engine': 'Engine',
            'height': '1.5',
            'width': '2.0',
            'length': '4.5',
            'description': 'a' * 256,
            'image_urls': []
        })}
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        expected_message = 'El campo descripción excede los 255 caracteres.'
        self.assertEqual(response['statusCode'], 400)
        self.assertIn(expected_message, response_body['message'])

    def test_invalid_year(self):
        event = {'body': json.dumps({
            'model': 'Model',
            'brand': 'Brand',
            'year': 'invalid',
            'price': '10000',
            'type': 'Type',
            'fuel': 'Fuel',
            'doors': '4',
            'engine': 'Engine',
            'height': '1.5',
            'width': '2.0',
            'length': '4.5',
            'description': 'Description',
            'image_urls': []
        })}
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo año debe ser un entero.', response_body['message'])

    def test_invalid_price(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': 'invalid',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo precio debe ser un decimal', response['body'])

    def test_invalid_doors(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': 'invalid',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo puertas debe ser un entero', response['body'])

    def test_invalid_height(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': 'invalid',
                'width': '2.0',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo altura debe ser un decimal', response['body'])

    def test_invalid_width(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': 'invalid',
                'length': '4.5',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo ancho debe ser un decimal', response['body'])

    def test_invalid_length(self):
        event = {
            'body': json.dumps({
                'model': 'Sedan',
                'brand': 'Toyota',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': 'invalid',
                'description': 'A nice car'
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo largo debe ser un decimal', response['body'])

    @patch('car.insert_data_car.app.get_connection')
    @patch('car.insert_data_car.app.handle_response')
    def test_insert_into_car_success(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        model = 'Modelo X'
        brand = 'Marca Y'
        year = 2022
        price = 30000
        type = 'Sedán'
        fuel = 'Gasolina'
        doors = 4
        engine = '2.0L'
        height = 1.5
        width = 2.0
        length = 4.0
        description = 'Un auto muy bueno'
        image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']

        response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length,
                                   description, image_urls)

        self.assertEqual(mock_cursor.execute.call_count, 3)
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Auto guardado correctamente.')

    @patch('car.insert_data_car.app.get_connection')
    @patch('car.insert_data_car.app.handle_response')
    def test_insert_into_car_failure(self, mock_handle_response, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.execute.side_effect = Exception("Test Exception")

        model = 'Modelo X'
        brand = 'Marca Y'
        year = 2022
        price = 30000
        type = 'Sedán'
        fuel = 'Gasolina'
        doors = 4
        engine = '2.0L'
        height = 1.5
        width = 2.0
        length = 4.0
        description = 'Un auto muy bueno'
        image_urls = ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']

        response = insert_into_car(model, brand, year, price, type, fuel, doors, engine, height, width, length,
                                   description, image_urls)

        self.assertTrue(mock_handle_response.called)
        called_args = mock_handle_response.call_args[0]
        self.assertEqual(str(called_args[0]), str(Exception("Test Exception")))
        self.assertEqual(called_args[1], 'Error al insertar auto.')
        self.assertEqual(called_args[2], 500)

    @patch('car.insert_data_car.app.insert_into_car')
    def test_lambda_handler(self, mock_insert_into_car):
        event = {
            'body': json.dumps({
                'model': 'Modelo X',
                'brand': 'Marca Y',
                'year': 2022,
                'price': 30000,
                'type': 'Sedán',
                'fuel': 'Gasolina',
                'doors': 4,
                'engine': '2.0L',
                'height': 1.5,
                'width': 2.0,
                'length': 4.0,
                'description': 'Un auto muy bueno',
                'image_urls': ['http://example.com/image1.jpg', 'http://example.com/image2.jpg']
            })
        }
        context = {}

        mock_insert_into_car.return_value = {
            'statusCode': 200,
            'headers': headers_cors,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Auto guardado correctamente.'
            })
        }

        response = lambda_handler(event, context)

        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body'])['message'], 'Auto guardado correctamente.')

    # Test for connection.py

    @patch('car.insert_data_car.connection.boto3.session.Session')
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

    @patch('car.insert_data_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
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

    @patch('car.insert_data_car.connection.pymysql.connect')
    @patch('car.insert_data_car.connection.get_secret')
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
