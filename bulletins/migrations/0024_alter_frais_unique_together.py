# Generated by Django 5.1.5 on 2025-03-09 15:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0023_archivepaiement_eleve_nom_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='frais',
            unique_together={('type_frais', 'annee_scolaire', 'classe')},
        ),
    ]
