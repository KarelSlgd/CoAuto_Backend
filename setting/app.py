headers_open = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Methods': 'GET,PUT,POST,DELETE,OPTIONS',
}


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'headers': headers_open,
        'body': ''
    }