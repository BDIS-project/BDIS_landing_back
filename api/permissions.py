from rest_framework.permissions import BasePermission
from django.contrib.auth.models import AnonymousUser
import logging

class IsAuthenticated(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return not isinstance(request.user, AnonymousUser)
    
class AllowAny(BasePermission):
    """
    Allow any access.
    This isn't strictly required, since you could use an empty
    permission_classes list, but it's useful because it makes the intention
    more explicit.
    """

    def has_permission(self, request, view):
        return True
    
class IsCashier(BasePermission):
    """
    Allows access only to users with the 'Cashier' role.
    """
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            logging.warning("Anonymous user trying to access a restricted view")
            return False

        logging.warning(request)
        return request.user and request.user['role'] == 'Cashier'


class IsManager(BasePermission):
    """
    Allows access only to users with the 'Manager' role.
    """
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            logging.warning("Anonymous user trying to access a restricted view")
            return False

        logging.warning(request)
        return request.user and request.user['role'] == 'Manager'

class IsCashierOrManager(BasePermission):
    """
    Allows access only to users with the 'Cashier' or 'Manager' role.
    """
    def has_permission(self, request, view):
        if isinstance(request.user, AnonymousUser):
            logging.warning("Anonymous user trying to access a restricted view")
            return False

        logging.warning(request)
        return request.user and (request.user['role'] == 'Manager' or request.user['role'] == 'Cashier')
    