import logging
import traceback

from src.coilsnake.datamodules import MODULES
from src.coilsnake.project_data import ProjectData
from src.misc.worker import Worker


def writeDirectory(worker: Worker, data: ProjectData):   
    try:
        for module in MODULES:
            try:
                worker.updates.emit(f"Saving {module.NAME}...")
                module.save(data)
            except Exception as e:
                worker.returns.emit({"title": f"Failed to save {module.NAME}",
                                     "text": f"Could not save {module.NAME}.",
                                     "info": f"{type(e).__name__}: {str(e)}"})
                raise

        logging.info(f"Successfully saved project at {data.dir}")
        worker.returns.emit(True)

    except Exception:
        logging.warning(traceback.format_exc())
        raise