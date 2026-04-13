from django.utils.functional import cached_property


class OrganizationMixin:
    @cached_property
    def active_members(self):
        from organizations.models import OrganizationMemberRole

        return self.members.exclude(
            role__in=[OrganizationMemberRole.DEACTIVATED, OrganizationMemberRole.NOT_ACTIVATED]
        )


class OrganizationMemberMixin:
    def has_permission(self, user):
        from organizations.models import OrganizationMemberRole

        if user.active_organization_id == self.organization_id:
            # Deactivated / not-activated members have no access
            if hasattr(self, 'role') and self.role in (
                OrganizationMemberRole.DEACTIVATED,
                OrganizationMemberRole.NOT_ACTIVATED,
            ):
                return False
            return True
        return False
