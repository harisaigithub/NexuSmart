# Generated by Django 4.2.6 on 2024-03-14 09:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school', '0018_delete_notes_remove_question_course_delete_course_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notes',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=100)),
                ('topic', models.CharField(max_length=100)),
                ('notes_file', models.FileField(upload_to='notes/')),
            ],
        ),
    ]
