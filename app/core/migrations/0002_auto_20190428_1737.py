# Generated by Django 2.1.8 on 2019-04-28 17:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='gallery',
            old_name='title',
            new_name='name',
        ),
    ]