[This file also exist in English](readme_ENG.md)

# I2C Scanner

L'exemple __[test_i2c_scanner](test_i2c_scanner.py)__ permet de reconfigurer le bus I2C du Pico-Oled-Boot à l'un des débits standards puis de scanner le bus I2C pour y découvrir les adresses utilisées.

Le scan est effectuer toutes les 2 secondes et le résultat affiché sur l'écran.

Les erreurs de scan sont également reportés sur l'écran.

![I2C Scanner](docs/i2c_scanner_00.jpg)

![I2C Scanner - Sélection vitesse bus](docs/i2c_scanner_01.jpg)

![I2C Scanner - Result du scan](docs/i2c_scanner_02.jpg)

Remarque:

* La vitesse du I2C bus affecte également le taux de rafraîchissement de l'écran et du Joystick.
* Le timeout standard est de 50_000 microsecond. Il est augmenté à a 500_000 uSec pour les vitesse les plus faibles.
* L'Oled et le GPIO expander (MCP) sont filtrés dans les résultats (mais néanmoins affichés en bas de l'écran).

# Autres exemples

* __[test_i2c_bmp280.py](test_i2c_bmp280.py)__ : Connectez un capteur BMP280/BME280 sur le connecteur Qwiic/StemmaQT, lire les données et les afficher sur l'écran (avec de jolies icones).<br />![Capteur BMP280/BME280 sur Qwiic/StemmaQT avec affichage de valeur](../../docs/_static/pico-oled-boot-bmp280.jpg)
* __[test_i2c_mcp9808.py](test_i2c_mcp9808.py)__ : Connectez un capteur de température MCP9808 sur le connecteur Qwiic/StemmaQt, lire l'information et l'afficher sur l'écran OLED.
