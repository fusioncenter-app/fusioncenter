# Generated by Django 4.0.6 on 2024-01-09 13:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0001_initial'),
        ('activity', '0006_alter_session_activity_alter_session_space'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='instructor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_instructors', to='institution.instructor'),
        ),
        migrations.AlterField(
            model_name='activity',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activity_sites', to='institution.site'),
        ),
    ]