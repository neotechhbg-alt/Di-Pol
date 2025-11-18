# Di-Pol

Ein kleines Werkzeug zum Darstellen und Animieren von elektrischen Dipolen.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Nutzung

Starte die Animation mit:

```bash
python dipole_viewer.py --dipole "0,0,1,0" --dipole "1,0,-1,0" --frames 120 --rotation-speed 2
```

Weitere Parameter:

- `--grid-limit`: Größe des dargestellten Bereiches (Standard 3.0)
- `--grid-size`: Auflösung des Vektorfeldes (Standard 20)
- `--frames`: Anzahl der Frames pro Animationsschleife
- `--rotation-speed`: Drehung der Dipole in Grad pro Frame
- `--interval`: Verzögerung zwischen den Frames in Millisekunden
- `--save`: Wenn angegeben, wird die Animation in eine Datei (z. B. MP4 oder GIF) gespeichert

Jeder Dipol wird über `--dipole "x,y,mx,my[,farbe]"` angegeben. Mehrere Dipole können durch mehrfache Verwendung der Option erzeugt werden.
