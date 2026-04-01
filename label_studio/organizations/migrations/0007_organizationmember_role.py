from django.db import migrations, models


def set_owner_roles(apps, schema_editor):
    """Set the role of organization creators to Owner."""
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    Organization = apps.get_model('organizations', 'Organization')

    for org in Organization.objects.all():
        if org.created_by_id:
            OrganizationMember.objects.filter(
                user_id=org.created_by_id,
                organization=org,
            ).update(role='OW')


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0006_alter_organizationmember_deleted_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='organizationmember',
            name='role',
            field=models.CharField(
                choices=[
                    ('OW', 'Owner'),
                    ('AD', 'Administrator'),
                    ('MA', 'Manager'),
                    ('RE', 'Reviewer'),
                    ('AN', 'Annotator'),
                    ('NO', 'Not Activated'),
                    ('DI', 'Deactivated'),
                ],
                db_index=True,
                default='AN',
                help_text='Role of the user in the organization.',
                max_length=2,
                verbose_name='role',
            ),
        ),
        migrations.RunPython(set_owner_roles, migrations.RunPython.noop),
    ]
