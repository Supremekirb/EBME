# EBME (EarthBound Map Editor)
# SupremeKirb

import argparse
import logging
import os
import sys

from PySide6.QtCore import QFile, QSettings, QStandardPaths
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

import resources_rc
import src.main.main as main
import src.misc.debug as debug
import src.misc.icons as icons

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug",
                        help="Set debug logging level (lower is more verbose, but zero is none)",
                        type=int,
                        choices=[0, 10, 20, 30, 40, 50],
                        default=20)
    parser.add_argument("-p", "--path",
                        help="Immediately load a project at this path",
                        type=str,
                        default=None)
    parser.add_argument("--no-autoload", action="store_true", help="Don't automatically load the most recent project even if the setting is enabled.")
    parser.add_argument("--system-output", action="store_true", help="Use system output instead of the debug window")
    
    args = parser.parse_args()
    
    if not args.system_output:
        # redirect stdout and stderr to the logger
        sys.stdout = debug.STREAM
        sys.stderr = debug.STREAM
    else:
        debug.SYSTEM_OUTPUT = True
        
    if args.debug:
        logging.basicConfig(level=args.debug)

    app = QApplication(sys.argv)
    
    # init icons now that we have a QApplication
    icons.init_icons()
    
    # this means we dont have to specify this every time we use QSettings
    app.setApplicationName("EBME")
    app.setOrganizationName("PK Hack")
    
    # do desktop file stuff if on wayland
    if QApplication.platformName() == "wayland":
        # check if a desktop file exists in the application folders
        # I'm pretty sure this is how Qt itself does it... hard to find it in the source code
        appPaths = QStandardPaths.standardLocations(QStandardPaths.StandardLocation.ApplicationsLocation)
        if not QStandardPaths.locate(QStandardPaths.StandardLocation.ApplicationsLocation, "EBME.desktop"):
            logging.info(f"Hi Wayland friend, creating a desktop entry now at {appPaths[0]}/EBME.desktop")
            logging.info("Also copying icon to ~/.local/share/icons/EBMEIcon.png")
            
            # ico files don't seem to work too well with auto-matching in desktop entries,
            # so just get the 128x128 one. It's not the end of the world
            QIcon(":/logos/icon.ico").pixmap(128, 128).save(os.path.join(
                QStandardPaths.standardLocations(QStandardPaths.StandardLocation.HomeLocation)[0],
                ".local/share/icons/EBMEIcon.png"
            ))
            
            file = QFile(":/misc/EBME.desktop")
            file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
            desktopFile = file.readAll().data().decode()
            if sys.argv[0] == __file__: # running from python source so desktop file exec needs to be different
                logging.warning("Seems like we're creating the desktop file while running from source.")
                logging.warning("The desktop file's Exec fields will use the binary of this Python. You may wish to change it to your own startup script or to an EBME binary.")
                desktopFile = desktopFile.replace("&EXEC", f"{sys.executable} {sys.argv[0]}")
            else: # otherwise binary, so sys.argv[0] gives us the location we need. Easy!
                desktopFile = desktopFile.replace("&EXEC", sys.argv[0])
                
            with open(os.path.join(appPaths[0],
                                   "EBME.desktop"), "w") as file:
                file.write(desktopFile)
        
        QApplication.setDesktopFileName("EBME")
            
    # create the main window
    # we do this now and not later so we can force a repaint after applying the theme with setUpdatesEnabled
    # ...surely there's a better way to do this?
    MainWin = main.MainApplication(app)
    settings = QSettings()

    # get and set theme
    MainWin.setUpdatesEnabled(False)
    theme = settings.value("personalisation/applicationTheme", type=str)
    if theme:
        if theme == "EarthBound":
            app.setStyle("Fusion")
            file = QFile(":/styles/eb.qss")
            file.open(QFile.OpenModeFlag.ReadOnly | QFile.OpenModeFlag.Text)
            app.setStyleSheet(file.readAll().data().decode())
        else:
            app.setStyle(theme)
    else:
        settings.setValue("personalisation/applicationTheme", app.style().objectName())
    MainWin.setUpdatesEnabled(True)

    MainWin.show()
    
    # If a path was passed, load it
    # If no path was passed and we're told not to autoload, boot without loading
    # Otherwise, if the settings say to, load the last successfully loaded project.
    # Otherwise, nothing
    if args.path:
        logging.info(f"Path was passed, loading project at {args.path}")
        MainWin.projectWin.openDirectory(args.path)
    else:
        loadLast = settings.value("main/disableLoadLast", type=bool)
        lastPath = settings.value("main/LastProjectPath", type=str)
        if lastPath and not loadLast and not args.no_autoload:
            logging.info(f"The last loaded project was at {lastPath}")
            MainWin.projectWin.openDirectory(lastPath)

    app.exec()
    
    # restore stdout and stderr
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__