import shutil

import yaml

from src.coilsnake.project_data import ProjectData
from src.coilsnake.resource_manager import openCoilsnakeResource
from src.misc.exceptions import CoilsnakeResourceNotFoundError


class DataModule:
    """
    Generic data module. Subclass and reimplement NAME, load, and save.
    """
    NAME = ""
    """Display name of the module. Should be written in plural and lowercase."""
    
    def load(projectData: ProjectData):
        raise NotImplementedError("Base data module has nothing to load!")
    
    def save(projectData: ProjectData):
        raise NotImplementedError("Base data module has nothing to save!")
    

class ProjectResourceDataModule(DataModule):
    """
    Data module that provides a standard interface for singular Project.snake resources.
    Subclass and reimplement NAME, MODULE, RESOURCE, _resourceLoad, and _resourceSave
    """
    MODULE: str|tuple[str] = ""
    """A Project.snake module key or a list of modules to attempt to find the resource in."""
    RESOURCE = ""
    """A Project.snake resource key"""
    
    @classmethod
    def load(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            modules = (cls.MODULE,)
        else:
            modules = cls.MODULE
    
        for module in modules:
            try:
                with openCoilsnakeResource(module, cls.RESOURCE, "r", projectData) as file:
                    cls._resourceLoad(projectData, file)
                break
            except CoilsnakeResourceNotFoundError:
                continue
        else:
            # was not broken, ie no modules have the resource
            raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in module(s) {modules}.")

    @classmethod
    def save(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            modules = (cls.MODULE,)
        else:
            modules = cls.MODULE
        
        for module in modules:
            try:
                with openCoilsnakeResource(module, cls.RESOURCE, "w", projectData) as file:
                    rep = cls._resourceSave(projectData)
                    shutil.copyfileobj(rep, file)
                break
            except CoilsnakeResourceNotFoundError:
                continue
        else:
            # was not broken, ie no modules have the resource
            raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in module(s) {modules}.")

 
    def _resourceLoad(projectData: ProjectData, resource):
        raise NotImplementedError("Base Coilsnake resource data module has nothing to load!")
    
    def _resourceSave(projectData: ProjectData):
        raise NotImplementedError("Base Coilsnake resource data module has nothing to save!")


class YMLResourceDataModule(ProjectResourceDataModule):
    """
    Data module that provides a standard interface for single-YML Project.snake resources.
    Subclass and reimplement NAME, MODULE, RESOURCE, FLOW_STYLE, _resourceLoad, and _resourceSave.
    See ProjectResourceDataModule for more information.
    """
    FLOW_STYLE = False
    """The flow style for the YML to dump as when saving"""
    
    @classmethod
    def load(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            modules = (cls.MODULE,)
        else:
            modules = cls.MODULE
    
        for module in modules:
            try:
                with openCoilsnakeResource(module, cls.RESOURCE, "r", projectData) as file:
                    resource = yaml.load(file, Loader=yaml.CSafeLoader)
                    cls._resourceLoad(projectData, resource)
                break
            except CoilsnakeResourceNotFoundError:
                continue
        else:
            # was not broken, ie no modules have the resource
            raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in module(s) {modules}.")
    
    @classmethod
    def save(cls, projectData: ProjectData):
        if isinstance(cls.MODULE, str):
            modules = (cls.MODULE,)
        else:
            modules = cls.MODULE
        
        yml = cls._resourceSave(projectData)                
        for module in modules:
            try:
                with openCoilsnakeResource(module, cls.RESOURCE, "w", projectData) as file:
                    yaml.dump(yml, file, Dumper=yaml.CSafeDumper, default_flow_style=cls.FLOW_STYLE, sort_keys=False)
                break
            except CoilsnakeResourceNotFoundError:
                continue
        else:
            # was not broken, ie no modules have the resource
            raise CoilsnakeResourceNotFoundError(f"Could not find the resource {cls.RESOURCE} in module(s) {modules}")