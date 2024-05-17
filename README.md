# Execution 

## Prerequis

[Installer python 3.11 ou supérieur](https://www.python.org/downloads/)

Ou avec conda
```
conda create -n myenv python=3.11
conda activate myenv
```

## Compiler un ficher asm

- `python3.11 compiler.py file.asm`

## Lancer le programme

- Executer `python game.py` a la racine du projet

## Executer les tests

- Executer `python -m unittest` a la racine du projet

# Architecture
Le jeu est structure en 3 parties et chaque partie peut regarder dans les autres par l'intermédiare du plateau de jeu
## CPU

le fichier cpu contient la classe de processeur et ses classes associés. Les flags sont représenté sous forme d'objets 
et les types de mémoire sous forme d'émunération.

Chaque processeur possède des méthodes principales représentant le décodage et l'execution d'un instruction,
et de méthodes d'instructions émulant les differentes instructions possible (`push` par exemple)

## View

le fichier view contient la classe représentant la vue du plateau de jeu

## Game

le fichier game représente le mécanisme du jeu, l'execution, la détermination du vainqueur, choix du fichier
, tout se déroule a l'interieur de la classe game

# Points de compréhension 



# Fait / a faire

Toutes les instructions ont été implémentés, ainsi que le fonctionnement du jeu et la vue.

Cependant, il faut utiliser le compilateur maison pour que cela marche, il supporte toutes les instructions,
les lignes vides et les commentaires en début de ligne (par un #) mais ne supporte pas les fonctions et les déclarations. Il faut ecrire les addresses soi-même