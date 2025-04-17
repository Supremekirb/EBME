import contextlib

from PySide6.QtCore import QSettings

import src.misc.common as common
from src.coilsnake.project_data import ProjectData


def getLineEnding() -> str|None:
    eol = QSettings().value("main/lineEnding", common.LINEENDINGINDEX.AUTO, type=int)
    match eol:
        case common.LINEENDINGINDEX.AUTO:
            return None
        case common.LINEENDINGINDEX.UNIX:
            return "\n"
        case common.LINEENDINGINDEX.WINDOWS:
            return "\r\n"
        case common.LINEENDINGINDEX.MAC:
            return "\r"
        case _:
            raise ValueError(f"Unrecognised line ending index: {eol}")
        

@contextlib.contextmanager
def openCoilsnakeResource(module: str, resource: str, mode: str, projectData: ProjectData):
    try:
        path = projectData.getResourcePath(module, resource)
        
        # only respect newline setting when writing
        # I don't know if it will cause any problems
        # when reading, but this should? be safer
        if "w" in mode:
            newline = getLineEnding()
        else:
            newline = None

        file = open(path, mode, encoding="utf-8", newline=newline)
        yield file

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the resource {module}.{resource} at {path}.") from e
    
    finally:
        try:
            file.close()
        except UnboundLocalError:
            pass # never got past the getResourcePath, which we already check for
        

@contextlib.contextmanager
def openTextResource(path: str, mode: str):
    try:
        if "w" in mode:
            newline = getLineEnding()
        else:
            newline = None
        
        file = open(path, mode, encoding="utf-8", newline=newline)
        yield file
    
    finally:
        try:
            file.close()
        except UnboundLocalError:
            pass