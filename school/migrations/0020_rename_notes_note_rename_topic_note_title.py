# Generated by Django 4.2.6 on 2024-03-16 04:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0019_notes'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Notes',
            new_name='Note',
        ),
        migrations.RenameField(
            model_name='note',
            old_name='topic',
            new_name='title',
        ),
    ]