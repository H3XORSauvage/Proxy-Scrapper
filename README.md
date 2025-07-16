# Proxy Scraper Ultra-Avancé

## 🚀 Nouvelles Fonctionnalités Avancées

### ✨ Fonctionnalités Majeures

1. **Validation Intelligente des Proxys**
   - Test automatique de la fonctionnalité des proxys
   - Validation parallèle pour plus de rapidité
   - **Interruption à la demande** (Ctrl+C)
   - Filtrage des proxys non fonctionnels

2. **Gestion des Gros Volumes**
   - Suppression automatique des doublons
   - Validation par batch (500-1000 proxys par lot)
   - Optimisation mémoire et performances
   - **Interruption propre** sans perte de données

3. **Test de Vitesse des Proxys**
   - Mesure du temps de réponse de chaque proxy
   - Tri automatique par vitesse (plus rapide en premier)
   - Affichage du top 10 des proxys les plus rapides
   - Sauvegarde avec métadonnées de vitesse

4. **Filtrage Géographique**
   - Détection automatique du pays des proxys
   - Filtrage par codes pays (US, FR, DE, etc.)
   - Utilisation de l'API ip-api.com
   - Sauvegarde avec informations géographiques

5. **Rotateur de Proxys Automatique**
   - Création d'un rotateur qui change automatiquement de proxy
   - Mélange aléatoire pour éviter la détection
   - Rotation circulaire dans la liste
   - Test du rotateur avec affichage des premiers proxys

6. **Interface Utilisateur Améliorée**
   - Menu interactif avec 12 options
   - Messages d'état détaillés et colorés
   - Gestion d'erreurs robuste
   - Interruption propre avec Ctrl+C

###  Fonctionnalités Techniques

- **Threading et Parallélisation** : Jusqu'à 50 workers simultanés
- **Formats de Sortie Multiples** : Simple, détaillé, JSON
- **Configuration Externalisée** : Fichier `config.json` pour les paramètres
- **Validation Ultra-Rapide** : Timeout de 2-5 secondes par proxy
- **Gestion d'Interruption** : Arrêt propre à tout moment

## 📋 Installation

```bash
pip install -r requirements.txt
```

##  Utilisation

### Options Disponibles

1. **Quitter le script**
2. **Scraper des proxys SOCKS5** (avec validation optionnelle)
3. **Scraper des proxys SOCKS4** (avec validation optionnelle)
4. **Scraper des proxys HTTP** (avec validation optionnelle)
5. **Scraper des proxys HTTPS** (avec validation optionnelle)
6. **Scraper tous les types de proxys**
7. **Valider des proxys existants**
8. **Validation rapide** (sans scraping)
9. **Afficher les informations sur les URLs**
10. **Tester la vitesse des proxys** ⭐ NOUVEAU
11. **Filtrer par pays** ⭐ NOUVEAU
12. **Créer un rotateur de proxys** ⭐ NOUVEAU

### Formats de Sortie

1. **Simple** : `IP:PORT`
2. **Détaillé** : `IP:PORT:TYPE:COUNTRY:SPEED:LAST_CHECKED`
3. **JSON** : Format JSON structuré avec métadonnées

## 🔍 Validation des Proxys

Le script teste automatiquement les proxys en :
- Faisant une requête HTTP vers `http://httpbin.org/ip`
- Vérifiant le code de statut 200
- Utilisant un timeout configurable (2-5 secondes)
- **Possibilité d'interruption avec Ctrl+C**

## ⚡ Test de Vitesse

Nouvelle fonctionnalité qui :
- Mesure le temps de réponse de chaque proxy
- Trie automatiquement par vitesse
- Affiche le top 10 des plus rapides
- Sauvegarde avec métadonnées de vitesse

## 🌍 Filtrage Géographique

Fonctionnalité avancée qui :
- Détecte automatiquement le pays des proxys
- Filtre par codes pays (US, FR, DE, etc.)
- Utilise l'API ip-api.com
- Sauvegarde avec informations géographiques

## 🔄 Rotateur de Proxys

Système automatique qui :
- Crée un rotateur de proxys
- Change automatiquement de proxy
- Mélange aléatoirement la liste
- Évite la détection par rotation

## ⚙️ Configuration

Modifiez `config.json` pour :
- Ajouter/supprimer des URLs de sources
- Ajuster les timeouts
- Changer le nombre de workers
- Personnaliser les URLs de test

## 📊 Performance

- **Scraping parallèle** : Jusqu'à 10x plus rapide
- **Validation parallèle** : Test simultané de multiples proxys
- **Gestion mémoire optimisée** : Suppression des doublons en temps réel
- **Interruption propre** : Arrêt à la demande sans perte

## 🛡️ Sécurité

- Validation des formats de proxy
- Gestion des timeouts pour éviter les blocages
- Filtrage des données malformées
- **Interruption propre** avec Ctrl+C

## 📁 Structure des Fichiers

```
proxy_scrapper/
├── ScProxy.py                # Script principal
├── fast_proxy_validator.py   # Validateur ultra-rapide
├── config.json               # Configuration externalisée
├── requirements.txt          # Dépendances Python
├── README.md                 # Documentation complète
└── backup/                   # Sauvegardes automatiques
```


## 🔄 Améliorations Futures Possibles

- [ ] Interface graphique (Tkinter/PyQt)
- [ ] Base de données pour stocker les proxys
- [ ] API REST pour accéder aux proxys
- [ ] Monitoring en temps réel des proxys
- [ ] Système de scoring automatique
- [ ] Intégration avec des outils de scraping

## 🆕 Nouvelles Fonctionnalités

### Test de Vitesse (Option 10)
- Mesure le temps de réponse de chaque proxy
- Trie automatiquement par vitesse
- Affiche le top 10 des plus rapides
- Sauvegarde avec métadonnées de vitesse

### Filtrage Géographique (Option 11)
- Détection automatique du pays des proxys
- Filtrage par codes pays
- Utilisation de l'API ip-api.com
- Sauvegarde avec informations géographiques

### Rotateur de Proxys (Option 12)
- Création d'un rotateur automatique
- Changement automatique de proxy
- Mélange aléatoire pour éviter la détection
- Test du rotateur avec affichage

### Interruption Intelligente
- **Ctrl+C** pour interrompre à tout moment
- Fin propre du batch en cours
- Sauvegarde des proxys déjà validés
- Messages informatifs sur l'état

## Avantages???

- ✅ **Contrôle total** : Interruption à la demande
- ✅ **Performance optimale** : Validation ultra-rapide
- ✅ **Fonctionnalités avancées** : Vitesse, géolocalisation, rotation
- ✅ **Interface intuitive** : Menu clair et informatif
- ✅ **Robustesse** : Gestion d'erreurs complète
- ✅ **Flexibilité** : Multiples formats de sortie 