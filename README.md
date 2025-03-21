<div align="center">
<img alt="EBME" src=https://github.com/Supremekirb/EBME/blob/main/assets/logos/logo.png?raw=true>
<h1 align="center">EarthBound Map Editor</h1>
<img alt="3rd Strongest Mole" src="https://img.shields.io/badge/3rd-Strongest_Mole-gold">
<img alt="SMAAAASH!!" src="https://img.shields.io/badge/SMAAAASH!!-blue">
<img alt="Pictures taken instantaneously!" src="https://img.shields.io/badge/Pictures_taken-instantaneously!-forestgreen">
<img alt="...Brick Road." src="https://img.shields.io/badge/...-Brick_Road.-orangered">
</div>

A GUI program to edit the overworld areas of _EarthBound_, written in Python.

Edits [CoilSnake](https://github.com/pk-hack/CoilSnake) projects.

## Features

* Edit object data in-program (such as NPC data)
* Select and edit multiple objects at once
* Convert PNG files to tilesets and place them visually
* Undo/redo almost everything
* Leave comments on some objects
* Rearrange minitiles in tilesets
* Preview foreground-layer graphics
* Add, delete, export, and import palettes
* Draw collision directly onto the map

## Downloads

Stable release executables for Windows and Linux are available in the [releases tab](https://github.com/Supremekirb/EBME/releases).
MacOS users will have to download the source code themselves. See [DEVELOPMENT.md](DEVELOPMENT.md).

If you want development builds, you can get the latest one [from nightly.link here](https://nightly.link/Supremekirb/EBME/workflows/build_push/main). Note that these may contain bugs and unfinished features! You can also access development builds [on GitHub here](https://github.com/Supremekirb/EBME/actions) by opening the workflow run you want.

## My software is telling me it's a virus!
Thankfully it isn't a virus. Unfortunately antiviruses often return false positives for EBME (see below for why). It's safe to add an exception to your antivirus software to stop it bugging you about EBME. Look up details for your OS/antivirus software.

This is because EBME is written in Python, but distributed as an executable file. For various reasons, this is somewhat nonstandard, and also ACTUAL viruses often use Python in this way. As such, lots of antiviruses have come to see the pattern as "Python in an EXE = bad". Hopefully, eventually enough people will download EBME and add exceptions that antiviruses will learn that it's safe - the same happened with CoilSnake for a time. And if you're still unsure, the source code is available for you to read and understand.

## Screenshots

![The map editor](assets/readme/mapeditor.png)
![The tile editor](assets/readme/tileeditor.png)
