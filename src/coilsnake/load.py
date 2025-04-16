import logging
import traceback

from src.coilsnake.loadmodules import MODULES
from src.coilsnake.project_data import ProjectData


def readDirectory(parent, dir):
    try:            
        projectData = ProjectData(dir)        
        for module in MODULES:
            try:
                parent.updates.emit(f"Loading {module.NAME}...")
                module.load(projectData)
            except Exception as e:
                parent.returns.emit({"title": f"Failed to load {module.NAME}.",
                                     "text": f"Could not load {module.NAME}.",
                                     "info": f"{type(e).__name__}: {str(e)}"})
                raise
        
        logging.info(f"Successfully loaded project at {projectData.dir}")
        parent.returns.emit(projectData)

    except Exception:
        logging.warning(traceback.format_exc())
        raise