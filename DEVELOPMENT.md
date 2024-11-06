# Development Notes

## Cloning

When cloning the source code, please use `--recurse-submodules`. If you're using a git GUI, such as GitHub Desktop, this should happen automatically. In any case please ensure that `/eb-png2fts/` contains png2fts source code.

## Preresiquites

EBME uses Python 3.12.7. I highly recommend using `pyenv` to manage multiple Python versions.
You should create a virtual environment, or PySide6 will complain at you. Use `venv` or `virtualenv` for this.

Once you've created the virtual environment, you should run `prepare_environment.py` to install modules and unpack .spec files.

You should run `prepare_environment.py` periodically in case of changes to `ebme.spec.TEMPLATE` and installed Python packages.

## Build Instructions

Note that it's not necessary to build to use EBME. You can also run `ebme.py` when in the correct environment. Setting up a script to do this for you will be easier than building. But if you still want to:

1. Open a console in the folder (make sure you have the correct Python version and env here!)
2. Run `pyside6-deploy -c embe.spec`
3. The program will be built to `ebme.exe`

You may need a C compiler if Nuitka complains at you. MSYS or Visual Studio 2022's will suffice.

(Note: If using VSCode, press `Ctrl+Shift+B` to build automagically.)

## EBME's Changes to CoilSnake Project Files

EBME modifies CoilSnake-generated `.yml`, `.fts`, and `.map` files. Nothing will make them incompatible with CoilSnake, but there are a few things worth noting:

* Any `.yml` file EBME saves to will have comments removed. EBProjEd does this too, but it doesn't write to tables where you'd usually have comments. See the next few points:
* Several `.yml` files gain new fields `EBME_Comment` and/or `EBME_Colour`. These store data about comments and colours associated with those objects.
* Several `.yml` files are organised in a more compact style for readability. This does not affect how `.yml` interpreters read the file.
* No hexadecimal values are saved, they will be decimal integers. Use Hex Mode (in View) to edit with hexadecimal values if that's your thing.
