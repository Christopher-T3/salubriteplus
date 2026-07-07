from django.db import models
from django.contrib.auth.models import User

# ==========================================
# FUNCTIONS DE SECOURS (SENTINELS)
# ==========================================

def get_sentinel_contributeur():
    """ Retourne ou crée un utilisateur générique pour les comptes supprimés """
    user, _ = User.objects.get_or_create(username='contributeur_supprime', is_active=False)
    contributeur, _ = Contributeur.objects.get_or_create(
        user=user,
        defaults={'nom': 'Anonyme', 'postnom': 'Anonyme', 'prenom': 'Contributeur', 'sexe': 'M', 'date_naissance': '2000-01-01'}
    )
    return contributeur.id

def get_sentinel_administrateur():
    """ Retourne ou crée un administrateur générique pour les comptes supprimés """
    user, _ = User.objects.get_or_create(username='administrateur_supprime', is_active=False)
    administrateur, _ = Administrateur.objects.get_or_create(
        user=user,
        defaults={'nom': 'Système', 'postnom': 'Système', 'prenom': 'Modérateur', 'sexe': 'M', 'date_naissance': '2000-01-01'}
    )
    return administrateur.id


# ==========================================
# HIERARCHIE DES UTILISATEURS (HERITAGE MULTI-TABLES)
# ==========================================

class Utilisateur(models.Model):
    # Extension un-à-un vers l'authentification de base de Django
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_metier')
    
    nom = models.CharField(max_length=150)
    postnom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    date_naissance = models.DateField()[cite: 1]
    sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')])[cite: 1]

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Contributeur(Utilisateur):
    # Django crée automatiquement la table 'app_contributeur' liée à 'app_utilisateur'
    def ajouter_signalement(self, signalement):
        pass


class Administrateur(Utilisateur):
    # Django crée automatiquement la table 'app_administrateur' liée à 'app_utilisateur'
    def valider_signalement(self, signalement):
        pass


# ==========================================
# CONFIGURATION GEOGRAPHIQUE
# ==========================================

class Pays(models.Model):
    nom = models.CharField(max_length=100, unique=True)[cite: 1]

class Province(models.Model):
    nom = models.CharField(max_length=100)[cite: 1]
    pays = models.ForeignKey(Pays, on_delete=models.PROTECT)[cite: 1] # Protection de la hiérarchie géographique

class Ville(models.Model):
    nom = models.CharField(max_length=100)[cite: 1]
    province = models.ForeignKey(Province, on_delete=models.PROTECT)[cite: 1]

class Commune(models.Model):
    nom = models.CharField(max_length=100)[cite: 1]
    ville = models.ForeignKey(Ville, on_delete=models.PROTECT)[cite: 1]


# ==========================================
# METIER ET GRAPHES DE SIGNALEMENTS
# ==========================================

class Coordonnees(models.Model):
    longitude = models.DecimalField(max_digits=9, decimal_places=6)[cite: 1]
    latitude = models.DecimalField(max_digits=9, decimal_places=6)[cite: 1]
    commune = models.ForeignKey(Commune, on_delete=models.PROTECT)[cite: 1] # Interdit de supprimer une commune liée à des coordonnées[cite: 1]


class TypeSignalement(models.Model):
    nom = models.CharField(max_length=150, unique=True)[cite: 1]


class Signalement(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = 'EN_COURS', 'En cours'[cite: 1]
        VALIDE = 'VALIDE', 'Valide'[cite: 1]
        INVALIDE = 'INVALIDE', 'Invalide'[cite: 1]

    date_signale = models.DateField(auto_now_add=True)[cite: 1]
    heure_signale = models.TimeField(auto_now_add=True)[cite: 1]
    date_analyse = models.DateField(null=True, blank=True)[cite: 1]
    heure_analyse = models.TimeField(null=True, blank=True)[cite: 1]
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)[cite: 1]

    # En cas de suppression du créateur, le signalement bascule sur l'information générique de secours
    poster_par = models.ForeignKey(
        Contributeur, 
        on_delete=models.SET(get_sentinel_contributeur),
        related_name='signalements_postes'
    )[cite: 1]

    # Un signalement à l'état EN_COURS n'a pas encore d'analyseur, d'où null=True[cite: 1]
    analyser_par = models.ForeignKey(
        Administrateur, 
        on_delete=models.SET(get_sentinel_administrateur), 
        null=True, 
        blank=True,
        related_name='signalements_analyses'
    )[cite: 1]

    # Le signalement doit être protégé : impossibilité de supprimer sa géolocalisation sous-jacente
    localiser = models.OneToOneField(Coordonnees, on_delete=models.PROTECT)[cite: 1]
    
    # Relation Many-To-Many d'intégrité
    types = models.ManyToManyField(TypeSignalement, related_name='signalements')[cite: 1]


class Photo(models.Model):
    nom = models.CharField(max_length=255)[cite: 1]
    lien = models.CharField(max_length=500)[cite: 1]
    size = models.IntegerField()[cite: 1]
    
    # Une photo appartient strictement à un signalement. Si le signalement saute (rare via PROTECT), la photo saute.
    signalement = models.ForeignKey(Signalement, on_delete=models.CASCADE, related_name='photos')[cite: 1]