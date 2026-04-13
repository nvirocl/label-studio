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
    """Check that the user has the required role-based permission for the view action.

    Works with ViewClassPermission to determine which permission string
    is required for the current HTTP method, then checks if the user's role
    grants that permission.
    """

    def has_permission(self, request, view):
        from core.role_permissions import user_has_permission

        if not request.user or not request.user.is_authenticated:
            return False

        permission_required = getattr(view, 'permission_required', None)
        if permission_required is None:
            return True

        # If it's a ViewClassPermission (Pydantic model), get method-specific permission
        if hasattr(permission_required, 'model_fields'):
            perm = getattr(permission_required, request.method, None)
            if perm is None:
                return True
            return user_has_permission(request.user, perm)

        # If it's a plain string, check directly
        if isinstance(permission_required, str):
            return user_has_permission(request.user, permission_required)

        return True


class HasMinimumRolePermission(BasePermission):
    """Check that the user has at least a minimum role.

    Set `minimum_role` on the view to use this permission class.
    Example:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasMinimumRolePermission]
            minimum_role = OrganizationMemberRole.MANAGER
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        minimum_role = getattr(view, 'minimum_role', None)
        if minimum_role is None:
            return True

        org = request.user.active_organization
        if org is None:
            return False

        return org.user_has_role_at_least(request.user, minimum_role)
