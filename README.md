# Checklist

## Intentions:

Gèrer via un interface Web codé avec Flask des checklists et des codes snippet.  
Les checklists doivent permettrent des subtitutions de variables. Pour le moment, les checklists auront des sections et des étapes uniquement.

- Checklist
  - Description de la checklist
  - Description des variables
  - Section 1
    - Etape 1
    - Etape 2
    - ...
  - Section 2
  - ...

## Configuration

Sous app, créer un dossier config et un dossier data
Dans le dossier config créer config.py et y mettre le contenu suivant (éditer)
```
DATABASE='app/data/checklist.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/checklist.db'
SQLALCHEMY_TRACK_MODIFICATIONS=False
SECRET_KEY='whatever secret key you want'
DEBUG=True
```

## Installation

Avec Python 3, créer un environnement virtuel

Activer l'env. virt.
```
. <venv>/bin/activate
```

Ajouter les packages listés dans requirements.txt

Créer la database
```
cd app
python
from checklist import db
db.create_all()
```

## Exécution dans l'environnement de développement
```
. <venv>/bin/activate
python checklist.py runserver
```
Ouvrir 127.0.0.1:5000 dans un browser

## Utilisation

Commencer par s'inscrire (Ignorer le message concernant l'activation.)
Définir des Variables Prédéfinies (qui seront utiliser dans les checklists et snippets). Exemple:
<DB> - Nom de la base de données
<SCHEMA> - Nom du schéma
...

Définir une checklist avec sections et étapes. Les étapes peuvent contenir du code. Exemple
db2 connect to <DB>

Sélectionner les Variables Prédéfinies pour la checklist

Préparer une checklist

Assigner les valeurs aux variables

Appliquer les valeurs au code

Pour utiliser une checklist préparée, utiliser la fonction "Modifier".  
Le long de l'exécution de votre checklist, vous pouvez sauver des résultats et mettre à jour le status de chaque étape.
