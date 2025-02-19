import asyncio
import math
import random
from enum import IntEnum

from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QBrush, QColor, QPixmap, Qt
from PySide6.QtWidgets import (QGraphicsPixmapItem, QGraphicsScene,
                               QGraphicsTextItem)

import src.misc.common as common
from src.coilsnake.project_data import ProjectData
from src.gnat.animation import (AnimatedGraphicsItem, Animation,
                                AnimationTimer, loadAnimations)
from src.gnat.game_state import GameState
from src.gnat.scripting import ScriptedAnimatedItem


class BonusHand(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/bonus.json"))
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/bonus.png"), BonusHand.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.play(self.getAnimation("flash"))
        
        self.trigIncrement = 0.5
        self.endingScript = False
        
        self.setPos(QPoint(random.randint(64, 192), 0))
        self.vy = 0.6

        GameState.addEnemy(self)
    
    def swatted(self):
        GameState.addLife()
        GameState.removeEnemy(self)
        self.endingScript = True
        return False # dont play hit animation
        
    async def script(self):
        while True:
            if self.endingScript:
                return

            if self.y() > 224:
                GameState.removeEnemy(self)
                return
            
            self.trigIncrement += 0.05
            self.vx = math.sin(self.trigIncrement)*1.5
            
            await self.pause()