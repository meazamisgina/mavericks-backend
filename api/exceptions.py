from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    # If the user is not authenticated (401), send a friendly JSON response
    if response is not None and response.status_code == status.HTTP_401_UNAUTHORIZED:
        response.data = {
            'error': 'Authentication Required',
            'message': 'Please log in to continue.',
        }
    
    return response