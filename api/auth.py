from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from django.db import connection

class JWTAuthentication(BaseJWTAuthentication):
    def get_raw_token(self, request):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            raise AuthenticationFailed('Authorization header not found')

        parts = auth_header.split()
        if parts[0].lower() != 'Bearer':
            raise AuthenticationFailed('Invalid token header')
        if len(parts) == 1:
            raise AuthenticationFailed('Token not found')
        elif len(parts) > 2:
            raise AuthenticationFailed('Invalid token header')

        return parts[1]

    def get_user(self, validated_token):
        user_id = validated_token['user_id']  # Adjust this according to your token structure

        # Query your database to retrieve the user based on user_id
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
            }
        else:
            raise InvalidToken('User not found or token is invalid.')

    def authenticate(self, request):
        raw_token = self.get_raw_token(request)
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return user, validated_token