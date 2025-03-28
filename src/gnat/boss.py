import math
import random
import time
from enum import IntEnum

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsRectItem

import src.misc.common as common
from src.gnat.animation import AnimatedGraphicsItem, loadAnimations
from src.gnat.cutscene import RoundStartDisplay, ScreenFader
from src.gnat.game_state import GameState
from src.gnat.misc import AttackProjectile, Mini
from src.gnat.scripting import ScriptedAnimatedItem


class Boss(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_thorax.json"))
    STATES = IntEnum("STATES", ["SPAWNING",
                                "NORMAL",
                                "HURTING",
                                "DYING"])
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_thorax.png"), Boss.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.head = BossHead(self)
        self.abdomen = BossAbdomen(self)
        self.wingL = BossWingLeft(self)
        self.wingR = BossWingRight(self)
        
        self.play(self.getAnimation("normal"))
        
        self.state = Boss.STATES.SPAWNING
        
        self.setX(128)
        self.setY(64)
        
        self.hp = 20
        
        self.hide()
        
        GameState.addEnemy(self)
        
    def swatted(self):
        if self.state == Boss.STATES.NORMAL:
            self.hp -= 1
            # annoying little formula to replicate the way the red tint works in the original...
            # - tinting starts on the 10th hit
            # - tinting increases every subsequent 2 hits
            # - does not reach fully red
            self.tint.setColor(QColor(255, 0, 0, max(0, (255/20)*(20-((self.hp-1)//2*2)-10))))
            if self.hp == 0:
                self.tint.setColor(QColor(0, 0, 0, 0))
                self.state == Boss.STATES.DYING
                GameState.removeEnemy(self)
                GameState.beginNextLevel()
            return True
        return False
    
    async def script(self):
        while True:
            match self.state:
                case Boss.STATES.SPAWNING:
                    self.hide()
                    screenFader = ScreenFader()
                    GameState.getScene().addItem(screenFader)
                    
                    for i in range(16, 255+16, 16):
                        i = common.cap(i, 0, 255)
                        screenFader.setAlpha(i)
                        await self.pause(1)
                        screenFader.setAlpha(0)
                        await self.pause(3)
                    
                    self.tint.setColor(QColor(0, 0, 0, 255))
                    self.show()
                    
                    for i in range(0, 255+16, 16):
                        i = common.cap(i, 0, 255)
                        self.tint.setColor(QColor(0, 0, 0, 255-i))
                        screenFader.setAlpha(255-i)
                        await self.pause(1)
                        screenFader.setAlpha(0)
                        await self.pause(3)
                    
                    self.state = Boss.STATES.NORMAL
            
                case _:
                    await self.pause()

class BossHead(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_head.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_head.png"), BossHead.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("blink"))
        
class BossAbdomen(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_abdomen.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_abdomen.png"), BossAbdomen.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("normal"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

class BossWingLeft(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_wings.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_wings.png"), BossWingLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("flyl"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

class BossWingRight(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_wings.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_wings.png"), BossWingRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("flyr"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)