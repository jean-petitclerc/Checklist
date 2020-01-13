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

DATABASE='app/data/checklist.db'
SQLALCHEMY_DATABASE_URI = 'sqlite:///data/checklist.db'
SQLALCHEMY_TRACK_MODIFICATIONS=False
SECRET_KEY='whatever secret key you want'
DEBUG=True

## Installation

Avec Python 3, créer un environnement virtuel venv
Ajouter les packages listés dans requirements.txt
Créer la database
. venv/bin/activate
cd app
python
from checklist import db
db.create_all()

## Exécution dans l'environnement de développement
. venv/bin/activate
python checklist.py runserver