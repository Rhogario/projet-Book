README - Projet Book


Ce projet a pour objectif de mettre à disposition via une API REST des informations en lien avec la vente de livres identifiés sur le site https://books.toscrape.com/.


1\. Fichiers du projet



Les fichiers sont partagés en 4 catégories : 
- Les fichiers originaux qui constituent notre base d'information initiale : 

sales\_raw.csv : données brutes de ventes.

bookworld\_database.db : base de données source contenant les tables de référence.


- Les scripts python :

pipeline.py : script qui extrait, transforme et charge les données.

api.py : script permettant de lancer l'API.



\-Les documents générés :

projet\_final\_database.db : base de données finale contenant les données traitées.

queries.sql : fichier regroupant les requêtes SQL générées.

schema\_final.sql : fichier décrivant le schéma des tables finales.



\-Les documents de documentation :

README.md : documentation du projet.



2\. Installation des dépendances



Afin de pouvoir exécuter les différents scripts il est nécessaire de remplir quelques conditions : 


- Avoir accès à un terminal généralement accessible sur n'importe quel appareil. 

- Avoir un environnement d'exécution de code Python


- Avoir installé les dépendances nécessaire pour les script 

Ecrire dans le terminal ligne après ligne : 
pip install pandas

pip install requests

pip install beautifulsoup4

pip install Flask

&#x20;


3\. Exécution du pipeline



Dans le terminal, s'assurer d'être à la racine du dossier du projet puis écrire la commande suivante :
python pipeline.py



Le pipeline extrait les données depuis les différentes sources, calcule les revenus en livres sterling et en euros, puis enregistre les résultats dans projet\_final\_database.db et crée également queries.sql et schema\_final.sql.



4\. Lancement de l'API



Après avoir exécuté le pipeline, démarrez l'API avec :



python api.py



L'API est accessible à l'adresse http://127.0.0.1:5000.



Les endpoints sont :



/health : vérification du fonctionnement de l'API.

/sales : consultation des ventes.

/sales\_by\_country : consultation des indicateurs de ventes par pays.



5\. Authentification par token et clé SSH



Token de l'API



L'API utilise un token pour autoriser les requêtes qui dépend de la variable d'environnement nommé API\_TOKEN.
Afin de le paramétrer, renseignez dans votre terminal :
 $env:API\_TOKEN="votre\_token"

Exemple d'appel :



http://127.0.0.1:5000/sales?token=votre\_token



Cette valeur est destinée aux tests locaux.



La clé SSH permet de s'authentifier auprès de GitHub afin de publier le projet sans saisir ses identifiants à chaque opération.



Générer une clé SSH avec la commande 
ssh-keygen -t ed25519 .

puis l'afficher via -t ed25519



Ajouter la clé publique (id\_ed25519.pub) dans les paramètres GitHub, rubrique SSH and GPG keys.



Vérifier la connexion avec ssh -T git@github.com.



Configurer l'adresse SSH du dépôt et publier les modifications avec Git.



git add .

git commit -m "Mettre un message"

git push

