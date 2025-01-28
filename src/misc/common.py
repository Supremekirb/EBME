# dump a bunch of common constants and functions here

import glob
import logging
import os
import platform
import shlex
from enum import IntEnum, IntFlag

from PySide6.QtCore import QProcess, QSettings, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMessageBox

from ebme import ROOT_DIR

# Current version number/ID
VERSION = "1.0.0"

# Pretty much just for posterity's sake
VERSIONHISTORY = IntEnum("VERSIONHISTORY", ["pre-alpha",
                                            "0.1.0",
                                            "0.2.0",
                                            "0.2.1",
                                            "1.0.0"],
                                            start = 0)

# Add new versions here. Add the new one at the top.
# Don't forget a linebreak between versions!
CHANGELOG = """\
=== 1.0.0 ===
(30/11/24)
This release adds the Tile Editor and Palette Editor, \
collision mode, foreground graphics, major optimisations, \
fixes a number of bugs, and a whole lot more.
Full changelog: Help -> About EBME -> Visit the repository on GitHub.

=== 0.2.1 ===
(03/08/2024)
This release adds a small menu to edit map music, \
makes some minor tweaks to the interface and controls, \
and fixes a few bugs.
Full changelog: Help -> About EBME -> Visit the repository on GitHub.

=== 0.2.0 ===
(25/07/2024)
This release adds a new mode to edit warps and PSI teleports, \
some miscellaneous extra stuff, and bugfixes. \
Some compatibility issues with EBProjEd have also been addressed.
Full changelog: Help -> About EBME -> Visit the repository on GitHub.

=== 0.1.0 ===
(18/07/2024)
Initial release! Thank you for waiting for so long :)
"""

# in pixels
EBMAPWIDTH = 8192
EBMAPHEIGHT = 10240

BYTELIMIT = 0xFF
WORDLIMIT = 0xFFFF

MAXTILES = 960

# TODO MULTIPLATFORM check if these sizes are universally ok
DEFAULTEDITORWIDTH = 1000
DEFAULTEDITORHEIGHT = 700
MINEDITORWIDTH = 450
MINEDITORHEIGHT = 310

# Max number of recent projects to remember
MAXRECENTS = 32

LINEENDINGINDEX = IntEnum("LINEENDINGINDEX", ["AUTO", # python default
                                              "UNIX", # LF
                                              "WINDOWS", # CR LF
                                              "MAC", # CR
                                              ],
                                              start=0) 

MAPZVALUES = IntEnum("MAPZVALUES", ["TILE", # actual map graphics
                                    "IMPORTEDMAP", # png2fts map preview
                                    "GRID", # the grid
                                    "SECTORSELECT", # yellow sector selection box
                                    "NPC", # NPCs
                                    "DOORDESTLINE", # door destination setting line
                                    "TRIGGER", # triggers
                                    "DOORDESTICON", # door destination setting icon
                                    "ENEMY", # enemy tiles
                                    "HOTSPOT", # hotspots
                                    "WARP", # warp dests
                                    "MAPMASK", # outer tile mask
                                    "SCREENMASK", # screen size mask
                                    ], 
                                    start=0)

MODEINDEX = IntEnum("MODEINDEX", ["TILE", 
                                  "SECTOR", 
                                  "NPC", 
                                  "TRIGGER", 
                                  "ENEMY", 
                                  "HOTSPOT", 
                                  "WARP",
                                  "COLLISION",
                                  "ALL", 
                                  "GAME"], 
                                  start=0)

TEMPMODEINDEX = IntEnum("TEMPMODEINDEX", ["NONE",
                                          "IMPORTMAP",
                                          "SETDOORDEST"],
                                          start=0)

ACTIONINDEX = IntEnum("ACTIONINDEX", ["MULTI", # wrapper to merge many commands
                                      "TILEPLACE", # cannot merge with itself
                                      "NPCMOVE", # drag on the map, cannot merge with itself
                                      "NPCSMOVE", # several NPCs, cannot merge with itself
                                      "NPCMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "NPCSMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "NPCCHANGE", # can merge with itself
                                      "NPCUPDATE", # can merge with itself
                                      "NPCADD", # cannot merge with itself
                                      "NPCDELETE", # cannot merge with itself
                                      "TRIGGERMOVE", # drag on the map, cannot merge with itself
                                      "TRIGGERMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "TRIGGERUPDATE", # can merge with itself
                                      "TRIGGERADD", # cannot merge with itself
                                      "TRIGGERDELETE", # cannot merge with itself
                                      "SECTORGFXUPDATE", # can merge with itself
                                      "SECTORATTRUPDATE", # can merge with itself
                                      "ENEMYTILEPLACE", # cannot merge with itself
                                      "ENEMYMAPGROUPUPDATE", # can merge with itself
                                      "HOTSPOTMOVE", # drag on the map, cannot merge with itself
                                      "HOTSPOTMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "HOTSPOTCOLOURUPDATE", # cannot merge with itself
                                      "HOTSPOTCOMMENTUPDATE", # can merge with itself
                                      "WARPMOVE", # drag on the map, cannot merge with itself
                                      "WARPMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "WARPUPDATE", # can merge with itself
                                      "TELEPORTMOVE", # drag on the map, cannot merge with itself
                                      "TELEPORTMOVESIDEBAR", # coords change in sidebar, can merge with itself
                                      "TELEPORTUPDATE", # can merge with itself
                                      "MAPMUSICCHANGE", # can merge with itself
                                      "MAPMUSICMOVE", # cannot merge with itself
                                      "MAPMUSICADD", # cannot merge wiht itself
                                      "MAPMUSICDELETE", # cannot merge with itself
                                      "MINITILEDRAW", # can merge with itself if contents are identical
                                      "ARRANGEMENTCHANGE", # can merge with itself if contents are identical
                                      "COLLISIONCHANGE", # cannot merge with itself
                                      "SUBPALETTECHANGE", # can merge with itself if contents are identical
                                      "MINITILESWAP", # cannot merge with itself
                                      "REPLACEPALETTE", # cannot merge with itself
                                      "PALETTESETTINGSUPDATE", # can merge with itself
                                      "ADDPALETTE", # cannot merge with itself
                                      "REMOVEPALETTE", # cannot merge with itself
                                      "ADDPALETTESETTINGSCHILD", # cannot merge with itself
                                      "REMOVEPALETTESETTINGSCHILD", # cannot merge with itself
                                      ])

# https://github.com/pk-hack/CoilSnake/blob/be5261bf53bf6b1656f693658c45dc321f8565c3/coilsnake/util/common/project.py#L18
COILSNAKEVERSIONNAMES = {
    1:  "1.0",
    2:  "1.1",
    3:  "1.2",
    4:  "1.3",
    5:  "2.0.4",
    6:  "2.1",
    7:  "2.2",
    8:  "2.3.1",
    9:  "3.33",
    10: "4.0",
    11: "4.1",
    12: "4.2",
}

DIRECTION8 = IntEnum("DIRECTION8", ["up",
                                    "up-right",
                                    "right",
                                    "down-right",
                                    "down",
                                    "down-left",
                                    "left",
                                    "up-left"],
                                    start=0)

DIRECTION4 = IntEnum("DIRECTION4", ["up",
                                    "right",
                                    "down",
                                    "left"],
                                    start=0)

COLLISIONBITS = IntFlag("COLLISIONBITS", ["FOREGROUNDBOTTOM",
                                          "FOREGROUNDTOP",
                                          "SUNSTROKE",
                                          "WATER",
                                          "TRIGGER",
                                          "UNUSED",
                                          "VERYSOLID",
                                          "SOLID"])
DEFAULTCOLLISIONPRESETS = "[[\"None\", 0, 0], [\"Solid\", 128, 16711680], [\"Trigger\", 16, 16776960], [\"Solid trigger\", 144, 14483711], [\"Water\", 8, 255], [\"Deep water\", 12, 127], [\"Sunstroke\", 4, 16744192], [\"Foreground bottom half\", 1, 3186688], [\"Foreground full\", 3, 10547200], [\"Talk through\", 130, 11534591]]"


MINITILENOFOREGROUND = 384

def getCoilsnakeVersion(id: int) -> str:
    try:
        return COILSNAKEVERSIONNAMES[id]
    except KeyError: return f"Unknown (ID {id})"

def absolutePath(file: str) -> str:
    """Get the absolute path of a file. Used to avoid packager weirdness.

    Args:
        file (str): relative path of file. Eg: `assets/icon.ico`

    Returns:
        str: absolute path of file
    """
    return os.path.join(ROOT_DIR, os.path.normpath(file))

def invertFlag(flag: int) -> int:
    """Invert a flag (add or subtract 0x8000 depending on if it's less or greater than that number)

    Args:
        flag (int): Flag to invert

    Returns:
        int: Inverted flag
    """
    if flag >= 0x8000:
        return flag-0x8000
    else: return flag+0x8000

def pixToWarp(val: int):
    """Convert pixel value to warp tile value"""
    return int(val//8)
def pixToTile(val: int):
    """Convert pixel value to tile value"""
    return int(val//32)
def pixToSecX(val: int):
    """Convert pixel value to sector X value"""
    return tileToSecX(pixToTile(val))
def pixToSecY(val: int):
    """Convert pixel value to sector Y value"""
    return tileToSecY(pixToTile(val))
def pixToEnemy(val: int):
    """Convert pixel value to enemy tile value"""
    return int(val//64)

def tileToPix(val: int):
    """Convert tile value to pixel value"""
    return int(val*32)
def tileToSecX(val: int):
    """Convert tile value to sector X value"""
    return int(val//8)
def tileToSecY(val: int):
    """Convert tile value to sector Y value"""
    return int(val//4)
def secXToTile(val: int):
    """Convert sector X value to tile value"""
    return int(val*8)
def secYToTile(val: int):
    """Convert sector Y value to tile value"""
    return int(val*4)
def warpToPix(val: int):
    """Convert warp tile value to pixel value"""
    return int(val*8)
def enemyToPix(val: int):
    """Convert enemy tile value to pixel value"""
    return int(val*64)

def cap(val: float, min_: float, max_: float):
    """Restrict a number to range (min, max)"""
    return max(min(max_, val), min_)

# https://stackoverflow.com/a/2267428
def baseN(num: int, base: int, numerals="0123456789abcdefghijklmnopqrstuvwxyz"):
    return ((num == 0) and numerals[0]) or (baseN(num // base, base, numerals).lstrip(numerals[0]) + numerals[num % base])

def normaliseFileExtension(path: str, ext: str) -> str:
    """Add a file extension to a path if the path doesn't already have a file extension."""
    if len(path.split(".")) == 1:
        path += "." + ext
    return path

def showErrorMsg(title: str="Error", text: str="Error.", info: str=None,
                 icon: QMessageBox.Icon=QMessageBox.Icon.Critical):
    """Uniform error message box handling

    Args:
        title (str, optional): Title of the error message box. Defaults to "Error".
        text (str, optional): Basic text contents. Defaults to "Error."
        info (str, optional): More detailed information. Defaults to None.
        icon (Icon, optional): Icon to use in the error box. Defaults to `QMessageBox.Icon.Critical`.
    """
    msg = QMessageBox()
    msg.setIcon(icon) 
    msg.setWindowIcon(QIcon(":/logos/icon.ico"))
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setInformativeText(info)
    msg.exec_()

# TODO MULTIPLATFORM add support for other platforms, check if custom commands work on other platforms 
def openCCSFromLabel(label: str, dir: str):
    """Open a CCS file in the user's default text editor from a label

    Args:
        label (str): Path to the CCS file
        projDir (str): Directory to search in (usually projdir/ccscript/)
    """

    # since this will be lambda'd mostly let's deal with the edge cases first
    if len(label) < 1:
        return showErrorMsg("Error",
                     "Invalid CCS file",
                     "This is an empty string.",
                     icon=QMessageBox.Icon.Warning)
    
    if label[0] == "$": # hex value, not a path
        return showErrorMsg("Error",
                     "Invalid CCS file",
                     "This is an address, not a CCScript label. You may need to decompile the script with CoilSnake first to edit this text.",
                     icon=QMessageBox.Icon.Warning)
    
    if "." not in label:
        return showErrorMsg("Error",
                     "Invalid CCS file",
                     "This is not a valid CCScript label.",
                     icon=QMessageBox.Icon.Warning)


    file = label.split(".")[0]
    lbl = label.split(".")[-1] + ":"

    # search for ccscript files within all subdirs
    path = glob.glob(f'{dir}/**/{file}.ccs', recursive=True)

    if not path:
        return showErrorMsg("Error",
                     "CCS file not found",
                     f"Couldn't find {file}.ccs.",
                     icon=QMessageBox.Icon.Warning)
    
    # search for the label
    with open(path[0]) as file:
        for num, line in enumerate(file, 1):
            if lbl in line:
                break
        else:
            num = 0
            logging.warning("Label not found in file, defaulting to start of file.")
    
    # start setting up the command
    process = QProcess()
    settings = QSettings()
    userCommand = settings.value("programs/textEditorCommand", "", str)

    if userCommand == "":
        # now find the default editor so we can add the right arguments
        # also windows only for now idk about other platforms
        match platform.system():
            case "Windows":
                editorPath = getDefaultEditorWindows('.ccs')
                if not editorPath:
                    return showErrorMsg("Error opening CCScript file",
                            "No default CCScript editor found",
                            "Please set a default editor in your system settings or provide a custom command in EBME settings.",
                            icon=QMessageBox.Icon.Warning)
                
                process.setProgram(editorPath)
                editorName = editorPath.split(os.sep)[-1].lower()
                match editorName:
                    case "notepad++.exe":
                        process.setArguments([f'-n{num}', path[0]])
                    case "code.exe":
                        process.setArguments(['--goto', f'{path[0]}:{num}'])
                    case "notepad.exe":
                        process.setArguments([path[0]]) # no goto-line support
                    case _:
                        logging.warning(f'Unknown default editor "{editorName}", file name will be passed.')
                        process.setArguments([path[0]])
            case _:
                return showErrorMsg("Error opening CCScript file",
                        "Your OS is not currently supported for searching for a default editor.",
                        "You can provide a custom CCScript editor command in EBME settings.",
                        icon=QMessageBox.Icon.Warning)

        process.errorOccurred.connect(lambda error: showErrorMsg("Error opening CCScript file",
                    "Error opening CCScript file",
                    f"Error: {error}, exit code: {process.exitCode()}, exit status: {process.exitStatus()}",
                    icon=QMessageBox.Icon.Warning))
    
    else:
        command = QProcess.splitCommand(userCommand)
        process.setProgram(QStandardPaths.findExecutable(command[0])) # absolute paths are safest
        args = command[1:]
        for i in range(len(args)):
            args[i] = args[i].replace("%F", str(path[0]))
            args[i] = args[i].replace("%L", str(num))
        process.setArguments(args)

        process.errorOccurred.connect(lambda error: showErrorMsg("Error opening CCScript file",
                        "Failed to execute user-provided command.",
                        f"Error: {error}, exit code: {process.exitCode()}, exit status: {process.exitStatus()}",
                        icon=QMessageBox.Icon.Warning))
    
    process.startDetached()

# based on https://stackoverflow.com/a/48121945/15287613
# improved with https://superuser.com/a/1715213 
def getDefaultEditorWindows(suffix: str):
    import winreg
    try:
        try:
            # this entire thing is a whole mess which i have arrived at after hours of trial and error
            # winreg is incredibly sensitive
            # anyway start by checking user settings (even though we shouldnt need to aaaaaaa)
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 fr"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{suffix}\UserChoice")
                
            fileClass = winreg.QueryValueEx(key, "ProgId")[0]
            key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, fileClass)
            command = winreg.QueryValue(key, r"Shell\open\command")
            return shlex.split(command)[0]

        except FileNotFoundError:
            # HKEY_CLASSES_ROOT *should* join CURRENT_USER and LOCAL_MACHINE but this seems to be unreliable
            # So that's why we checked CURRENT_USER first
            fileClass = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, suffix)
            command = winreg.QueryValue(winreg.HKEY_CLASSES_ROOT, fr"{fileClass}\shell\open\command")
            return shlex.split(command)[0]

    except Exception:
        return # caller should handle None as a failure
