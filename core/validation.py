import json
from functools import wraps
from django.http import JsonResponse
from pydantic import ValidationError

def validate_request(query_schema=None, body_schema=None):
    """
    Decorator to validate incoming request data using Pydantic schemas.
    - query_schema: Pydantic model for request.GET
    - body_schema: Pydantic model for request.body (JSON)
    
    If validation passes, the validated data is attached to:
    - request.validated_query
    - request.validated_body
    
    If validation fails, returns a 400 JSON response with error details.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Validate Query Params
            if query_schema:
                try:
                    # Convert QueryDict to a standard dict for validation
                    query_dict = request.GET.dict()
                    validated_query = query_schema(**query_dict)
                    request.validated_query = validated_query
                except ValidationError as e:
                    return JsonResponse({
                        "error": "Invalid query parameters",
                        "details": e.errors()
                    }, status=400)
            
            # Validate JSON Body
            if body_schema:
                try:
                    if request.body:
                        body_data = json.loads(request.body)
                    else:
                        body_data = {}
                    
                    validated_body = body_schema(**body_data)
                    request.validated_body = validated_body
                except json.JSONDecodeError:
                    return JsonResponse({
                        "error": "Malformed JSON payload."
                    }, status=400)
                except ValidationError as e:
                    return JsonResponse({
                        "error": "Invalid request body",
                        "details": e.errors()
                    }, status=400)
                    
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
