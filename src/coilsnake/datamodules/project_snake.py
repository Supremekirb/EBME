import os

import yaml

from src.coilsnake.datamodules.data_module import DataModule
from src.coilsnake.project_data import ProjectData
from src.coilsnake.resource_manager import openTextResource


class ProjectSnakeModule(DataModule):
    NAME = "Project.snake"
    
    def load(data: ProjectData):
        try:
            with openTextResource(os.path.normpath(os.path.join(data.dir, "Project.snake")), "r") as file:
                data.projectSnake = yaml.load(file, Loader=yaml.CSafeLoader)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Project.snake was not found in {data.dir}. Is this a CoilSnake project?") from e
    
    
    def save(data: ProjectData):
        with openTextResource(os.path.normpath(os.path.join(data.dir, "Project.snake")), "w") as file:
            yaml.dump(data.projectSnake, file, Dumper=yaml.CSafeDumper, default_flow_style=None, sort_keys=False)