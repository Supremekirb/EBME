import logging
import traceback

from src.coilsnake.datamodules import MODULES
from src.coilsnake.project_data import ProjectData
from src.misc.worker import Worker


def readDirectory(worker: Worker, dir):
    try:            
        projectData = ProjectData(dir)        
        for module in MODULES:
            try:
                worker.updates.emit(f"Loading {module.NAME}...")
                module.load(projectData)
            except Exception as e:
                worker.returns.emit({"title": f"Failed to load {module.NAME}.",
                                     "text": f"Could not load {module.NAME}.",
                                     "info": f"{type(e).__name__}: {str(e)}"})
                raise
        
        logging.info(f"Successfully loaded project at {projectData.dir}")
        worker.returns.emit(projectData)

    except Exception:
        logging.warning(traceback.format_exc())
        raise