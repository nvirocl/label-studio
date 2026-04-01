"""Role-based permission mapping for Label Studio.

This module defines what each role can do. It maps role codes to sets of
permission strings defined in core.permissions.AllPermissions.

Roles hierarchy (highest to lowest):
    Owner > Administrator > Manager > Reviewer > Annotator
"""

from organizations.models import OrganizationMemberRole

# Permissions available to each role.
# Higher roles inherit all permissions from lower roles.
ROLE_PERMISSIONS = {
    OrganizationMemberRole.ANNOTATOR: {
        'annotations.create',
        'annotations.view',
        'annotations.change',
        'annotations.delete',
        'tasks.view',
        'predictions.any',
        'avatar.any',
        'labels.view',
        'views.view',
        'users.token.any',
    },
    OrganizationMemberRole.REVIEWER: {
        # Inherits all annotator permissions plus:
        'annotations.create',
        'annotations.view',
        'annotations.change',
        'annotations.delete',
        'tasks.view',
        'tasks.change',
        'predictions.any',
        'avatar.any',
        'labels.view',
        'views.view',
        'views.create',
        'views.change',
        'users.token.any',
    },
    OrganizationMemberRole.MANAGER: {
        # Full project-level access
        'projects.create',
        'projects.view',
        'projects.change',
        'projects.delete',
        'projects.reset_cache',
        'tasks.create',
        'tasks.view',
        'tasks.change',
        'tasks.delete',
        'annotations.create',
        'annotations.view',
        'annotations.change',
        'annotations.delete',
        'actions.perform',
        'predictions.any',
        'avatar.any',
        'labels.create',
        'labels.view',
        'labels.change',
        'labels.delete',
        'models.create',
        'models.view',
        'models.change',
        'models.delete',
        'webhooks.view',
        'webhooks.change',
        'storages.view',
        'storages.change',
        'storages.sync',
        'views.view',
        'views.create',
        'views.change',
        'views.delete',
        'views.reset',
        'users.token.any',
    },
    OrganizationMemberRole.ADMINISTRATOR: {
        # All manager permissions plus organization management
        'organizations.view',
        'organizations.change',
        'organizations.invite',
        'projects.create',
        'projects.view',
        'projects.change',
        'projects.delete',
        'projects.reset_cache',
        'tasks.create',
        'tasks.view',
        'tasks.change',
        'tasks.delete',
        'annotations.create',
        'annotations.view',
        'annotations.change',
        'annotations.delete',
        'actions.perform',
        'predictions.any',
        'avatar.any',
        'labels.create',
        'labels.view',
        'labels.change',
        'labels.delete',
        'models.create',
        'models.view',
        'models.change',
        'models.delete',
        'model_provider_connection.create',
        'model_provider_connection.view',
        'model_provider_connection.change',
        'model_provider_connection.delete',
        'webhooks.view',
        'webhooks.change',
        'storages.view',
        'storages.change',
        'storages.sync',
        'views.view',
        'views.create',
        'views.change',
        'views.delete',
        'views.reset',
        'users.token.any',
    },
    OrganizationMemberRole.OWNER: {
        # Full access to everything
        'organizations.create',
        'organizations.view',
        'organizations.change',
        'organizations.delete',
        'organizations.invite',
        'projects.create',
        'projects.view',
        'projects.change',
        'projects.delete',
        'projects.reset_cache',
        'tasks.create',
        'tasks.view',
        'tasks.change',
        'tasks.delete',
        'annotations.create',
        'annotations.view',
        'annotations.change',
        'annotations.delete',
        'actions.perform',
        'predictions.any',
        'avatar.any',
        'labels.create',
        'labels.view',
        'labels.change',
        'labels.delete',
        'models.create',
        'models.view',
        'models.change',
        'models.delete',
        'model_provider_connection.create',
        'model_provider_connection.view',
        'model_provider_connection.change',
        'model_provider_connection.delete',
        'webhooks.view',
        'webhooks.change',
        'storages.view',
        'storages.change',
        'storages.sync',
        'views.view',
        'views.create',
        'views.change',
        'views.delete',
        'views.reset',
        'users.token.any',
    },
}


def role_has_permission(role, permission_name):
    """Check if a given role has a specific permission."""
    role_perms = ROLE_PERMISSIONS.get(role)
    if role_perms is None:
        return False
    return permission_name in role_perms


def get_user_role_for_organization(user, organization=None):
    """Get the role of a user in an organization.

    If organization is None, uses the user's active_organization.
    Returns None if the user is not a member.
    """
    from organizations.models import OrganizationMember

    if organization is None:
        organization = user.active_organization
    if organization is None:
        return None

    try:
        member = OrganizationMember.objects.get(
            user=user, organization=organization, deleted_at__isnull=True
        )
        return member.role
    except OrganizationMember.DoesNotExist:
        return None


def user_has_permission(user, permission_name, organization=None):
    """Check if a user has a specific permission in the given organization."""
    role = get_user_role_for_organization(user, organization)
    if role is None:
        return False
    return role_has_permission(role, permission_name)
