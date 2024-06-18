from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from django.db import connection

class JWTAuthentication(BaseJWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token['user_id']

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
                'is_authenticated': True

            }
        else:
            raise InvalidToken('User not found or token is invalid.')

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, validated_token).
        """
        raw_token = self.get_raw_token(request)
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return user, validated_token

