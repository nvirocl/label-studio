import pytest
from core.role_permissions import ROLE_PERMISSIONS, role_has_permission, user_has_permission
from organizations.models import OrganizationMember, OrganizationMemberRole
from organizations.tests.factories import OrganizationFactory
from users.tests.factories import UserFactory


class TestRolePermissionsMapping:
    """Test the role-to-permission mapping."""

    def test_owner_has_all_permissions(self):
        owner_perms = ROLE_PERMISSIONS[OrganizationMemberRole.OWNER]
        assert 'organizations.create' in owner_perms
        assert 'organizations.delete' in owner_perms
        assert 'projects.create' in owner_perms
        assert 'tasks.create' in owner_perms
        assert 'annotations.create' in owner_perms

    def test_admin_cannot_delete_org(self):
        admin_perms = ROLE_PERMISSIONS[OrganizationMemberRole.ADMINISTRATOR]
        assert 'organizations.delete' not in admin_perms
        assert 'organizations.create' not in admin_perms
        assert 'organizations.view' in admin_perms
        assert 'organizations.change' in admin_perms

    def test_manager_has_project_permissions(self):
        manager_perms = ROLE_PERMISSIONS[OrganizationMemberRole.MANAGER]
        assert 'projects.create' in manager_perms
        assert 'projects.change' in manager_perms
        assert 'projects.delete' in manager_perms
        assert 'tasks.create' in manager_perms
        assert 'annotations.create' in manager_perms

    def test_manager_no_org_permissions(self):
        manager_perms = ROLE_PERMISSIONS[OrganizationMemberRole.MANAGER]
        assert 'organizations.view' not in manager_perms
        assert 'organizations.change' not in manager_perms
        assert 'organizations.invite' not in manager_perms

    def test_reviewer_limited_permissions(self):
        reviewer_perms = ROLE_PERMISSIONS[OrganizationMemberRole.REVIEWER]
        assert 'annotations.view' in reviewer_perms
        assert 'annotations.change' in reviewer_perms
        assert 'tasks.view' in reviewer_perms
        assert 'tasks.change' in reviewer_perms
        assert 'projects.create' not in reviewer_perms
        assert 'tasks.create' not in reviewer_perms

    def test_annotator_minimal_permissions(self):
        annotator_perms = ROLE_PERMISSIONS[OrganizationMemberRole.ANNOTATOR]
        assert 'annotations.create' in annotator_perms
        assert 'annotations.view' in annotator_perms
        assert 'tasks.view' in annotator_perms
        assert 'projects.view' in annotator_perms
        assert 'views.view' in annotator_perms
        assert 'views.create' in annotator_perms
        assert 'views.change' in annotator_perms
        assert 'views.delete' in annotator_perms
        assert 'projects.create' not in annotator_perms
        assert 'tasks.create' not in annotator_perms
        assert 'tasks.change' not in annotator_perms

    def test_reviewer_has_projects_view(self):
        reviewer_perms = ROLE_PERMISSIONS[OrganizationMemberRole.REVIEWER]
        assert 'projects.view' in reviewer_perms
        assert 'projects.create' not in reviewer_perms

    def test_deactivated_no_permissions(self):
        assert OrganizationMemberRole.DEACTIVATED not in ROLE_PERMISSIONS

    def test_not_activated_no_permissions(self):
        assert OrganizationMemberRole.NOT_ACTIVATED not in ROLE_PERMISSIONS

    def test_role_has_permission_function(self):
        assert role_has_permission(OrganizationMemberRole.OWNER, 'projects.create')
        assert role_has_permission(OrganizationMemberRole.ANNOTATOR, 'annotations.create')
        assert not role_has_permission(OrganizationMemberRole.ANNOTATOR, 'projects.create')
        assert not role_has_permission(OrganizationMemberRole.DEACTIVATED, 'annotations.view')
        assert not role_has_permission('XX', 'annotations.view')


@pytest.mark.django_db
class TestUserHasPermission:
    def test_owner_has_permission(self):
        org = OrganizationFactory(created_by__username='owner')
        owner = org.created_by
        assert user_has_permission(owner, 'projects.create')
        assert user_has_permission(owner, 'organizations.delete')

    def test_annotator_limited_permission(self):
        org = OrganizationFactory(created_by__username='owner')
        user = UserFactory(username='annotator', active_organization=org)
        assert user_has_permission(user, 'annotations.create')
        assert not user_has_permission(user, 'projects.create')

    def test_nonmember_no_permission(self):
        org = OrganizationFactory(created_by__username='owner')
        user = UserFactory(username='outsider')
        assert not user_has_permission(user, 'annotations.create', organization=org)

    def test_deactivated_no_permission(self):
        org = OrganizationFactory(created_by__username='owner')
        user = UserFactory(username='deactivated', active_organization=org)
        OrganizationMember.objects.filter(user=user, organization=org).update(
            role=OrganizationMemberRole.DEACTIVATED
        )
        assert not user_has_permission(user, 'annotations.create')
