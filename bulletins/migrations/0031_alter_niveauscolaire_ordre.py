# Generated by Django 5.1.5 on 2025-02-21 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0030_note_note_devoir_delete_notedevoir'),
    ]

    operations = [
        migrations.AlterField(
            model_name='niveauscolaire',
            name='ordre',
            field=models.IntegerField(unique=True),
        ),
    ]
