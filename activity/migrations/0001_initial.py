# Generated by Django 4.0.6 on 2023-12-24 14:28

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('institution', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=255)),
                ('type', models.CharField(choices=[('Ballet', 'Ballet'), ('Ballroom', 'Ballroom'), ('Belly Dance', 'Belly Dance'), ('Breakdance', 'Breakdance'), ('Contemporary', 'Contemporary'), ('Flamenco', 'Flamenco'), ('Folklore', 'Folklore'), ('Hip Hop', 'Hip Hop'), ('Irish Dance', 'Irish Dance'), ('Jazz', 'Jazz'), ('Krumping', 'Krumping'), ('Locking', 'Locking'), ('Modern Dance', 'Modern Dance'), ('Salsa', 'Salsa'), ('Street Fusion', 'Street Fusion'), ('Swing', 'Swing'), ('Tango', 'Tango'), ('Tap Dance', 'Tap Dance'), ('Vogue', 'Vogue'), ('Waacking', 'Waacking'), ('Zumba', 'Zumba')], max_length=20, verbose_name='Discipline')),
                ('status', models.CharField(choices=[('active', 'Active'), ('inactive', 'Inactive')], default='active', max_length=20)),
                ('custom_capacity', models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('confirmed', 'Confirmed'), ('canceled', 'Canceled'), ('rescheduled', 'Rescheduled'), ('pending', 'Pending')], default='confirmed', max_length=20)),
                ('date', models.DateField()),
                ('from_time', models.TimeField()),
                ('to_time', models.TimeField()),
                ('session_capacity', models.PositiveIntegerField()),
                ('activity', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='activity.activity')),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='institution.space')),
            ],
        ),
        migrations.CreateModel(
            name='Participants',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inscription_datetime', models.DateTimeField(auto_now_add=True)),
                ('assistance_datetime', models.DateTimeField(blank=True, null=True)),
                ('assistance_status', models.CharField(choices=[('present', 'Present'), ('cancelled', 'Cancelled'), ('absent', 'Absent'), ('registered', 'Registered')], default='registered', max_length=20)),
                ('assistance_editor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='editor_assistance_status', to=settings.AUTH_USER_MODEL)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='activity.session')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
