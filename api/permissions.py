from rest_framework.permissions import BasePermission
import logging

class IsCashier(BasePermission):
    def has_permission(self, request, view):
        logging.warning(request)
        return request.user.role == 'Cashier'

class IsManager(BasePermission):
    def has_permission(self, request, view):
        logging.warning(request)
        return request.user.role == 'Manager'
        #return request.user and request.user.groups.filter(name='Manager').exists()