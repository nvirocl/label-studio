from urllib.parse import urlencode

from organizations.models import OrganizationMember, OrganizationMemberRole
from organizations.tests.factories import OrganizationFactory
from rest_framework import status
from rest_framework.test import APITestCase
from users.tests.factories import UserFactory


class TestOrganizationMemberRole(APITestCase):
    """Tests for the OrganizationMemberRole model and hierarchy."""

    def test_role_hierarchy(self):
        assert OrganizationMemberRole.has_at_least('OW', 'OW')
        assert OrganizationMemberRole.has_at_least('OW', 'AD')
        assert OrganizationMemberRole.has_at_least('OW', 'MA')
        assert OrganizationMemberRole.has_at_least('OW', 'RE')
        assert OrganizationMemberRole.has_at_least('OW', 'AN')

        assert OrganizationMemberRole.has_at_least('AD', 'AD')
        assert OrganizationMemberRole.has_at_least('AD', 'MA')
        assert not OrganizationMemberRole.has_at_least('AD', 'OW')

        assert OrganizationMemberRole.has_at_least('MA', 'MA')
        assert not OrganizationMemberRole.has_at_least('MA', 'AD')

        assert OrganizationMemberRole.has_at_least('RE', 'RE')
        assert OrganizationMemberRole.has_at_least('RE', 'AN')
        assert not OrganizationMemberRole.has_at_least('RE', 'MA')

        assert OrganizationMemberRole.has_at_least('AN', 'AN')
        assert not OrganizationMemberRole.has_at_least('AN', 'RE')

        assert not OrganizationMemberRole.has_at_least('DI', 'AN')
        assert not OrganizationMemberRole.has_at_least('NO', 'AN')


class TestOrganizationMemberModel(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by

    def test_owner_role_set_on_creation(self):
        """Organization creator should get Owner role."""
        member = OrganizationMember.objects.get(user=self.owner, organization=self.organization)
        assert member.role == OrganizationMemberRole.OWNER

    def test_is_owner_property(self):
        member = OrganizationMember.objects.get(user=self.owner, organization=self.organization)
        assert member.is_owner is True

    def test_default_role_is_annotator(self):
        """New members should default to Annotator role."""
        user = UserFactory(username='new_user', active_organization=self.organization)
        member = OrganizationMember.objects.get(user=user, organization=self.organization)
        assert member.role == OrganizationMemberRole.ANNOTATOR

    def test_add_user_with_role(self):
        """Organization.add_user should accept role parameter."""
        user = UserFactory(username='manager_user')
        om = self.organization.add_user(user, role=OrganizationMemberRole.MANAGER)
        assert om.role == OrganizationMemberRole.MANAGER

    def test_has_role_at_least(self):
        member = OrganizationMember.objects.get(user=self.owner, organization=self.organization)
        assert member.has_role_at_least(OrganizationMemberRole.OWNER)
        assert member.has_role_at_least(OrganizationMemberRole.ADMINISTRATOR)
        assert member.has_role_at_least(OrganizationMemberRole.ANNOTATOR)


class TestOrganizationHelpers(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by

    def test_get_user_role(self):
        assert self.organization.get_user_role(self.owner) == OrganizationMemberRole.OWNER

    def test_get_user_role_nonmember(self):
        user = UserFactory(username='outsider')
        assert self.organization.get_user_role(user) is None

    def test_user_has_role_at_least(self):
        assert self.organization.user_has_role_at_least(self.owner, OrganizationMemberRole.ADMINISTRATOR)
        assert self.organization.user_has_role_at_least(self.owner, OrganizationMemberRole.OWNER)

    def test_user_has_role_at_least_nonmember(self):
        user = UserFactory(username='outsider')
        assert not self.organization.user_has_role_at_least(user, OrganizationMemberRole.ANNOTATOR)


class TestRoleUpdateAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by
        cls.admin_user = UserFactory(username='admin_user', active_organization=cls.organization)
        cls.manager_user = UserFactory(username='manager_user', active_organization=cls.organization)
        cls.annotator_user = UserFactory(username='annotator_user', active_organization=cls.organization)

        # Set roles
        OrganizationMember.objects.filter(
            user=cls.admin_user, organization=cls.organization
        ).update(role=OrganizationMemberRole.ADMINISTRATOR)
        OrganizationMember.objects.filter(
            user=cls.manager_user, organization=cls.organization
        ).update(role=OrganizationMemberRole.MANAGER)
        # annotator_user gets default Annotator role

    def get_url(self, user_pk):
        return f'/api/organizations/{self.organization.id}/memberships/{user_pk}/'

    def test_owner_can_change_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.REVIEWER},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['role'] == OrganizationMemberRole.REVIEWER

        # Verify in DB
        member = OrganizationMember.objects.get(user=self.annotator_user, organization=self.organization)
        assert member.role == OrganizationMemberRole.REVIEWER

    def test_owner_can_assign_admin(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.ADMINISTRATOR},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['role'] == OrganizationMemberRole.ADMINISTRATOR

    def test_admin_can_change_role(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.MANAGER},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['role'] == OrganizationMemberRole.MANAGER

    def test_admin_cannot_assign_admin(self):
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.ADMINISTRATOR},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_cannot_change_admin_role(self):
        """Admins cannot demote other admins - only owners can."""
        # First make another user admin
        other_admin = UserFactory(username='other_admin', active_organization=self.organization)
        OrganizationMember.objects.filter(
            user=other_admin, organization=self.organization
        ).update(role=OrganizationMemberRole.ADMINISTRATOR)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.patch(
            self.get_url(other_admin.id),
            data={'role': OrganizationMemberRole.ANNOTATOR},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_manager_cannot_change_role(self):
        self.client.force_authenticate(user=self.manager_user)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.REVIEWER},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_annotator_cannot_change_role(self):
        self.client.force_authenticate(user=self.annotator_user)
        response = self.client.patch(
            self.get_url(self.manager_user.id),
            data={'role': OrganizationMemberRole.ANNOTATOR},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_change_owner_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.get_url(self.owner.id),
            data={'role': OrganizationMemberRole.ADMINISTRATOR},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_cannot_assign_owner_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': OrganizationMemberRole.OWNER},
            format='json',
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_invalid_role_rejected(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.patch(
            self.get_url(self.annotator_user.id),
            data={'role': 'XX'},
            format='json',
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestMemberListIncludesRole(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by
        cls.annotator = UserFactory(username='annotator', active_organization=cls.organization)

    def test_list_includes_role_field(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/organizations/{self.organization.id}/memberships')
        assert response.status_code == 200

        results = response.json()['results']
        for member in results:
            assert 'role' in member

        # Owner should have OW role
        owner_member = next(m for m in results if m['user']['id'] == self.owner.id)
        assert owner_member['role'] == OrganizationMemberRole.OWNER

        # New user should have AN role
        annotator_member = next(m for m in results if m['user']['id'] == self.annotator.id)
        assert annotator_member['role'] == OrganizationMemberRole.ANNOTATOR

    def test_detail_includes_role_field(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(
            f'/api/organizations/{self.organization.id}/memberships/{self.owner.id}/'
        )
        assert response.status_code == 200
        assert response.json()['role'] == OrganizationMemberRole.OWNER


class TestOrganizationRolesAPI(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by

    def test_list_roles(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/organizations/roles')
        assert response.status_code == 200
        data = response.json()

        role_codes = [r['code'] for r in data]
        assert 'OW' in role_codes
        assert 'AD' in role_codes
        assert 'MA' in role_codes
        assert 'RE' in role_codes
        assert 'AN' in role_codes

    def test_unauthenticated_cannot_list_roles(self):
        response = self.client.get('/api/organizations/roles')
        assert response.status_code in (401, 403)


class TestRolePermissions(APITestCase):
    """Test that role-based permissions control access to resources."""

    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by
        cls.annotator = UserFactory(username='annotator', active_organization=cls.organization)
        # annotator gets default Annotator role

    def test_owner_can_view_organization(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(f'/api/organizations/{self.organization.id}')
        assert response.status_code == 200

    def test_whoami_includes_role(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get('/api/current-user/whoami')
        assert response.status_code == 200
        data = response.json()
        assert 'org_role' in data
        assert data['org_role'] == OrganizationMemberRole.OWNER

    def test_annotator_whoami_includes_role(self):
        self.client.force_authenticate(user=self.annotator)
        response = self.client.get('/api/current-user/whoami')
        assert response.status_code == 200
        data = response.json()
        assert data['org_role'] == OrganizationMemberRole.ANNOTATOR

    def test_whoami_permissions_filtered_by_role(self):
        """Annotator should have fewer permissions than owner."""
        self.client.force_authenticate(user=self.owner)
        owner_response = self.client.get('/api/current-user/whoami')
        owner_permissions = set(owner_response.json()['permissions'])

        self.client.force_authenticate(user=self.annotator)
        annotator_response = self.client.get('/api/current-user/whoami')
        annotator_permissions = set(annotator_response.json()['permissions'])

        # Annotator should have fewer permissions
        assert len(annotator_permissions) < len(owner_permissions)
        # Annotator should have annotation permissions
        assert 'annotations.create' in annotator_permissions
        assert 'annotations.view' in annotator_permissions


class TestDeactivatedUserAccess(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = OrganizationFactory(created_by__username='owner')
        cls.owner = cls.organization.created_by
        cls.deactivated_user = UserFactory(username='deactivated', active_organization=cls.organization)
        OrganizationMember.objects.filter(
            user=cls.deactivated_user, organization=cls.organization
        ).update(role=OrganizationMemberRole.DEACTIVATED)

    def test_deactivated_user_whoami_no_permissions(self):
        self.client.force_authenticate(user=self.deactivated_user)
        response = self.client.get('/api/current-user/whoami')
        assert response.status_code == 200
        data = response.json()
        assert data['org_role'] == OrganizationMemberRole.DEACTIVATED
        assert len(data['permissions']) == 0
