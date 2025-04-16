import os

import yaml

from src.coilsnake.loadmodules.load_module import LoadModule
from src.coilsnake.project_data import ProjectData


class ProjectSnakeModule(LoadModule):
    NAME = "Project.snake"
    
    def load(data: ProjectData):
        try:
            with open(os.path.join(data.dir, "Project.snake")) as project:
                data.projectSnake = yaml.load(project, Loader=yaml.CSafeLoader)

        except FileNotFoundError as e:
            raise FileNotFoundError(f"Project.snake was not found in {data.dir}. Is this a CoilSnake project?") from e