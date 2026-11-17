# BookWorld – Pipeline de données et API des ventes par pays

Projet final du bootcamp Data Analyst DataBird (RNCP37827 – Bloc 01) – Yassin Abaghdir, 2026.

---

## Présentation

BookWorld est une librairie en ligne fictive qui vend des livres dans plusieurs pays. L'objectif du projet est de calculer **le chiffre d'affaires réalisé dans chaque pays**, en livres sterling (£) et en euros (€).

Les données nécessaires sont réparties entre 4 sources. Le projet est donc composé de deux parties :

1. **Une pipeline de données** (`pipeline.py`), qui fonctionne en 3 étapes, appelées **ETL** :
   - **Extract** : récupérer les données des 4 sources ;
   - **Transform** : les nettoyer, les relier entre elles et calculer le chiffre d'affaires par pays ;
   - **Load** : enregistrer le résultat dans une base de données SQLite (`bookworld_final.db`).
2. **Une API** (`api.py`), qui permet de consulter ces résultats. Elle est protégée par une **clé** (un mot de passe) : sans la bonne clé, l'accès est refusé.

### Les 4 sources de données

| Source | Contenu |
|---|---|
| `sales_raw.csv` | Les 240 ventes brutes (date, livre, pays, canal de vente, quantité, remise, nom du client) |
| `bookworld_reference.db` | Les données de référence de l'entreprise (pays, canaux de vente, catégories) |
| Site books.toscrape.com | Le prix de chaque livre, récupéré automatiquement sur le site (*scraping*) |
| API Frankfurter | Le taux de change £ → € à la date de chaque vente (service gratuit, sans inscription) |

### Protection des données personnelles (RGPD)

Le fichier des ventes contient le prénom et le nom des clients. La pipeline **supprime ces colonnes** avant d'enregistrer les données : la base finale, et donc l'API, ne contiennent aucune information permettant d'identifier un client.

---

## Rôle de chaque fichier

| Fichier | Rôle |
|---|---|
| `pipeline.py` | La pipeline ETL : récupère les 4 sources, calcule et crée la base finale |
| `api.py` | L'API qui donne accès aux résultats, protégée par une clé |
| `sales_raw.csv` | Source : les ventes brutes |
| `bookworld_reference.db` | Source : les données de référence (pays, canaux, catégories) |
| `bookworld_final.db` | La base finale créée par la pipeline (sans noms ni prénoms) |
| `schema_final.sql` | La structure de la base finale : ses tables et les liens entre elles |
| `queries.sql` | Deux exemples de requêtes SQL sur la base finale : un filtre (ventes du canal WEB) et un enrichissement (ventes reliées aux livres, pays et canaux) |
| `bookworld.png` | Le schéma de la base finale (modèle en étoile) |
| `requirements.txt` | La liste des librairies Python à installer |
| `.env.example` | Un modèle pour créer le fichier `.env` qui contient la clé de l'API |
| `.gitignore` | La liste des fichiers à ne pas publier sur GitHub (notamment `.env`, qui contient la clé) |

> **Note :** les fichiers `.db` sont des bases de données SQLite. GitHub ne peut pas afficher leur contenu ; pour les consulter, il faut un logiciel comme [DB Browser for SQLite](https://sqlitebrowser.org/) (gratuit).

---

## Prérequis

- **Une connexion Internet** : la pipeline en a besoin pour récupérer les prix et les taux de change.
- **Python 3** installé sur l'ordinateur.
  - Pour vérifier, ouvrez un terminal (voir ci-dessous) et tapez `python --version`. Un numéro de version doit s'afficher (par exemple `Python 3.12.0`).
  - Sinon, téléchargez Python sur [python.org](https://www.python.org/downloads/). **Sur Windows, cochez la case « Add Python to PATH »** pendant l'installation.

### Ouvrir un terminal

Le terminal est la fenêtre dans laquelle on tape les commandes de ce guide. On tape la commande, puis on appuie sur **Entrée**.

- **Windows** : touche Windows → tapez `PowerShell` → Entrée.
- **Mac** : Cmd + Espace → tapez `Terminal` → Entrée.

---

## Étape 1 – Télécharger le projet

**Sans Git (méthode la plus simple) :**

1. Sur la page GitHub du projet, cliquez sur le bouton vert **`<> Code`**, puis sur **`Download ZIP`**.
2. Dans votre dossier Téléchargements, faites un clic droit sur le fichier ZIP → **Extraire tout**.
3. Vous obtenez un dossier `bookworld` (ou `bookworld-main`).

**Avec Git :**

```bash
git clone https://github.com/yassinabaghdir-beep/bookworld.git
```

Ou en SSH, si une clé SSH est associée à votre compte GitHub :

```bash
git clone git@github.com:yassinabaghdir-beep/bookworld.git
```

---

## Étape 2 – Se placer dans le dossier du projet

Les commandes suivantes doivent **obligatoirement** être lancées **depuis le dossier du projet**.

> **Important :** `pipeline.py` et `api.py` cherchent leurs fichiers (`sales_raw.csv`, `bookworld_reference.db`, `bookworld_final.db`) **dans le dossier où se trouve le terminal**, et non dans le dossier où se trouvent les scripts. Si le terminal est placé ailleurs, les fichiers sont introuvables et la pipeline s'arrête, ou une base vide est créée au mauvais endroit.

- **Windows** : ouvrez le dossier du projet dans l'Explorateur de fichiers, faites un clic droit dans une zone vide → **Ouvrir dans le Terminal**.
- **Ou**, dans un terminal déjà ouvert, utilisez la commande `cd` (« changer de dossier ») suivie du chemin du dossier, par exemple :

```bash
cd Downloads/bookworld
```

> Si vous avez téléchargé le ZIP, le dossier s'appelle sans doute `bookworld-main` : adaptez la commande (`cd Downloads/bookworld-main`).

Pour vérifier que vous êtes au bon endroit, tapez `ls` : la liste doit contenir `pipeline.py`, `api.py`, `sales_raw.csv` et `bookworld_reference.db`.

**Ne lancez pas** les scripts en indiquant leur chemin depuis un autre dossier (par exemple `python Downloads/bookworld/pipeline.py`) : placez-vous d'abord dans le dossier, puis tapez `python pipeline.py`.

---

## Étape 3 – Installer les librairies

```bash
pip install -r requirements.txt
```

Cette commande installe toutes les librairies listées dans `requirements.txt` (pandas, requests, beautifulsoup4, flask, python-dotenv). L'installation peut prendre une minute.

---

## Étape 4 – Lancer la pipeline

```bash
python pipeline.py
```

Le terminal affiche le déroulement de chaque étape. À la fin, vous devez notamment voir :
- **240 ventes** lues ;
- **0** vente sans prix, sans taux de change ou sans pays ;
- **8 pays** dans le résultat.

Le fichier `bookworld_final.db` est alors créé (ou mis à jour) dans le dossier où se trouve le terminal, c'est-à-dire le dossier du projet si l'étape 2 a été suivie. La pipeline peut être relancée autant de fois que nécessaire : la base est recréée à chaque fois.

En cas de problème sur une source (fichier absent, site ou API inaccessible), la pipeline s'arrête et affiche un message qui indique la source en cause.

---

## Étape 5 – Créer la clé de l'API

L'API est protégée par une clé que vous choisissez vous-même. Elle est stockée dans un fichier `.env`, qui n'est jamais publié sur GitHub.

1. Dans le dossier du projet, faites une **copie** du fichier `.env.example`.
2. Renommez la copie en **`.env`** (exactement ce nom, sans rien avant le point).
3. Ouvrez `.env` avec le Bloc-notes. Il contient :
   ```
   API_KEY=remplacer_par_votre_cle
   ```
4. Remplacez `remplacer_par_votre_cle` par la clé de votre choix, sans espace. Par exemple :
   ```
   API_KEY=MaCle2026
   ```
5. Enregistrez le fichier.

> Sur Windows, si l'extension des fichiers est masquée, vérifiez que le fichier ne s'appelle pas `.env.txt`.

---

## Étape 6 – Lancer l'API

Toujours **depuis le dossier du projet** (voir l'étape 2) :

```bash
python api.py
```

Le terminal affiche l'adresse `http://127.0.0.1:5000`. `127.0.0.1` désigne votre propre ordinateur : l'API fonctionne en local.

**Laissez ce terminal ouvert** : le fermer arrête l'API.

---

## Étape 7 – Interroger l'API

Ouvrez **un deuxième terminal** dans le dossier du projet (le premier doit continuer à faire tourner l'API).

L'API propose 2 **endpoints** (adresses auxquelles on envoie une demande) :

| Endpoint | Méthode | Réponse |
|---|---|---|
| `/health` | GET | `status : ok` → l'API fonctionne |
| `/sales-by-country` | GET | Les 8 pays avec : `country_code`, `country_name`, `total_orders` (nombre de commandes), `total_quantity` (nombre de livres vendus), `total_revenue_gbp` (chiffre d'affaires en £) et `total_revenue_eur` (en €), du pays qui rapporte le plus au moins |

### Authentification

Chaque demande doit contenir la clé dans un **en-tête** (une information envoyée avec la demande) nommé `X-API-Key`. Dans les commandes ci-dessous, remplacez `MaCle2026` par la clé inscrite dans votre fichier `.env`.

**Windows (PowerShell) :**

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health -Headers @{"X-API-Key"="MaCle2026"}
```

```powershell
Invoke-RestMethod http://127.0.0.1:5000/sales-by-country -Headers @{"X-API-Key"="MaCle2026"}
```

**Mac / Linux :**

```bash
curl -H "X-API-Key: MaCle2026" http://127.0.0.1:5000/health
```

```bash
curl -H "X-API-Key: MaCle2026" http://127.0.0.1:5000/sales-by-country
```

### Vérifier la protection

Sans clé (ou avec une mauvaise clé), l'API refuse l'accès :

```powershell
Invoke-RestMethod http://127.0.0.1:5000/health
```

Réponse : `Clé API invalide ou absente` avec le code d'erreur **401** (accès non autorisé). C'est le comportement attendu.

> **Pourquoi l'API ne s'ouvre-t-elle pas dans un navigateur ?** Un navigateur (Chrome, Edge…) n'envoie pas l'en-tête `X-API-Key`. L'API refuse donc l'accès : c'est voulu. Elle s'utilise depuis un terminal, ou depuis un autre programme (tableau de bord, application…).

### Arrêter l'API

Dans le terminal où tourne l'API, appuyez sur **Ctrl + C**.

---

## Problèmes fréquents

| Message | Cause | Solution |
|---|---|---|
| `python n'est pas reconnu…` | Python n'est pas installé, ou la case « Add Python to PATH » n'a pas été cochée | Réinstaller Python en cochant la case |
| `No such file or directory` / fichier introuvable | Le terminal n'est pas dans le dossier du projet | Refaire l'étape 2, puis relancer la commande |
| `no such table` (l'API répond par une erreur) | L'API a été lancée hors du dossier du projet : elle a créé une base vide à cet endroit | Supprimer ce `bookworld_final.db` vide, refaire l'étape 2, puis relancer `python api.py` |
| `ModuleNotFoundError` | Les librairies ne sont pas installées | Refaire l'étape 3 |
| `KeyError: 'API_KEY'` | Le fichier `.env` est absent ou mal nommé | Refaire l'étape 5 |
| `Clé API invalide ou absente` | La clé envoyée est différente de celle du fichier `.env` | Vérifier que les deux clés sont identiques |
| Le deuxième terminal n'obtient pas de réponse | L'API n'est pas lancée | Vérifier que `python api.py` tourne dans le premier terminal |
