# Development Notes

## Preresiquites

EBME uses Python 3.10.11. I highly recommend using `pyenv` to manage multiple Python versions.
You should create a virtual environment, or PySide6 will complain at you. Use `venv` or `virtualenv` for this.
Once you've created the virtual environment, you should run `prepare_environment.py` to install modules and unpack .spec files.
You should run `prepare_environment.py` periodically in case of changes to `ebme.spec.TEMPLATE` and png2fts.

## Build Instructions

1. Open a console in the folder (make sure you have the correct Python version and env here!)
2. Run `pyside6-deploy -c embe.spec`
3. The program will be built to `ebme.exe`

You may need a C compiler if Nuitka complains at you. MSYS or Visual Studio 2022's will suffice.

(Note: If using VSCode, press `Ctrl+Shift+B` to build automagically.)

## EBME's Changes to CoilSnake Project Files

EBME modifies CoilSnake-generated `.yml`, `.fts`, and `.map` files. Nothing will make them incompatible with CoilSnake, but there are a few things worth noting:

* Any `.yml` file EBME saves to will have comments removed. EBProjEd does this too, but it doesn't write to tables where you'd usually have comments. See the next few points:
* `npc_config_table.yml` gains a new field - `EBME_Comment`. This contains a string to be displayed when editing that NPC.
* `map_hotspots.yml` gains two new fields - `EBME_Comment` and `EBME_Colour`. These contain a comment and an RGB tuple respectively, for use when editing that hotspot.
* `map_sprites.yml` and `map_doors.yml` are organised in a more compact style for readability. This does not affect how `.yml` interpreters read the file.
* No hexadecimal values are saved, they will be decimal integers. Use Hex Mode (in View) to edit with hexadecimal values if that's your thing.

## Some Known Issues on Linux

You might need to install Numpy 1.26.4 for compatibility with Linux systems. I don't know why this is, and Numpy 1.26.4 breaks some things on Windows, which is why I've left it at 1.24.3 (the only version I found to work, but I haven't tested them all.)

Also, I haven't yet tried building it.
