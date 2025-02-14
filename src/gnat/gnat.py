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
from src.gnat.scripting import ScriptedAnimatedItem


class Gnat1(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/gnat1.json"))
    STATES = IntEnum("STATES", ["FLYING",
                                "DYING"])
    
    def __init__(self, animationTimer = AnimationTimer):
        super().__init__(animationTimer, QPixmap(":/gnat/spritesheets/gnat1.png"), Gnat1.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.play(self.getAnimation("fly"))
        
        self.trigIncrement = 1
        self.speedFactor = 0
        self.targetSpeedFactor = 3
        
        self.state = Gnat1.STATES.FLYING
    
    def swatted(self):
        if self.state != Gnat1.STATES.DYING:
            self.vx = 0
            self.vy = 0
            self.state = Gnat1.STATES.DYING
            self.play(self.getAnimation("death"))
            return True
        return False
        
    async def script(self):
        while True:
            match self.state:
                case Gnat1.STATES.DYING:
                    self.vy += 0.5
                    if self.y() > 224 and self.scene():
                        self.scene().removeItem(self)
                    await self.pause()
            
                case Gnat1.STATES.FLYING:
                    targetPos = self.calculateTargetPos()
                    
                    self.trigIncrement += 0.2
                    
                    if self.speedFactor > self.targetSpeedFactor:
                        self.speedFactor -= 1
                    elif self.speedFactor < self.targetSpeedFactor:
                        self.speedFactor += 1
                    else: # they're equal
                        if not random.randint(0, 50) or self.targetSpeedFactor == 0:
                            # can stay going in a circle, but dont stay still
                            self.targetSpeedFactor = random.randint(-10, 10)
                    
                    # wavy circle movement!
                    # it's not 100% accurate to the original,
                    # but it feels similar
                    # they move across the screen in a line less though.
                    self.vx = math.sin(self.trigIncrement)*self.speedFactor
                    self.vy = math.cos(self.trigIncrement)*self.speedFactor
                    
                    # sometimes randomly invert our movement
                    if not random.randint(0, 200):
                        self.speedFactor *= -1
                        self.targetSpeedFactor *= -1
                    
                    # and make sure to bounce off the walls
                    if not 16 < targetPos.x() < 224:
                        self.speedFactor *= -1
                        self.vx *= -1
                    if not 16 < targetPos.y() < 192:
                        self.speedFactor *= -1
                        self.vy *= -1
                    
                    await self.pause(2, False)