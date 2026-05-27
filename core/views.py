from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from core.rate_limit import standard_rate_limit, login_rate_limit
from core.validation import validate_request
from core.schemas import UserSignupSchema, ProductQuerySchema

@require_http_methods(["GET"])
@standard_rate_limit(rate='100/15m')
@validate_request(query_schema=ProductQuerySchema)
def sample_product_list_view(request):
    """
    Example view demonstrating GET validation and standard rate limiting.
    Allows 100 requests per 15 minutes per IP.
    """
    # The validated data is available as request.validated_query
    category = request.validated_query.category
    min_price = request.validated_query.min_price
    max_price = request.validated_query.max_price
    
    # Normally you would query the database here
    # e.g., Product.objects.filter(...)
    
    return JsonResponse({
        "status": "success",
        "data": f"Fetched products for category: {category}, min_price: {min_price}, max_price: {max_price}"
    })


@csrf_exempt
@require_http_methods(["POST"])
@login_rate_limit(rate='5/m')
@validate_request(body_schema=UserSignupSchema)
def sample_signup_view(request):
    """
    Example view demonstrating POST JSON body validation and strict rate limiting.
    Allows 5 requests per minute per IP to prevent spam/brute-force.
    """
    # The validated data is available as request.validated_body
    username = request.validated_body.username
    email = request.validated_body.email
    
    # We do not log or return the password in production.
    
    return JsonResponse({
        "status": "success",
        "message": f"User {username} with email {email} registered successfully!"
    })
