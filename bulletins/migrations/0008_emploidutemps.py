# Generated by Django 5.1.5 on 2025-03-05 17:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0007_paiement_annee_scolaire'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmploiDuTemps',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('jour', models.CharField(choices=[('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'), ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi')], max_length=10)),
                ('heure_debut', models.TimeField()),
                ('heure_fin', models.TimeField()),
                ('classe', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bulletins.classe')),
                ('enseignant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bulletins.enseignant')),
                ('matiere', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bulletins.matiere')),
            ],
        ),
    ]
