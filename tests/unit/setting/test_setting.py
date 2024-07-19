import unittest
from setting.app import lambda_handler, headers_open


class TestSetting(unittest.TestCase):

    def test_lambda_handler(self):
        event = {}
        context = {}

        response = lambda_handler(event, context)

        expected_response = {
            'statusCode': 200,
            'headers': headers_open,
            'body': ''
        }

        self.assertEqual(response['statusCode'], expected_response['statusCode'])
        self.assertEqual(response['headers'], expected_response['headers'])
        self.assertEqual(response['body'], expected_response['body'])
