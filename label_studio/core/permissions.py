"""This file and its contents are licensed under the Apache License 2.0. Please see the included NOTICE for copyright information and LICENSE for a copy of the license."""

import logging  # noqa: I001
from typing import Optional

from pydantic import BaseModel, ConfigDict

import rules

logger = logging.getLogger(__name__)


class AllPermissions(BaseModel):
    model_config = ConfigDict(protected_namespaces=('__.*__', '_.*'))

    organizations_create: str = 'organizations.create'
    organizations_view: str = 'organizations.view'
    organizations_change: str = 'organizations.change'
    organizations_delete: str = 'organizations.delete'
    organizations_invite: str = 'organizations.invite'
    projects_create: str = 'projects.create'
    projects_view: str = 'projects.view'
    projects_change: str = 'projects.change'
    projects_delete: str = 'projects.delete'
    projects_reset_cache: str = 'projects.reset_cache'
    tasks_create: str = 'tasks.create'
    tasks_view: str = 'tasks.view'
    tasks_change: str = 'tasks.change'
    tasks_delete: str = 'tasks.delete'
    views_reset: str = 'views.reset'
    annotations_create: str = 'annotations.create'
    annotations_view: str = 'annotations.view'
    annotations_change: str = 'annotations.change'
    annotations_delete: str = 'annotations.delete'
    actions_perform: str = 'actions.perform'
    predictions_any: str = 'predictions.any'
    avatar_any: str = 'avatar.any'
    labels_create: str = 'labels.create'
    labels_view: str = 'labels.view'
    labels_change: str = 'labels.change'
    labels_delete: str = 'labels.delete'
    models_create: str = 'models.create'
    models_view: str = 'models.view'
    models_change: str = 'models.change'
    models_delete: str = 'models.delete'
    model_provider_connection_create: str = 'model_provider_connection.create'
    model_provider_connection_view: str = 'model_provider_connection.view'
    model_provider_connection_change: str = 'model_provider_connection.change'
    model_provider_connection_delete: str = 'model_provider_connection.delete'
    webhooks_view: str = 'webhooks.view'
    webhooks_change: str = 'webhooks.change'
    users_token_any: str = 'users.token.any'

    storages_view: str = 'storages.view'
    storages_change: str = 'storages.change'
    storages_sync: str = 'storages.sync'

    views_view: str = 'views.view'
    views_create: str = 'views.create'
    views_change: str = 'views.change'
    views_delete: str = 'views.delete'


all_permissions = AllPermissions()


class ViewClassPermission(BaseModel):
    GET: Optional[str] = None
    PATCH: Optional[str] = None
    PUT: Optional[str] = None
    DELETE: Optional[str] = None
    POST: Optional[str] = None


# Role-to-permission mapping.
# Each role has a set of allowed permissions.
# Owner: all permissions
# Manager: can manage projects, tasks, annotations, storages, models, webhooks, views and invite users
# Reviewer: can view projects/tasks, create/view/change annotations, perform actions, view models
# Annotator: can view projects/tasks, create annotations, manage own avatar/token
ROLE_PERMISSIONS = {
    'owner': {perm for _, perm in all_permissions},
    'manager': {
        all_permissions.organizations_view,
        all_permissions.organizations_invite,
        all_permissions.projects_create,
        all_permissions.projects_view,
        all_permissions.projects_change,
        all_permissions.projects_delete,
        all_permissions.projects_reset_cache,
        all_permissions.tasks_create,
        all_permissions.tasks_view,
        all_permissions.tasks_change,
        all_permissions.tasks_delete,
        all_permissions.annotations_create,
        all_permissions.annotations_view,
        all_permissions.annotations_change,
        all_permissions.annotations_delete,
        all_permissions.actions_perform,
        all_permissions.predictions_any,
        all_permissions.avatar_any,
        all_permissions.labels_create,
        all_permissions.labels_view,
        all_permissions.labels_change,
        all_permissions.labels_delete,
        all_permissions.models_create,
        all_permissions.models_view,
        all_permissions.models_change,
        all_permissions.models_delete,
        all_permissions.model_provider_connection_create,
        all_permissions.model_provider_connection_view,
        all_permissions.model_provider_connection_change,
        all_permissions.model_provider_connection_delete,
        all_permissions.webhooks_view,
        all_permissions.webhooks_change,
        all_permissions.users_token_any,
        all_permissions.storages_view,
        all_permissions.storages_change,
        all_permissions.storages_sync,
        all_permissions.views_reset,
        all_permissions.views_view,
        all_permissions.views_create,
        all_permissions.views_change,
        all_permissions.views_delete,
    },
    'reviewer': {
        all_permissions.organizations_view,
        all_permissions.projects_view,
        all_permissions.tasks_view,
        all_permissions.annotations_create,
        all_permissions.annotations_view,
        all_permissions.annotations_change,
        all_permissions.annotations_delete,
        all_permissions.actions_perform,
        all_permissions.predictions_any,
        all_permissions.avatar_any,
        all_permissions.labels_view,
        all_permissions.models_view,
        all_permissions.model_provider_connection_view,
        all_permissions.users_token_any,
        all_permissions.views_view,
        all_permissions.views_create,
        all_permissions.views_change,
        all_permissions.views_delete,
    },
    'annotator': {
        # Same as manager minus: organizations_invite, projects_create,
        # projects_change, projects_delete, projects_reset_cache,
        # tasks_create, tasks_change, tasks_delete, views_delete
        all_permissions.organizations_view,
        all_permissions.projects_view,
        all_permissions.tasks_view,
        all_permissions.annotations_create,
        all_permissions.annotations_view,
        all_permissions.annotations_change,
        all_permissions.annotations_delete,
        all_permissions.actions_perform,
        all_permissions.predictions_any,
        all_permissions.avatar_any,
        all_permissions.labels_create,
        all_permissions.labels_view,
        all_permissions.labels_change,
        all_permissions.labels_delete,
        all_permissions.models_create,
        all_permissions.models_view,
        all_permissions.models_change,
        all_permissions.models_delete,
        all_permissions.model_provider_connection_create,
        all_permissions.model_provider_connection_view,
        all_permissions.model_provider_connection_change,
        all_permissions.model_provider_connection_delete,
        all_permissions.webhooks_view,
        all_permissions.webhooks_change,
        all_permissions.users_token_any,
        all_permissions.storages_view,
        all_permissions.storages_change,
        all_permissions.storages_sync,
        all_permissions.views_reset,
        all_permissions.views_view,
        all_permissions.views_create,
        all_permissions.views_change,
    },
}


def get_user_role_for_organization(user):
    """Get the user's role in their active organization.

    Returns the role string or None if the user has no active organization membership.
    """
    if not user.is_authenticated or not user.active_organization_id:
        return None

    from organizations.models import OrganizationMember

    try:
        membership = OrganizationMember.objects.get(
            user=user,
            organization_id=user.active_organization_id,
            deleted_at__isnull=True,
        )
        return membership.role
    except OrganizationMember.DoesNotExist:
        return None


def get_permissions_for_role(role):
    """Return the set of permission strings allowed for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def user_has_permission(user, permission_name):
    """Check if the user has a specific permission based on their role."""
    role = get_user_role_for_organization(user)
    if role is None:
        return False
    return permission_name in get_permissions_for_role(role)


def make_perm(name, pred, overwrite=False):
    if rules.perm_exists(name):
        if overwrite:
            rules.remove_perm(name)
        else:
            return
    rules.add_perm(name, pred)


for _, permission_name in all_permissions:
    make_perm(permission_name, rules.is_authenticated)
