# Generated by Django 5.1.5 on 2025-02-15 18:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0015_remove_note_annee_scolaire_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='etablissement',
            name='ia',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Inspection Académique'),
        ),
        migrations.AddField(
            model_name='etablissement',
            name='ief',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name="Inspection de l'Éducation et de la Formation"),
        ),
    ]
