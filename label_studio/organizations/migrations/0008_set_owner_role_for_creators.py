"""Data migration: set existing organization creators to the 'owner' role."""

from django.db import migrations


def set_owner_role_for_creators(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')

    for org in Organization.objects.select_related('created_by').filter(created_by__isnull=False):
        OrganizationMember.objects.filter(
            user=org.created_by,
            organization=org,
        ).update(role='owner')


def reverse_owner_role(apps, schema_editor):
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    OrganizationMember.objects.filter(role='owner').update(role='annotator')


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0007_add_role_to_organizationmember'),
    ]

    operations = [
        migrations.RunPython(set_owner_role_for_creators, reverse_owner_role),
    ]
