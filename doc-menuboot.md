# Bibliothèque MenuBoot

Le script [menuboot.py](lib/menuboot.py) contient la classe __MenuBoot__ utilisée pour afficher, gérér et détecter l'activation d'une enntrée menu sur l'écran OLED.

MenuBoot permet l'affichage de:

* __basic MenuItem__ avec un code+libellé (pouvant être activé/désactivé)
* __range MenuItem__ pour sélectionner une valeur numérique parmi une gamme de valeurs.
* __combo MenuItem__ pour sélectionner une valeur dans une liste prédéfinie de clé-valeur
* __custom MenuItem__ pour créer une action personnalisée sur une entrée menu (aussi dit "Screen")

Les __basic MenuItem__ permettent au script utilisateur d'exécuter la tâche tandis que les __range, combo, custom MenuItem__ sont complètement automone (ne nécessite pas de code utilisateur pour fonctionner). A noter que le "custom MenuItem" permet néanmoins de lier du code utilisateur au fonctionnement du MenuItem (le dit "Screen").

## Classe MenuBoot

Un menu est construit à l'aide de la classe `MenuBoot`. Le script ci-dessous indique comment créer des entrées dans le menu. Les méthodes principales sont: `add_label()` , `start()` et `update()`. Le MenuItem sélectionner peut être identifier à l'aide de la propriété `selected`.

![Exemple de menu](docs/_static/menu-boot-add-label.jpg)

![Navigationn menu](docs/_static/menu-boot-nav.jpg)

Le bout de code ci-dessous indique comment:

1. Créer un menu, 
2. L'afficher (et utiliser UP et DOWN pour se déplacer dans le menu) 
3. Etre informé de l'entrée sélectionné avec ENTER.

Voir le script [test_menu_basic.py](examples/test_menu_basic.py) pour plus de détails.

``` 
from oledboot import *
from menuboot import *

lcd = OledBoot()
menu = MenuBoot( lcd )

menu.add_label( "start", "Start Oven" ) # code, Label
menu.add_label( "stop" , "Stop Oven" , enabled=False )
menu.add_range( "preheat" , "PreHeat %s C", 25, 180, 5, 50 ) # Min, Max, Step, default
menu.add_label( "t1", "test1" ) 
menu.add_label( "t2", "test2" ) 
menu.add_label( "t3", "test3" ) 
menu.add_label( "t4", "test4" ) 
menu.add_label( "t5", "test5" ) 
menu.add_label( "t6", "test6" ) 
menu.add_label( "t7", "test7" ) 
menu.add_label( "t8", "test8" ) 

menu.start()
while True:
        if menu.update(): # True lorsqu'unne entrée est sélectionnnée
                entry = menu.selected # Lu une seule fois
                if entry:
                        print( "%s selected" % entry )

                        if entry.code=="start":
                                menu.by_code("stop").enabled=True
                        elif entry.code=="stop":
                                menu.by_code("stop").enabled=False
        # effectuer vos autres tâches ici
```

Seul les éléments fondamentaux sont décris ci-dessous.

### Constructeur

``` 
def __init__( self, oled_boot )
```

Connstructeur du Menu, prend un objet OledBoot (l'écran OLED) en référence.

### Méthode add_label()
Ajoute un libellé (_label_) dans le menu. 

L'action d'une telle entrée est gérée directement par le script utilisateur.

```
def add_label( self, code, label, enabled=True ):
```

* __code__ : identification unique du MenuItem.
* __label__ : libellé __statique__ affiché dans le menu. 


### Méthode add_range()

Ajoute une entrée de type RANGE dans le menu.

![Range Menu Item](docs/_static/menu-boot-add-range.jpg)

```
def add_range( self, code, label, min_val, max_val, step, default_val, enabled=True ):
```

* __code__ : identification unique du MenuItem.
* __label__ : libellé __dynamique__ affiché dans le menu et l'écran de sélection de valeur. Le spécificateur de format __"%s" (requis) est remplacé__ avec la valeur actuelle du paramètre.
* __min_val__ : valeur minimale de la gamme.
* __max_val__ : valeur maximale de la gamme.
* __step__ : increment/décrement de la valeur dans la gamme.
* __default_val__ : la valeur par défaut utilisé lors de l'affichage de l'écran de sélection.
* __enabled__ : False=le menu ne peut pas être sélectionner (présente un X à l'avant de l'entrée menu.

Cette entrée est prise en charge par le menu et permet à l'utilisateur de sélectionner une valeur numérique (parmi une gamme de valeur autorisée). Le script utilisateur __est notifié après__ la sélectionne de la nouvelle valeur numérique.

La valeur numérique peur être obtenue à depuis l'objet __MenuItem__ comme ceci:

```
value = my_menu.by_code("menuitem_code").cargo.value
```

Etant donné que la propriété `my_menu.selected` retourne également un objet __MenuItem__, la valeur `value` peut être obtenue à l'aide du script suivant:

```
entry = menu.selected
...
if (entry!=None) and (entry.code=="the_range_menuitem_code"):
  value = entry.cargo.value
```

Voir également l'example [test_menu_range.py](examples/test_menu_range.py) pour plus d'informations

### Méthode add_combo()

Ajout un menu item contenant une sélection de type COMBO.

![Combo Menu Item](docs/_static/menu-boot-add-combo.jpg)

Une telle entrée est gérée par le menu et permet à l'utilisateur de sélectionner une entrée parmi une liste de valeurs possibles. Le script utilisateur __est notifié après__ la sélection de la nouvelle valeur.

```
def add_combo( self, code, label, entries, default, enabled=True ):
```

* __code__ : identification unique du MenuItem.
* __label__ : libellé __dynamique__ affiché dans le menu et l'écran de sélection. Le spécificateur de format __"%s" (requis) est remplacé__ avec le libellé actuelle du paramètre.
* __entries__ : liste d'entrées (key,label) affiché dans l'écran de sélection COMBO.
* __default__ : valeur initiale (la _key_) à sélectionner lorsque l'écran de sélection est affiché.
* __enabled__ : False=le menu ne peut pas être sélectionner (présente un X à l'avant de l'entrée menu.

La valeur sélectionné peut-être obtenu depuis le __MenuItem__ comme suit:

```
value = my_menu.by_code("menuitem_code").value
label = my_menu.by_code("menuitem_code").label
```

Le script [test_menu_combo.py](examples/test_menu_combo.py) indique comment encode une COMBO dans le menu

```
from oledboot import OledBoot
from menuboot import MenuBoot

lcd = OledBoot()
menu = MenuBoot( lcd )

menu.add_label( "start", "Start Oven" ) # code, Label
menu.add_label( "t1", "test1" ) 
menu.add_label( "t2", "test2" ) 
# Parameter are: Menu-code, Menu-label, List of Key-Label, Selected-Key
menu.add_combo( "combo4", 
                "Mode: %s", 
                [("v1", "value 1"),("v2", "value 2"),("v3", "value 3"),("v4", "value 4"),("v5", "value 5"),("v6", "value 6"),("v7", "value 7"),("v8", "value 8")], 
                "v8" ) 
menu.add_label( "t3", "test3" ) 
menu.add_label( "t5", "test5" ) 
menu.add_label( "t6", "test6" ) 
menu.add_label( "t7", "test7" ) 
menu.add_label( "t8", "test8" ) 

menu.start()

while True:
  if menu.update(): # true when entry selected
    entry = menu.selected # will reset selection
      if entry:
        print( "%s selected" % entry )
        # We are informed when we leave the Combo sub-menu
        if entry and entry.code=="combo4":
          print( "Combo selection is '%s' " % menu.by_code("combo4").cargo.value )
          print( "  +-> with label '%s'" % menu.by_code("combo4").cargo.label )
  # Process other tasks here
```

Lorsque le script est exécuté, le resultat suivant est affiché dans la session REPL.

```
<combo4 "Mode: v5"> selected
Combo selection is 'v5'
  +-> with label 'value 5'
```

### Méthode add_screen()

Add a custom SCREEN menu item. When the entry is selected, it calls a `on_start()` function then continuously calls a `on_draw()` function until the ENTER key is pressed.

As for Range and Combo menu item, the user script is notified when the SCREEN is closed.

This feature is used to show custom display content or custom configuration content.

```
def add_screen( self, code, label, on_draw, on_start=None, enabled=True ):
```

* __code__ : identification unique du MenuItem.
* __label__ : libellé __statique__ affiché dans le menu.
* __on_draw__ : événement `event( screen_controler )` appelé avant les appels à `on_draw`. C'est l'endroit idéal pour initialiser des variables.
* __on_draw__ : événement `event( screen_controler, oled )` appelé pour rafraîchir le contenu de l'écran. Cette fonction est constamment appelée jusqu'à ce que le `screen_controler` detecte la pression sur ENTER.
* __enabled__ : False=le menu ne peut pas être sélectionner (présente un X à l'avant de l'entrée menu.

Voir le script d'exemple [test_menu_screen.py](examples/test_menu_screen.py) pour plus d'information.

### Méthode start()

Prépare les instances d'objet pour afficher le menu. l'appel de `start()` est suivit d'appels  en boucle à `update()`.

```
def start( self ):
```

### Méthode update(): bool

La méthode `update()` gère l'affichage du menu et les interactions avec celui-co.

```
def update( self ):
```

La méthode `update()` doit être appélée aussi longtemps que le menu doit être affiché par le scrip utilisateur.

La méthode retourne `True` lorsqu'une entrée du menu à été sélectionnée.

L'élément sélectionné peut être identifié à l'aide de la propriété `selected`.

__Lorsqu'un Basic MenuItem est sélectionné:__ 

comme un élément ajouté avec `add_label` ALORS le script utilisateur est notifié directement de la sélection. 

__Lorsqu'un menu est géré paar un "Menu Controler":__ 

Ce qui est le cas avec les menu de type Range, Combo, Screen ALORS l'exécution est transférée au contrôleur. Le contrôleur prend en charge l'affichage sur l'OLED et prend en charge la tâche de configuration.

Le script utilisateur est informé de la sélection uniquement lorsque le contrôleur termine sa tâche et revient à l'affichage du menu.


### Attribut selected: MenuItem

Retourne une référence sur le MenuItem sélectionné. La référence est effacée dès que la propriété est lue (cela évite de multiples détections accidentelles d'un menu item activé).

```
 @property
 def selected( self ):
```

Notez qu'un MenuItem associé à un contrôleur comme Range, Combo, Screen, ect permet d'accéder au contrôleur via la propriété `MenuItem.cargo`. Le contrôleur permet d'acccéder aux informations complémentaires relatives à la fonction qu'il implémente.

### Méthode by_code(): MenuItem

Retourne la référence d'un Menu Item identifier par son code d'identification. 


```
def by_code( self, code ):
```

## Classe MenuItem

La classe MenuItem contiens les informations relatives a une entrée menu.

Les propriétés principales sont les suivantes:

* __owner__ : le owner est l'instance de MenuBoot.
* __code__ : chaîne de caractères agissant comme identification unique de l'entrée.
* __label__ : libellé affiché dans le menu.
* __enabled__ : True/False, le point de menu désactivé (`enabled=False`) reste visible mais ne reçoit jamais le focus (le rectangle de sélection).
* __visible__ : True/False, le point de menu apparaît (ou pas) dans le menu.
* __cargo__ : None ou reference vers le contrôleur lorsque cela est applicable (comme Range, Combo, Screen, etc)
* __focus__ : _Propriété_ indiquant lorsque le point de menu doit recevoir le focus (le cadre autour du point de menu).
* __selected__ : _Propriété_ indiquant lorsque le point de menu a été sélectionné par l'utilisateur.

Les méthodes principales sont les suivantes:
* __draw()__ : affiche le point de menu sur l'OLED à la position indiquée.

## RangeControler, ComboControler, ScreenControler

Ces classes gèrent les caractéristiques avancées du point de menu. 

L'instance de ces classes est accéssible via l'attribut `MenuItem.cargo`, ce qui permet d'accéder aux propriétés spécifiques de l'instance.

Les propriétés principales sont les suivantes:

* __owner__ : l'instance du menu (MenuBoot).
* __parent__ : le point de menu parent (MenuItem).
* Chaque controleur implémente également les attributs spécifiques à la tâche à réaliser.

Les méthodes principales (commune à tout les contrôleurs) sont les suivantes:

* __start()__ : initialise l'état interne du contrôleur. Il est suivit d'appels à la méthode `update()` .
* __update()__ : appelés continuellement jusuq'à la pression sur ENTER par l'utilisateur. Cette méthode prend en charge l'affichage l'affichage sur l'OLED (et répond aux interactions utilisateurs).


