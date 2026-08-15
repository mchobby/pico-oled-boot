[This file also exist in English](readme_ENG.md)

# BootLoader et AutoRun pour MicroPython

## Au démarrage

Le bootloader vérifie quel était le dernier script exécuté puis le démarre à nouveau.

![Bootloader AutoRun](docs/bootloader-autorun.jpg)

Si le script en question produit une erreur alors le bootloader capture l'erreur
et affiche celle-ci sur l'écrab OLED. La LED rouge clignote pour signaler l'erreur.

![Bootloader capturant l'erreur](docs/bootloader-error.jpg)

## Sélectionner un autre script 

A tout moment, l'utilisateur peut sélectionner un autre script a démarrer.

Presser le bouton __A__ lorsque le microcontrôleur démarre (cycle d'alimenation ou un Reset!) 
affichera le menu de sélection.

![Activer le script de sélection](docs/bootloader-activation.jpg)

Cela présentera une liste des scripts disponibles à la racine du système de fichiers.

Le joystick permet de sélectionner le script à exécuter. Presser le joystick (ENTER) pour sélectionner le script.

Le microcontrôleur va redémarrer puis charger le script sélectionné :-)

## Eviter le démarrage automatique (AutoRun)

Le bootloader et l'AutoRun peut être neutralisé lorsque le microcontrôleur démarre.

Presser simplement le bouton __B__ au démarrage.

![Désactiver le bootloader](docs/bootloader-skip.jpg)

La LED rouge reste fixement allumée pour signaler l'annulation de l'AutoRun.

L'AutoRun et le bootloader seront de nouveau actif au redémarrage suivant!


# Comment cela fonctionne

![AutoRun How-To](docs/autorun-howto.jpg)
