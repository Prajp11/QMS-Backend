"""
Custom authentication class that allows requests to proceed even with invalid tokens
This is useful for endpoints that are public (AllowAny) but may receive expired tokens
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class OptionalJWTAuthentication(JWTAuthentication):
    """
    JWT Authentication that doesn't fail on invalid tokens
    If token is valid, authenticates the user
    If token is invalid or missing, returns None (allows anonymous access)
    This allows views with AllowAny permission to work even with expired tokens
    """
    
    def authenticate(self, request):
        try:
            return super().authenticate(request)
        except (InvalidToken, TokenError):
            # Token is invalid/expired, but don't fail - return None to allow anonymous
            return None
