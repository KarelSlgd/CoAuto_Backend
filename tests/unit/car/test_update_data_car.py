import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from car.update_data_car.app import lambda_handler, update_car, get_existing_image_urls
from car.update_data_car.connection import get_connection, handle_response, headers_cors, get_secret
from botocore.exceptions import ClientError


class TestUpdateCar(unittest.TestCase):

    def test_invalid_body(self):
        event = {
            'body': 'invalid json'
        }
        response = lambda_handler(event, None)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response_body['message'], 'Cuerpo de la petición inválido.')

    def setUp(self):
        self.context = Mock()

    def test_long_model(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'M' * 51,
                'brand': 'Tesla',
                'year': 2022,
                'price': 79999,
                'type': 'Sedan',
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'Dual Motor',
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'A great electric car.',
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo modelo excede los 50 caracteres.', response['body'])

    def test_long_brand(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Mod',
                'brand': 'B' * 52,
                'year': 2022,
                'price': 79999,
                'type': 'Sedan',
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'Dual Motor',
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'A great electric car.',
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo marca excede los 50 caracteres.', response_body['message'])

    def test_long_type(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model S',
                'brand': 'Tesla',
                'year': 2022,
                'price': 79999,
                'type': 'T' * 31,
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'Dual Motor',
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'A great electric car.',
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo tipo excede los 30 caracteres.', response['body'])

    def test_long_fuel(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model S',
                'brand': 'Tesla',
                'year': 2022,
                'price': 79999,
                'type': 'Sedan',
                'fuel': 'F' * 31,
                'doors': 4,
                'engine': 'Dual Motor',
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'A great electric car.',
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo combustible excede los 30 caracteres.', response['body'])

    def test_long_engine(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model S',
                'brand': 'Tesla',
                'year': 2022,
                'price': 79999,
                'type': 'Sedan',
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'E' * 31,
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'A great electric car.',
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo motor excede los 30 caracteres.', response['body'])

    def test_long_description(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model S',
                'brand': 'Tesla',
                'year': 2022,
                'price': 79999,
                'type': 'Sedan',
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'Dual Motor',
                'height': 1445,
                'width': 1963,
                'length': 4978,
                'description': 'D' * 256,
                'image_urls': []
            })
        }
        response = lambda_handler(event, self.context)
        response_body = json.loads(response['body'])
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El campo descripción excede los 255 caracteres.', response_body['message'])

    def test_invalid_price(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model X',
                'brand': 'Brand X',
                'year': '2020',
                'price': 'invalid price',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.0',
                'description': 'Test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El precio debe ser un decimal.', response['body'])

    def test_invalid_doors(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model X',
                'brand': 'Brand X',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': 'invalid doors',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': '4.0',
                'description': 'Test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Las puertas deben ser un entero.', response['body'])

    def test_invalid_height(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model X',
                'brand': 'Brand X',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': 'invalid height',
                'width': '2.0',
                'length': '4.0',
                'description': 'Test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('La altura debe ser un decimal.', response['body'])

    def test_invalid_width(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model X',
                'brand': 'Brand X',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': 'invalid width',
                'length': '4.0',
                'description': 'Test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('El ancho debe ser un decimal.', response['body'])

    def test_invalid_length(self):
        event = {
            'body': json.dumps({
                'id_auto': '123',
                'model': 'Model X',
                'brand': 'Brand X',
                'year': '2020',
                'price': '20000',
                'type': 'SUV',
                'fuel': 'Gasoline',
                'doors': '4',
                'engine': 'V8',
                'height': '1.5',
                'width': '2.0',
                'length': 'invalid length',
                'description': 'Test description',
                'image_urls': []
            })
        }
        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('La longitud debe ser un decimal.', response['body'])

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.handle_response')
    def test_invalid_json_body(self, mock_handle_response, mock_get_connection):
        event = {'body': 'invalid json'}
        context = {}
        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'Cuerpo de la petición inválido.', 400)

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.handle_response')
    def test_missing_parameters(self, mock_handle_response, mock_get_connection):
        event = {'body': json.dumps({})}
        context = {}
        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'Faltan parámetros.', 400)

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.handle_response')
    def test_invalid_year_format(self, mock_handle_response, mock_get_connection):
        body = {
            'id_auto': '1', 'model': 'Model X', 'brand': 'Toyota', 'year': 'twenty-twenty',
            'price': '20000', 'type': 'SUV', 'fuel': 'Gasoline', 'doors': '4',
            'engine': 'V8', 'height': '1.5', 'width': '2.0', 'length': '4.5',
            'description': 'Nice car', 'image_urls': []
        }
        event = {'body': json.dumps(body)}
        context = {}
        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El año debe ser un entero.', 400)

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.handle_response')
    def test_invalid_price_format(self, mock_handle_response, mock_get_connection):
        body = {
            'id_auto': '1', 'model': 'Model X', 'brand': 'Toyota', 'year': '2020',
            'price': 'twenty thousand', 'type': 'SUV', 'fuel': 'Gasoline', 'doors': '4',
            'engine': 'V8', 'height': '1.5', 'width': '2.0', 'length': '4.5',
            'description': 'Nice car', 'image_urls': []
        }
        event = {'body': json.dumps(body)}
        context = {}
        response = lambda_handler(event, context)
        mock_handle_response.assert_called_with(None, 'El precio debe ser un decimal.', 400)

    @patch('car.update_data_car.app.get_connection')
    def test_get_existing_image_urls(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_cursor = mock_connection.cursor.return_value.__enter__.return_value
        mock_cursor.fetchall.return_value = [('url1',), ('url2',)]

        cursor = mock_cursor
        id_auto = '1'
        urls = get_existing_image_urls(cursor, id_auto)

        self.assertEqual(urls, ['url1', 'url2'])

    @patch('car.update_data_car.app.update_car')
    def test_lambda_handler_success(self, mock_update_car):
        event = {
            'body': json.dumps({
                'id_auto': 1,
                'model': 'Model S',
                'brand': 'Tesla',
                'year': 2020,
                'price': 80000,
                'type': 'Sedan',
                'fuel': 'Electric',
                'doors': 4,
                'engine': 'Electric',
                'height': 1445,
                'width': 1963,
                'length': 4970,
                'description': 'A great electric car.',
                'image_urls': ['url1', 'url2']
            })
        }

        mock_update_car.return_value = {
            'statusCode': 200,
            'body': json.dumps({
                'statusCode': 200,
                'message': 'Auto actualizado correctamente.'
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Auto actualizado correctamente.', response['body'])

    @patch('car.update_data_car.app.get_connection')
    @patch('car.update_data_car.app.get_existing_image_urls')
    def test_update_car_success(self, mock_get_existing_image_urls, mock_get_connection):
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        mock_get_existing_image_urls.return_value = ['url1']

        response = update_car(
            id_auto=1,
            model='Model S',
            brand='Tesla',
            year=2020,
            price=80000,
            type='Sedan',
            fuel='Electric',
            doors=4,
            engine='Electric',
            height=1445,
            width=1963,
            length=4970,
            description='A great electric car.',
            image_urls=['url2']
        )

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Auto actualizado correctamente.', json.loads(response['body'])['message'])

        mock_cursor.execute.assert_any_call(
            "UPDATE auto SET model=%s, brand=%s, year=%s, price=%s, type=%s, fuel=%s, doors=%s, engine=%s, height=%s, width=%s, length=%s, description=%s WHERE id_auto=%s",
            ('Model S', 'Tesla', 2020, 80000, 'Sedan', 'Electric', 4, 'Electric', 1445, 1963, 4970,
             'A great electric car.', 1)
        )

        mock_cursor.execute.assert_any_call(
            "INSERT INTO auto_image (url, id_auto) VALUES (%s, %s)",
            ('url2', 1)
        )

        mock_cursor.execute.assert_any_call(
            "DELETE FROM auto_image WHERE url = %s AND id_auto = %s",
            ('url1', 1)
        )

    @patch('car.update_data_car.app.get_connection')
    def test_update_car_db_error(self, mock_get_connection):
        mock_connection = MagicMock()
        mock_connection.cursor.side_effect = Exception('DB error')
        mock_get_connection.return_value = mock_connection

        response = update_car(
            id_auto=1,
            model='Model S',
            brand='Tesla',
            year=2020,
            price=80000,
            type='Sedan',
            fuel='Electric',
            doors=4,
            engine='Electric',
            height=1445,
            width=1963,
            length=4970,
            description='A great electric car.',
            image_urls=['url2']
        )

        self.assertEqual(response['statusCode'], 500)
        response_body = json.loads(response['body'])
        self.assertEqual(response_body['message'], 'Ocurrió un error al actualizar el auto.')
        self.assertEqual(response_body['error'], 'DB error')

    # Test for connection.py

    @patch('car.update_data_car.connection.boto3.session.Session')
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

    @patch('car.update_data_car.connection.boto3.session.Session')
    def test_get_secret_error(self, mock_session):
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        mock_client.get_secret_value.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetSecretValue')

        with self.assertRaises(ClientError):
            get_secret()

    @patch('car.update_data_car.connection.pymysql.connect')
    @patch('car.update_data_car.connection.get_secret')
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

    @patch('car.update_data_car.connection.pymysql.connect')
    @patch('car.update_data_car.connection.get_secret')
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
