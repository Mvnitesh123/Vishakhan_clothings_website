from django_ratelimit.decorators import ratelimit
from functools import wraps

def standard_rate_limit(rate='100/15m', block=True):
    """
    Standard rate limit decorator for views.
    Limits by IP by default.
    - rate: e.g. '100/15m' (100 requests per 15 minutes)
    - block: True means it will raise a Ratelimited exception or use RATELIMIT_VIEW 
             (which we configured in settings).
    """
    def decorator(view_func):
        @ratelimit(key='ip', rate=rate, block=block)
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def login_rate_limit(rate='5/m', block=True):
    """
    Stricter rate limit for sensitive endpoints like login/signup to prevent brute force.
    """
    def decorator(view_func):
        @ratelimit(key='ip', rate=rate, block=block)
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
