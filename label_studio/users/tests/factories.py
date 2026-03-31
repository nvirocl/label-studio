import factory
from organizations.models import OrganizationMember, OrganizationMemberRole
from users.models import User


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.LazyAttribute(lambda u: u.email.split('@')[0])
    password = factory.Faker('password')

    class Meta:
        model = User

    class Params:
        role = OrganizationMemberRole.ANNOTATOR

    @factory.post_generation
    def active_organization(self, create, extracted, **kwargs):
        if not create or not extracted:
            return
        self.active_organization = extracted
        self.save(update_fields=['active_organization'])
        role = kwargs.get('role', self.role if hasattr(self, 'role') else OrganizationMemberRole.ANNOTATOR)
        OrganizationMember.objects.create(user=self, organization=extracted, role=role)
