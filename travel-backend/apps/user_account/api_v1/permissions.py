from rest_framework.permissions import BasePermission


class CanManageEnquiries(BasePermission):
    """
    Permission class for enquiry management.
    Allows access if user has can_manage_enquiries permission or is admin/superuser.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers and admins have full access
        if request.user.is_superuser or request.user.is_admin:
            return True
        
        # Check if user has enquiry management permission
        return request.user.can_manage_enquiries


class CanManageAdministration(BasePermission):
    """
    Permission class for administration management.
    Allows access if user has can_manage_administration permission or is admin/superuser.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers and admins have full access
        if request.user.is_superuser or request.user.is_admin:
            return True
        
        # Check if user has administration management permission
        return request.user.can_manage_administration


class IsAdminOrHasBothPermissions(BasePermission):
    """
    Permission class that grants access if user is admin/superuser 
    OR has both enquiry and administration permissions.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Superusers and admins have full access
        if request.user.is_superuser or request.user.is_admin:
            return True
        
        # Check if user has both permissions
        return (request.user.can_manage_enquiries and 
                request.user.can_manage_administration)
