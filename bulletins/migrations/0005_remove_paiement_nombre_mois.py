# Generated by Django 5.1.5 on 2025-03-02 01:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0004_paiement_nombre_mois'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paiement',
            name='nombre_mois',
        ),
    ]
