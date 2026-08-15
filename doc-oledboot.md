# Bibliothèque OledBoot

Le script [oledboot.py](lib/oledboot.py) contient la classe __OledBoot__ ainsi que la définition de différentes constantes.

Seul les definitions essentiels sont reprises ci-dessous.

## Constantes

Les constantes suivantes sont utilisées pour identifier les différentes directions du joystick. Les constantes couvrent également la détection du bouton "Start" ainsi que la pression sur le joystick ("Enter").

```
DOWN = const(1) # BAS
UP   = const(8) # HAUT
RIGHT= const(4) # DROITE
LEFT = const(16)# GAUCHE
ENTER= const(2)
START= const(32)
```

A noter qu'orienter le joystick vers le haut (UP) en le pressant (ENTER) retournera une valeur composée ENNTER+UP (soit 10). La valeur 0 est retournée lorsqu'aucune direction n'est détectée.

## Classe OledBoot

La classe __OledBoot__ permet d'accéder rapidemennt aux fonctionnalités de l'écran, des entrées et des sorties. La classe prend en charge l'allocation des ressources nécessaires.

La classe __OledBoot__ hérite du [FrameBuffer Micropython](https://docs.micropython.org/en/latest/library/framebuf.html) proposant ainsi les différentes primitives de dessins (voir [la documentation ici](https://docs.micropython.org/en/latest/library/framebuf.html))

Remarque:

La bibliothèque FBGFX (egalement installée avec MPRemote) peut être utilisé pour étendre les possibilités de FrameBuffer. Voyez la [documentation FBGFX ici](https://github.com/mchobby/esp8266-upy/tree/master/FBGFX))

### Constructeur

``` 
def __init__( self, oled_addr=0x3c, mcp_addr=0x26 )
```

* __oled_addr__ : Adresse I2C de l'afficheur OLED. Elle peut-être modifiée à l'arriere de l'écran. Dans pareil cas, indiquer la nouvelle adresse ici.
* __mcp_addr__ : Adresse I2C du _GPIO expander_. cette adresse peut être modifiée à l'arriere ce la carte à l'aide d'un cavalier à souder 3 positions (couper la trace en place et souder la partie opposée sur le plot central). Indiquer ici la nouvelle addresse I2C lorsque celle-ci à changé.

### Attribut i2c : I2C

Offre un accès direct au bus I2C partager entre l'écran OLED, le _GPIO expander_ et du port Qwiic/StemmaQt.

Cette référence sera utile lorsque vous connectez un périphérique supplémentaire sur le port Qwiic/StemmaQt.

### Attributs a: Pin , b: Pin

Offre un accès aux boutons A ou B. Comme ce sont des instances de classe Pin,le script utilisateur peut accéder à la méthode `value()` ou y attacher un _IRQ handler_.

La valeur retournée est __`False` lorsque le bouton est pressé__ et `True` lorsqu'il est relâché.

### Attributs red: LedAdapter, green: LedAdapter

Propose un accès aux LEDs verte (__green__) et rouge (__red__) situées au dessus du joystick.

La classe `LedAdapter` permet d'accéder aux methodes `value()`, `on()` et `off()` permettant ainsi de controler une LED si c'était un objet `Pin`.

### Attribut dir: int

Vérifie l'état du joystick (et bouton _Start_) puis retourne une des constantes DOWN, UP, RIGHT, LEFT, ENTER, START sinon retournera 0.

A noter que si plusieurs actions sont combinées comme RIGHT+START or LEFT+START+ENTER alors les différentes constantes impliquées sont sommées ensembles.

## Classe LedAdapter

La classe __LedAdapter__ est conçue pour contôler les LEDs connectées sur le __GPIO expander__ (MCP23008) comme si elles étaient attachées sur des broches du microcontrôleur (donc comme des objets de type `Pin`). 

Par conséquent la LED rouge (_red_) et LED verte (_green_) peuvent être commandé avec les méthodes:

* __on()__ : active la LED
* __off()__ : désactive la LED
* __value()__ : utilise le paramètre booléen pour activer/désactiver la LED. Sans paramètre: retourne le dernier état connu.

