# Generated by Django 5.1.5 on 2025-02-13 17:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0007_alter_etablissement_telephone'),
    ]

    operations = [
        migrations.AddField(
            model_name='note',
            name='appreciation',
            field=models.TextField(blank=True, null=True),
        ),
    ]
