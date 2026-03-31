from core.permissions import user_has_permission
from rest_framework.permissions import SAFE_METHODS, BasePermission


class HasObjectPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.has_permission(request.user)


class MemberHasOwnerPermission(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method not in SAFE_METHODS and not request.user.own_organization:
            return False

        return obj.has_permission(request.user)


class HasRolePermission(BasePermission):
    """Check that the requesting user's role grants the required permission.

    The view must define ``permission_required`` (a string or a
    ``ViewClassPermission`` instance).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        permission_required = getattr(view, 'permission_required', None)
        if permission_required is None:
            return True

        # ViewClassPermission: look up by HTTP method
        if hasattr(permission_required, 'GET'):
            permission_name = getattr(permission_required, request.method, None)
            if permission_name is None:
                return True
        else:
            permission_name = permission_required

        return user_has_permission(request.user, permission_name)
