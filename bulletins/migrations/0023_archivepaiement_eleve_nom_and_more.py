# Generated by Django 5.1.5 on 2025-03-09 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletins', '0022_remove_archivepaiement_eleve_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='archivepaiement',
            name='eleve_nom',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='archivepaiement',
            name='eleve_prenom',
            field=models.CharField(default=1, max_length=100),
            preserve_default=False,
        ),
    ]
