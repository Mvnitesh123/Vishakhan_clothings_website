from django.http import JsonResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

def ratelimited_error_view(request, exception=None):
    """
    Global view that django-ratelimit uses when a user exceeds the limit.
    Configured in settings.py with RATELIMIT_VIEW = 'core.middleware.ratelimited_error_view'
    """
    logger.warning(f"Rate limit exceeded for IP: {request.META.get('REMOTE_ADDR')}")
    
    # We can inspect if the request expects JSON or HTML
    if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
        response = JsonResponse({
            "error": "Too Many Requests",
            "message": "You have exceeded your request limit. Please try again later."
        }, status=429)
    else:
        # Fallback to JSON or we could render a template
        response = JsonResponse({
            "error": "Too Many Requests",
            "message": "You have exceeded your request limit. Please try again later."
        }, status=429)
    
    # Add Retry-After header (e.g. 60 seconds)
    response['Retry-After'] = '60'
    return response

class RateLimitMiddleware:
    """
    Middleware to catch ratelimit exceptions if the custom view fails or 
    to add additional global ratelimiting logic if needed.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response
