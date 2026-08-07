---
name: ste-ecriture
description: Reecrit la prose francaise en francais technique simplifie selon ASD-STE100. Deux modes : strict et aromatise.
---

# ste-ecriture

Ecrivez de la prose selon les regles du francais technique simplifie.

## Quand utiliser

Utilisez ce skill quand :
- Vous ecrivez de la documentation technique en francais
- Vous ameliorez la clarte des descriptions de PR
- Vous nettoyez les messages d'erreur
- Vous reduisez le slop LLM dans le texte francais

Deux modes :
- **strict** : Pour instructions et erreurs - clarte maximale
- **aromatise** : Pour prose generale - equilibre clarte/naturel

## Regles fondamentales

### 1. Mots simples
- Evitez : essentiellement, fondamentalement, pratiquement
- Preferez : mots directs et concrets
- Evitez : revolutionnaire, innovant, disruptif, puissant

### 2. Voix active
- Evitez : Le fichier est traite par le systeme
- Preferez : Le systeme traite le fichier

### 3. Pas de nominalisations
- Evitez : La realisation de cette tache necessite...
- Preferez : Pour realiser cette tache, vous devez...

### 4. Specificite
- Evitez : tres important, tres bon, tres difficile
- Preferez : descriptions precises et mesurables

### 5. Phrases courtes
- Une idee par phrase
- Maximum 20-25 mots en mode strict

### 6. Pas de remplissage
- Supprimez : en fait, en realite, bien sur
- Supprimez : il est important de noter que
- Supprimez : sans aucun doute


## Exemples

### Mode strict

BEFORE:
Il est essentiel de noter que le systeme necessite une configuration prealable.

AFTER:
Configurez le systeme avant utilisation.

### Mode aromatise

BEFORE:
Cette solution revolutionnaire permet de gerer les configurations complexes.

AFTER:
Cet outil gere les configurations complexes via une interface claire.

## Utilisation du linter

Le linter francais (fr/fr-ste-lint.py) verifie automatiquement :

- Mots interdits (essentiellement, fondamentalement, etc.)
- Termes marketing (revolutionnaire, innovant, disruptif, etc.)
- Expressions de remplissage (en fait, en realite, bien sur, etc.)

## Detection automatique

Le systeme detecte le francais via :
- Caracteres accentes : a, e, e, i, o, u
- Caracteres speciaux : c, oe, ae
- Priorite : Russe > Espagnol > Francais > Anglais

## Ressources

- Documentation : docs/USAGE.md
- Exemples : fr/samples/
- Tests : tests/test_fr_ste_lint.py

## Contribution

Pour ameliorer les regles francaises :
1. Modifiez les patterns dans fr/fr-ste-lint.py
2. Ajoutez des exemples dans fr/samples/
3. Mettez a jour les tests dans tests/test_fr_ste_lint.py
4. Creez une pull request

## Licence

MIT License - fait partie d'anti-slop-kit
