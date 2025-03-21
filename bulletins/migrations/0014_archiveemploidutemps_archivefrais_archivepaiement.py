# Generated by Django 5.1.5 on 2025-03-07 17:39

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0013_remove_scolaritearchive_classe_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveEmploiDuTemps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee_scolaire', models.CharField(max_length=9)),
                ('classe', models.CharField(max_length=100)),
                ('enseignant', models.CharField(max_length=200)),
                ('matiere', models.CharField(max_length=100)),
                ('jour', models.CharField(max_length=10)),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('date_archivage', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ArchiveFrais',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee_scolaire', models.CharField(max_length=9)),
                ('type_frais', models.CharField(choices=[('inscription', "Frais d'inscription"), ('mensualite', 'Mensualité'), ('autre', 'Autre frais')], max_length=20)),
                ('montant', models.DecimalField(decimal_places=2, max_digits=10)),
                ('classe', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('date_archivage', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='ArchivePaiement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee_scolaire', models.CharField(max_length=9)),
                ('eleve', models.CharField(max_length=200)),
                ('frais', models.CharField(max_length=200)),
                ('montant_paye', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date_paiement', models.DateField()),
                ('mode_paiement', models.CharField(choices=[('especes', 'Espèces'), ('cheque', 'Chèque'), ('virement', 'Virement bancaire'), ('mobile', 'Mobile Money')], max_length=20)),
                ('statut', models.CharField(choices=[('paye', 'Payé'), ('partiel', 'Partiel'), ('impaye', 'Impayé')], max_length=20)),
                ('reference', models.CharField(blank=True, max_length=100, null=True)),
                ('date_archivage', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
