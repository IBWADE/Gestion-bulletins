from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def generer_echeances_pour_eleve(eleve):
    from .models import Frais, Echeance, AnneeScolaire    

    # Vérifier que l'élève a une classe
    if not eleve.classe:
        print("L'élève n'a pas de classe")
        return

    # Récupérer l'année scolaire en cours
    annee_scolaire = AnneeScolaire.get_annee_scolaire_en_cours()
    if not annee_scolaire:
        print("Aucune année scolaire en cours")
        return

    # Vérifier s'il y a des frais définis pour la classe de l'élève
    frais_mensuels = Frais.objects.filter(type_frais='mensualite', classe=eleve.classe, annee_scolaire=annee_scolaire)
    if not frais_mensuels.exists():
        print("Aucun frais trouvé pour cette classe")
        return

    # Déterminer les dates de début et de fin des échéances
    date_debut = annee_scolaire.debut  # Commence toujours à la date de début de l'année scolaire
    date_fin = annee_scolaire.fin
    date_echeance = (date_debut + relativedelta(months=1)).replace(day=5)

    # Générer les échéances depuis le début de l'année scolaire jusqu'à la fin
    while date_echeance <= date_fin:
        for frais in frais_mensuels:
            # Vérifier si une échéance existe déjà pour ce mois
            echeance_existante = Echeance.objects.filter(
                eleve=eleve,
                frais=frais,
                date_echeance__year=date_echeance.year,
                date_echeance__month=date_echeance.month
            ).first()

            if echeance_existante:
                # Si l'échéance existe, la marquer comme impayée
                echeance_existante.statut = 'impaye'
                echeance_existante.save()
                print(f"🔄 Échéance mise à jour : {date_echeance} - {frais.montant} (statut: impaye)")
            else:
                # Si l'échéance n'existe pas, la créer avec un statut impayé
                Echeance.objects.create(
                    eleve=eleve,
                    frais=frais,
                    date_echeance=date_echeance,
                    montant_du=frais.montant,
                    statut='impaye'
                )
                print(f"✅ Échéance créée : {date_echeance} - {frais.montant} (statut: impaye)")

        # Passer au mois suivant
        date_echeance += relativedelta(months=1)  # Utiliser relativedelta pour éviter les erreurs avec timedelta
        date_echeance = date_echeance.replace(day=5)