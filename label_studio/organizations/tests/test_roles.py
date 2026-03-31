"""Tests for the role-based access control (RBAC) system.

Tests cover:
- Role assignment during organization creation
- Role-based permission filtering in WhoAmI
- Role update API (owner/manager restrictions)
- Permission enforcement per role (owner, manager, reviewer, annotator)
- Edge cases: last owner protection, self-role change, cross-org restrictions
"""

from urllib.parse import urlencode

from core.permissions import (
    ROLE_PERMISSIONS,
    all_permissions,
    get_permissions_for_role,
    get_user_role_for_organization,
    user_has_permission,
)
from organizations.models import OrganizationMember, OrganizationMemberRole
from organizations.tests.factories import OrganizationFactory
from projects.tests.factories import ProjectFactory
from rest_framework.test import APITestCase
from tasks.tests.factories import AnnotationFactory
from users.tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Unit tests for core/permissions helpers
# ---------------------------------------------------------------------------


class TestRolePermissionMapping(APITestCase):
    """Verify the ROLE_PERMISSIONS constant is consistent."""

    def test_owner_has_all_permissions(self):
        all_perm_names = {perm for _, perm in all_permissions}
        self.assertEqual(ROLE_PERMISSIONS['owner'], all_perm_names)

    def test_manager_has_no_org_change_or_delete(self):
        manager_perms = ROLE_PERMISSIONS['manager']
        self.assertNotIn(all_permissions.organizations_change, manager_perms)
        self.assertNotIn(all_permissions.organizations_delete, manager_perms)
        self.assertNotIn(all_permissions.organizations_create, manager_perms)

    def test_reviewer_cannot_create_projects(self):
        reviewer_perms = ROLE_PERMISSIONS['reviewer']
        self.assertNotIn(all_permissions.projects_create, reviewer_perms)
        self.assertNotIn(all_permissions.projects_change, reviewer_perms)
        self.assertNotIn(all_permissions.projects_delete, reviewer_perms)

    def test_annotator_minimal_permissions(self):
        annotator_perms = ROLE_PERMISSIONS['annotator']
        # Can view and annotate
        self.assertIn(all_permissions.projects_view, annotator_perms)
        self.assertIn(all_permissions.annotations_create, annotator_perms)
        self.assertIn(all_permissions.annotations_view, annotator_perms)
        # Cannot change or delete annotations
        self.assertNotIn(all_permissions.annotations_change, annotator_perms)
        self.assertNotIn(all_permissions.annotations_delete, annotator_perms)
        # Cannot manage projects
        self.assertNotIn(all_permissions.projects_create, annotator_perms)
        self.assertNotIn(all_permissions.projects_change, annotator_perms)

    def test_get_permissions_for_unknown_role_returns_empty(self):
        self.assertEqual(get_permissions_for_role('unknown'), set())


# ---------------------------------------------------------------------------
# Tests for role assignment during organization creation
# ---------------------------------------------------------------------------


class TestOrganizationCreatorGetsOwnerRole(APITestCase):
    def test_creator_is_owner(self):
        org = OrganizationFactory(created_by__username='creator')
        member = OrganizationMember.objects.get(user=org.created_by, organization=org)
        self.assertEqual(member.role, OrganizationMemberRole.OWNER)

    def test_added_user_defaults_to_annotator(self):
        org = OrganizationFactory(created_by__username='creator')
        new_user = UserFactory(username='new_user')
        org.add_user(new_user)
        member = OrganizationMember.objects.get(user=new_user, organization=org)
        self.assertEqual(member.role, OrganizationMemberRole.ANNOTATOR)

    def test_add_user_with_explicit_role(self):
        org = OrganizationFactory(created_by__username='creator')
        new_user = UserFactory(username='manager_user')
        org.add_user(new_user, role=OrganizationMemberRole.MANAGER)
        member = OrganizationMember.objects.get(user=new_user, organization=org)
        self.assertEqual(member.role, OrganizationMemberRole.MANAGER)


# ---------------------------------------------------------------------------
# Tests for get_user_role_for_organization / user_has_permission
# ---------------------------------------------------------------------------


class TestPermissionHelpers(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.org.created_by
        cls.owner.active_organization = cls.org
        cls.owner.save(update_fields=['active_organization'])

        cls.annotator_user = UserFactory(username='annotator', active_organization=cls.org)

    def test_owner_role_detected(self):
        self.assertEqual(get_user_role_for_organization(self.owner), OrganizationMemberRole.OWNER)

    def test_annotator_role_detected(self):
        self.assertEqual(get_user_role_for_organization(self.annotator_user), OrganizationMemberRole.ANNOTATOR)

    def test_owner_has_org_change(self):
        self.assertTrue(user_has_permission(self.owner, all_permissions.organizations_change))

    def test_annotator_lacks_org_change(self):
        self.assertFalse(user_has_permission(self.annotator_user, all_permissions.organizations_change))

    def test_annotator_can_create_annotation(self):
        self.assertTrue(user_has_permission(self.annotator_user, all_permissions.annotations_create))

    def test_no_active_org_returns_none(self):
        user = UserFactory(username='orphan')
        self.assertIsNone(get_user_role_for_organization(user))


# ---------------------------------------------------------------------------
# Tests for WhoAmI serializer returning role-filtered permissions
# ---------------------------------------------------------------------------


class TestWhoAmIPermissions(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.org.created_by
        cls.owner.active_organization = cls.org
        cls.owner.save(update_fields=['active_organization'])

        cls.annotator_user = UserFactory(username='annotator', active_organization=cls.org)
        cls.manager_user = UserFactory(username='manager', active_organization=cls.org)
        # Promote manager
        OrganizationMember.objects.filter(user=cls.manager_user, organization=cls.org).update(
            role=OrganizationMemberRole.MANAGER,
        )

    def test_owner_whoami_has_all_permissions(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/current-user/whoami')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['role'], OrganizationMemberRole.OWNER)
        all_perm_names = sorted({perm for _, perm in all_permissions})
        self.assertEqual(data['permissions'], all_perm_names)

    def test_annotator_whoami_limited_permissions(self):
        self.client.force_authenticate(user=self.annotator_user)
        response = self.client.get('/api/current-user/whoami')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['role'], OrganizationMemberRole.ANNOTATOR)
        self.assertNotIn(all_permissions.organizations_change, data['permissions'])
        self.assertIn(all_permissions.annotations_create, data['permissions'])

    def test_manager_whoami_has_project_permissions(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.get('/api/current-user/whoami')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['role'], OrganizationMemberRole.MANAGER)
        self.assertIn(all_permissions.projects_create, data['permissions'])
        self.assertNotIn(all_permissions.organizations_change, data['permissions'])


# ---------------------------------------------------------------------------
# Tests for the role field in organization member list API
# ---------------------------------------------------------------------------


class TestOrganizationMemberListWithRole(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.org.created_by
        cls.annotator_user = UserFactory(username='annotator', active_organization=cls.org)

    def test_member_list_includes_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/organizations/{self.org.id}/memberships')
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        owner_entry = next(r for r in results if r['user']['id'] == self.owner.id)
        self.assertEqual(owner_entry['role'], OrganizationMemberRole.OWNER)
        annotator_entry = next(r for r in results if r['user']['id'] == self.annotator_user.id)
        self.assertEqual(annotator_entry['role'], OrganizationMemberRole.ANNOTATOR)


# ---------------------------------------------------------------------------
# Tests for OrganizationMemberRoleAPI (PATCH role)
# ---------------------------------------------------------------------------


class TestOrganizationMemberRoleAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.org.created_by
        cls.owner.active_organization = cls.org
        cls.owner.save(update_fields=['active_organization'])

        cls.annotator_user = UserFactory(username='annotator', active_organization=cls.org)
        cls.manager_user = UserFactory(username='manager', active_organization=cls.org)
        OrganizationMember.objects.filter(user=cls.manager_user, organization=cls.org).update(
            role=OrganizationMemberRole.MANAGER,
        )

    def _role_url(self, user_pk):
        return f'/api/organizations/{self.org.id}/memberships/{user_pk}/role'

    # --- Owner operations ---

    def test_owner_can_promote_annotator_to_manager(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(self.annotator_user.pk),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], OrganizationMemberRole.MANAGER)
        # Verify in DB
        member = OrganizationMember.objects.get(user=self.annotator_user, organization=self.org)
        self.assertEqual(member.role, OrganizationMemberRole.MANAGER)

    def test_owner_can_assign_owner_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(self.annotator_user.pk),
            data={'role': OrganizationMemberRole.OWNER},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], OrganizationMemberRole.OWNER)

    def test_owner_cannot_demote_self_if_last_owner(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(self.owner.pk),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_can_demote_self_if_another_owner_exists(self):
        # First promote another user to owner
        OrganizationMember.objects.filter(user=self.manager_user, organization=self.org).update(
            role=OrganizationMemberRole.OWNER,
        )
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(self.owner.pk),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], OrganizationMemberRole.MANAGER)

    # --- Manager operations ---

    def test_manager_can_change_annotator_to_reviewer(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            self._role_url(self.annotator_user.pk),
            data={'role': OrganizationMemberRole.REVIEWER},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['role'], OrganizationMemberRole.REVIEWER)

    def test_manager_cannot_assign_owner_role(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            self._role_url(self.annotator_user.pk),
            data={'role': OrganizationMemberRole.OWNER},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    def test_manager_cannot_change_owner_role(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            self._role_url(self.owner.pk),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    # --- Annotator/Reviewer operations ---

    def test_annotator_cannot_change_roles(self):
        self.client.force_authenticate(user=self.annotator_user)
        response = self.client.patch(
            self._role_url(self.manager_user.pk),
            data={'role': OrganizationMemberRole.ANNOTATOR},
            format='json',
        )
        self.assertEqual(response.status_code, 403)

    # --- Validation ---

    def test_invalid_role_value_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(self.annotator_user.pk),
            data={'role': 'superadmin'},
            format='json',
        )
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_user_returns_404(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self._role_url(999999),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# Tests for OrganizationMember model role properties
# ---------------------------------------------------------------------------


class TestOrganizationMemberRoleProperties(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner_member = OrganizationMember.objects.get(user=cls.org.created_by, organization=cls.org)

    def test_is_owner_property(self):
        self.assertTrue(self.owner_member.is_owner)
        self.assertFalse(self.owner_member.is_manager)
        self.assertFalse(self.owner_member.is_reviewer)
        self.assertFalse(self.owner_member.is_annotator)

    def test_has_management_role(self):
        self.assertTrue(self.owner_member.has_management_role)

    def test_annotator_is_not_management(self):
        annotator = UserFactory(username='a1')
        self.org.add_user(annotator)
        member = OrganizationMember.objects.get(user=annotator, organization=self.org)
        self.assertFalse(member.has_management_role)
        self.assertTrue(member.is_annotator)


# ---------------------------------------------------------------------------
# Tests for User.is_organization_admin
# ---------------------------------------------------------------------------


class TestUserIsOrganizationAdmin(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.org.created_by
        cls.annotator_user = UserFactory(username='annotator', active_organization=cls.org)

    def test_owner_is_admin(self):
        self.assertTrue(self.owner.is_organization_admin(self.org.pk))

    def test_annotator_is_not_admin(self):
        self.assertFalse(self.annotator_user.is_organization_admin(self.org.pk))


# ---------------------------------------------------------------------------
# Tests for existing member list functionality with roles
# ---------------------------------------------------------------------------


class TestExistingMemberListWithRole(APITestCase):
    """Ensure the existing member list test scenarios still work with the role field."""

    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by
        cls.user_1 = UserFactory(username='user_1', active_organization=cls.organization)
        cls.user_2 = UserFactory(username='user_2', active_organization=cls.organization)

    def get_url(self, params=None):
        params = params or {}
        return f'/api/organizations/{self.organization.id}/memberships?{urlencode(params)}'

    def test_list_organization_members_includes_roles(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.get_url())
        assert response.status_code == 200
        results = response.json()['results']
        assert len(results) == 3

        # Owner should have owner role
        owner_entry = next(r for r in results if r['user']['id'] == self.owner.id)
        assert owner_entry['role'] == OrganizationMemberRole.OWNER

        # Other users should have annotator role (default)
        for user in [self.user_1, self.user_2]:
            entry = next(r for r in results if r['user']['id'] == user.id)
            assert entry['role'] == OrganizationMemberRole.ANNOTATOR

    def test_with_contributed_to_projects_still_works(self):
        project = ProjectFactory(created_by=self.user_1, organization=self.organization)
        AnnotationFactory(task__project=project, completed_by=self.user_1)

        self.client.force_authenticate(user=self.owner)
        response = self.client.get(self.get_url(params={'contributed_to_projects': 1}))
        assert response.status_code == 200
        results = response.json()['results']

        user_1_entry = next(r for r in results if r['user']['id'] == self.user_1.id)
        assert user_1_entry['role'] == OrganizationMemberRole.ANNOTATOR
        assert len(user_1_entry['user']['contributed_to_projects']) == 1
