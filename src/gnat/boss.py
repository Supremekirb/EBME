import asyncio
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
                                "DYING"])
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_thorax.png"), Boss.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.head = BossHead(self)
        self.abdomen = BossAbdomen(self)
        self.wingL = BossWingLeft(self)
        self.wingR = BossWingRight(self)
        self.shoulderL = BossShoulderLeft(self)
        self.shoulderR = BossShoulderRight(self)
        self.handL = BossHandLeft(self)
        self.handR = BossHandRight(self)
        
        self.play(self.getAnimation("normal"))
        
        self.state = Boss.STATES.SPAWNING
        
        self.setX(128)
        self.setY(64)
        
        self.hp = 20
        self.hitCooldown = 0
        self.waitingForMove = False
        
        self.hide()
        
        GameState.addEnemy(self)
        
    def swatted(self):
        if self.state == Boss.STATES.NORMAL and not self.hitCooldown:
            self.hp -= 1
            self.hitCooldown = 30
            # annoying little formula to replicate the way the red tint works in the original...
            # - tinting starts on the 10th hit
            # - tinting increases every subsequent 2 hits
            # - does not reach fully red
            self.tint.setColor(QColor(255, 0, 0, max(0, (255/20)*(20-((self.hp-1)//2*2)-10))))
            
            if self.hp == 0:
                self.tint.setColor(QColor(0, 0, 0, 0))
                self.state == Boss.STATES.DYING
                GameState.removeEnemy(self)
                GameState.playBGM("bossdeath")
                GameState.beginNextLevel()
            else:
                GameState.playSFX(random.choice(("bosshurt1", "bosshurt2", "bosshurt3")))
                
            return True
        return False
    
    async def bobTask(self, lock: asyncio.Event):
        while True:
            for i in range(0, 6):
                self.setY(self.y()+1)
                await self.pause(4, lock=lock)
            for i in range(0, 6):
                self.setY(self.y()-1)
                await self.pause(4, lock=lock)
    
    async def moveToMouseTask(self, lock: asyncio.Event):
        targetX = int(GameState.getScene().handCursor.x())
        targetX = common.cap(targetX, 16, 176)
        while True:
            if self.x() < targetX:
                self.setX(self.x() + 1)
            elif self.x() > targetX:
                self.setX(self.x() - 1)
            else:
                self.waitingForMove = False
                break # task complete
            await self.pause(1, lock=lock)
        
    async def script(self):
        bobTaskLock = asyncio.Event()
        bobTaskLock.set()
        bobTask = asyncio.create_task(self.bobTask(bobTaskLock))
        
        currentMove = None
        
        hurtLock = asyncio.Event()
        hurtLock.set()
        
        while True:
            if self.hitCooldown > 0:
                hurtLock.clear()
                self.hitCooldown -= 1
                self.setVisible(not self.isVisible())
            elif self.hitCooldown == 0:
                hurtLock.set()
                self.setVisible(True)    
            
            # goes back to this after every move is complete
            if not self.waitingForMove and self.state == Boss.STATES.NORMAL:
                if currentMove:
                    currentMove.cancel()
                    currentMove = None
                # move logic
                currentMove = asyncio.create_task(self.moveToMouseTask(hurtLock))
                self.waitingForMove = True
            
            match self.state:
                case Boss.STATES.SPAWNING:
                    self.hide()
                    screenFader = ScreenFader()
                    GameState.getScene().addItem(screenFader)
                    
                    GameState.playBossBGM()
                    
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

class BossShoulderLeft(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossShoulderLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("uppermidl"))
        
class BossShoulderRight(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossShoulderRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("uppermidr"))
        
class BossHandLeft(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossHandLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("middownopenl"))
        
class BossHandRight(AnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossHandRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("middownopenr"))