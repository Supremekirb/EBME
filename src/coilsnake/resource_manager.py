import contextlib
from src.coilsnake.project_data import ProjectData

@contextlib.contextmanager
def openCoilsnakeResource(module: str, resource: str, mode: str, projectData: ProjectData):
    try:
        path = projectData.getResourcePath(module, resource)
        file = open(path, mode, encoding="utf-8")
        yield file

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find the resource {module}.{resource} at {path}.") from e
    
    finally:
        try:
            file.close()
        except UnboundLocalError:
            pass # never got past the getResourcePath, which we already check for