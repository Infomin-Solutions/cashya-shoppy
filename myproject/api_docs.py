import os
import json
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def api_docs(request):
    """
    Serve the Postman collection as downloadable JSON when accessing /api/docs/
    """
    try:
        # Path to the Postman collection file
        collection_path = os.path.join(
            settings.BASE_DIR, 'Cashya_Shoppy_API.postman_collection.json')

        # Check if file exists
        if not os.path.exists(collection_path):
            return JsonResponse({
                'error': 'API documentation not found',
                'message': 'Postman collection file is missing'
            }, status=404)

        # Read the collection file
        with open(collection_path, 'r', encoding='utf-8') as file:
            collection_data = json.load(file)

        # Create response with proper headers for download
        response = HttpResponse(
            json.dumps(collection_data, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="Cashya_Shoppy_API.postman_collection.json"'
        response['Content-Description'] = 'Postman API Collection'

        return response

    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid collection file',
            'message': 'The Postman collection file is corrupted'
        }, status=500)
    except Exception as e:
        return JsonResponse({
            'error': 'Server error',
            'message': str(e)
        }, status=500)
