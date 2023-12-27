# Generated by Django 4.0.6 on 2023-12-26 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity', '0003_alter_activity_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='type',
            field=models.CharField(choices=[('Ballet', 'Ballet'), ('Ballroom', 'Ballroom'), ('Belly Dance', 'Belly Dance'), ('Breakdance', 'Breakdance'), ('Contemporary', 'Contemporary'), ('Flamenco', 'Flamenco'), ('Folklore', 'Folklore'), ('Hip Hop', 'Hip Hop'), ('Irish Dance', 'Irish Dance'), ('Jazz', 'Jazz'), ('Krumping', 'Krumping'), ('Locking', 'Locking'), ('Modern Dance', 'Modern Dance'), ('Salsa', 'Salsa'), ('Street Fusion', 'Street Fusion'), ('Swing', 'Swing'), ('Tango', 'Tango'), ('Tap Dance', 'Tap Dance'), ('Vogue', 'Vogue'), ('Waacking', 'Waacking'), ('Zumba', 'Zumba')], max_length=20, verbose_name='Discipline'),
        ),
    ]