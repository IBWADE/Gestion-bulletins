# Generated by Django 5.1.5 on 2025-03-07 18:40

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0014_archiveemploidutemps_archivefrais_archivepaiement'),
    ]

    operations = [
        migrations.CreateModel(
            name='ArchiveNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('annee_scolaire', models.CharField(max_length=9)),
                ('eleve', models.CharField(max_length=200)),
                ('matiere', models.CharField(max_length=100)),
                ('note_devoir', models.FloatField()),
                ('note_composition', models.FloatField()),
                ('moyenne_matiere', models.FloatField()),
                ('points_matiere', models.FloatField()),
                ('semestre', models.PositiveIntegerField()),
                ('date_archivage', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
