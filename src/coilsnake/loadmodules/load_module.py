import yaml

from src.misc.exceptions import CoilsnakeResourceNotFoundError
from src.coilsnake.project_data import ProjectData
from src.coilsnake.resource_manager import openCoilsnakeResource


class LoadModule:
    """
    Generic load module. Subclass and reimplement NAME and load.
    """
    NAME = ""
    """Display name of the module. Should be written in plural and lowercase."""
    
    def load(projectData: ProjectData):
        raise NotImplementedError("Base load module has nothing to load!")
    

class CoilsnakeResourceLoadModule(LoadModule):
    """
    Load module that attempts to open a Project.snake resource.
    Subclass and reimplement NAME, MODULE, RESOURCE, and _resourceLoad.
    """
    MODULE: str|tuple[str] = ""
    """A Project.snake module key or a list of modules to attempt to find the resource in."""
    RESOURCE = ""
    """A Project.snake resource key"""
    
    @classmethod
    def load(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            with openCoilsnakeResource(cls.MODULE, cls.RESOURCE, "r", projectData) as file:
                cls._resourceLoad(projectData, file)
        
        if isinstance(cls.MODULE, tuple):
            for module in cls.MODULE:
                try:
                    with openCoilsnakeResource(module, cls.RESOURCE, "r", projectData) as file:
                        cls._resourceLoad(projectData, file)
                    break
                except CoilsnakeResourceNotFoundError:
                    continue
            else:
                return
            # was not broken, ie no modules have the resource
            raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in modules {cls.MODULE}.")
             
    def _resourceLoad(projectData: ProjectData, resource):
        raise NotImplementedError("Base Coilsnake resource load module has nothing to load!")


class YMLCoilsnakeResourceLoadModule(CoilsnakeResourceLoadModule):
    """
    Load module that attempts to open a YML-format Project.snake resource.
    Subclass and reimplement NAME, MODULE, RESOURCE, and _resourceLoad.
    """
    
    @classmethod
    def load(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            with openCoilsnakeResource(cls.MODULE, cls.RESOURCE, "r", projectData) as file:
                resource = yaml.load(file, Loader=yaml.CSafeLoader)
                cls._resourceLoad(projectData, resource)
        
        if isinstance(cls.MODULE, tuple):
            for module in cls.MODULE:
                try:
                    with openCoilsnakeResource(module, cls.RESOURCE, "r", projectData) as file:
                        resource = yaml.load(file, Loader=yaml.CSafeLoader)
                        cls._resourceLoad(projectData, resource)
                    break
                except CoilsnakeResourceNotFoundError:
                    continue
            else:
                # was not broken, ie no modules have the resource
                raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in modules {cls.MODULE}.")