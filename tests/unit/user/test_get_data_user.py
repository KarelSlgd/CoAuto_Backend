import unittest
import json

from unittest.mock import patch, MagicMock
from user.get_data_user import app


class TestUser(unittest.TestCase):

    @patch('user.get_data_user.app.get_connection')
    @patch('user.get_data_user.app.handle_response')
    def test_lambda_handler_success(self, mock_handle_response, mock_get_connection):
        # Mockear la conexión y los resultados de la consulta
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        # Simular resultados de la consulta
        mock_cursor.fetchall.return_value = [
            (1, 'cognito_1', 'email1@example.com', 'John', 'Doe', 'Admin', 'Active', 'image1.jpg'),
            (2, 'cognito_2', 'email2@example.com', 'Jane', 'Smith', 'User', 'Inactive', 'image2.jpg')
        ]

        # Ejecutar la función
        response = app.lambda_handler({}, {})

        # Verificar el código de estado y la estructura de la respuesta
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['statusCode'], 200)
        self.assertEqual(body['message'], 'Usuarios obtenidos correctamente')
        self.assertEqual(len(body['data']), 2)
        self.assertEqual(body['data'][0]['name'], 'John')

    @patch('user.get_data_user.app.get_connection')
    @patch('user.get_data_user.app.handle_response')
    def test_lambda_handler_query_failure(self, mock_handle_response, mock_get_connection):
        # Mockear la conexión y forzar una excepción
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_connection
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.execute.side_effect = Exception('Database error')

        # Simular respuesta de handle_response
        mock_handle_response.return_value = {
            "statusCode": 500,
            "body": json.dumps({
                "error": "Error al obtener usuarios"
            }),
        }

        # Ejecutar la función
        response = app.lambda_handler({}, {})

        # Verificar el código de estado y la estructura de la respuesta
        self.assertEqual(response['statusCode'], 500)
        body = json.loads(response['body'])
        self.assertEqual(body['error'], 'Error al obtener usuarios')

