from organizations.models import OrganizationMember, OrganizationMemberRole


class UserMixin:
    @property
    def is_annotator(self):
        if not hasattr(self, 'active_organization') or self.active_organization is None:
            return False
        try:
            member = OrganizationMember.objects.get(
                user=self, organization=self.active_organization, deleted_at__isnull=True
            )
            return member.role == OrganizationMemberRole.ANNOTATOR
        except OrganizationMember.DoesNotExist:
            return False

    def is_project_annotator(self, project):
        return self.is_annotator

    @property
    def org_role(self):
        """Get the user's role in their active organization."""
        if not hasattr(self, 'active_organization') or self.active_organization is None:
            return None
        try:
            member = OrganizationMember.objects.get(
                user=self, organization=self.active_organization, deleted_at__isnull=True
            )
            return member.role
        except OrganizationMember.DoesNotExist:
            return None

    def has_permission(self, user):
        return OrganizationMember.objects.filter(
            user=user, organization=user.active_organization, deleted_at__isnull=True
        ).exclude(
            role__in=[OrganizationMemberRole.DEACTIVATED, OrganizationMemberRole.NOT_ACTIVATED]
        ).exists()
