#!/usr/bin/env bash
echo "Copy pbm file..."
cp tiled-project/level1.pbm micropython/level1.pbm
echo "Compile tmx file..."
python3 extract-level-data.py tiled-project/level1.tmx micropython/level1 tiled-project/wall.ids tiled-project/door.ids
python3 show-wall.py micropython/level1
