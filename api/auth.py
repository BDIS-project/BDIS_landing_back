from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.core.cache import cache
from django.db import connection

class JWTAuthentication(BaseJWTAuthentication):
    token_prefix = 'blacklisted_token_'  # Prefix for cache key

    def get_raw_token(self, request):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return None

        parts = auth_header.split()
        if parts[0].lower() != 'bearer':
            return None
        if len(parts) == 1:
            return None
        elif len(parts) > 2:
            raise AuthenticationFailed('Invalid token header')

        return parts[1]

    def get_user(self, validated_token):
        user_id = validated_token['user_id'] 

        # Query the database to retrieve user based on user_id
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, Employee.empl_role "
                "FROM User_Table "
                "INNER JOIN Employee ON Employee.id_employee = User_Table.id_employee "
                "WHERE user_id = %s",
                [user_id]
            )
            user = cursor.fetchone()

        if user:
            user_id, username, role = user
            return {
                'id': user_id,
                'username': username,
                'role': role,
                'is_authenticated': True
            }
        else:
            raise InvalidToken('User not found or token is invalid.')

    def authenticate(self, request):
        raw_token = self.get_raw_token(request)
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)

        # Check if token is blacklisted
        if self.token_is_blacklisted(raw_token):
            raise AuthenticationFailed('Token is blacklisted')
        
        user = self.get_user(validated_token)
        return user, validated_token
    
    def token_is_blacklisted(self, token):
        return cache.get(self.token_prefix + token) is not None

    def blacklist_token(self, token):
        cache.set(self.token_prefix + token, True, timeout=None)  # Store indefinitely in cache