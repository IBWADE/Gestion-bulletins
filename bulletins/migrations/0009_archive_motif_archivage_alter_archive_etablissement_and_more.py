# Generated by Django 5.1.5 on 2025-03-06 09:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0008_emploidutemps'),
    ]

    operations = [
        migrations.AddField(
            model_name='archive',
            name='motif_archivage',
            field=models.CharField(choices=[('fin_annee', 'Fin d’année scolaire'), ('depart', 'Départ de l’établissement'), ('redoublement', 'Redoublement')], default='fin_annee', max_length=50),
        ),
        migrations.AlterField(
            model_name='archive',
            name='etablissement',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='bulletins.etablissement'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='archive',
            unique_together={('eleve', 'annee_scolaire')},
        ),
    ]
