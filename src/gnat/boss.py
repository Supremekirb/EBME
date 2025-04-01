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
from src.gnat.cutscene import (CongratulationsCutsceneHandler,
                               RoundStartDisplay, ScreenFader)
from src.gnat.game_state import GameState
from src.gnat.misc import AttackProjectile, BossMini, BossProjectile, Mini
from src.gnat.scripting import ScriptedAnimatedItem


class Boss(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_thorax.json"))
    STATES = IntEnum("STATES", ["SPAWNING",
                                "NORMAL",
                                "LAUGHING",
                                "DYING"])
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_thorax.png"), Boss.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        # for cutscene stuff
        self.duplicateThorax = DuplicateBossThorax(self)
        self.head = BossHead(self)
        self.abdomen = BossAbdomen(self)
        self.wingL = BossWingLeft(self)
        self.wingR = BossWingRight(self)
        self.shoulderL = BossShoulderLeft(self)
        self.shoulderR = BossShoulderRight(self)
        self.handL = BossHandLeft(self)
        self.handR = BossHandRight(self)
        self.particle = BossParticle(self)
        
        self.play(self.getAnimation("normal"))
        
        self.state = Boss.STATES.SPAWNING
        
        self.setX(98)
        self.setY(64)
        
        self.hp = 20
        self.hitCooldown = 0
        self.waitingForMove = False
        
        self.hide()
        
        GameState.addEnemy(self)
        
    def swatted(self):
        if self.state == Boss.STATES.NORMAL and not self.hitCooldown:
            self.hp -= 1
            self.hitCooldown = 45
            # annoying little formula to replicate the way the red tint works in the original...
            # - tinting starts on the 10th hit
            # - tinting increases every subsequent 2 hits
            # - does not reach fully red
            self.tint.setColor(QColor(255, 0, 0, max(0, (255/20)*(20-((self.hp-1)//2*2)-10))))
            
            # my best approximation of the life-spawning behaviour
            # i don't know if it's this for sure...
            if self.hp == 5 and GameState.INSTANCE.rank == 0:
                GameState.getScene().spawnLife()
                
            if self.hp == 0:
                self.tint.setColor(QColor(0, 0, 0, 0))
                self.state = Boss.STATES.DYING
                if GameState.INSTANCE.level == 3:
                    GameState.playBGM("bossdeathlow")
                else:
                    GameState.playBGM("bossdeath")
                self.particle.damaging = False
                for i in GameState.getScene().items():
                    if isinstance(i, BossProjectile) or isinstance(i, BossMini):
                        i.deleteLater()
            else:
                if GameState.INSTANCE.level == 3:
                    GameState.playSFX(random.choice(("bosshurtlow1", "bosshurtlow2", "bosshurtlow3")))
                else:
                    GameState.playSFX(random.choice(("bosshurt1", "bosshurt2", "bosshurt3")))
                self.head.play(self.head.getAnimation("hit"))
                self.shoulderL.play(self.shoulderL.getAnimation("upperhitl"))
                self.shoulderR.play(self.shoulderR.getAnimation("upperhitr"))
                self.handL.play(self.handL.getAnimation("hitl"))
                self.handR.play(self.handR.getAnimation("hitr"))
                self.abdomen.play(self.abdomen.getAnimation("hit"))
                
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
        targetX = int(GameState.getScene().handCursor.x())-30
        targetX = common.cap(targetX, 16, 176)
        while True:
            if abs(self.x() - targetX) < 3:
                self.waitingForMove = False
                break
            
            if self.x() < targetX:
                self.setX(self.x() + 1*GameState.getSpeedMultiplier())
            elif self.x() > targetX:
                self.setX(self.x() - 1*GameState.getSpeedMultiplier())
            else:
                self.waitingForMove = False
                break # task complete
            await self.pause(1, lock=lock)
            
    async def fireProjectilesTask(self, lock: asyncio.Event):
        self.head.play(self.head.getAnimation("flash"))
        self.shoulderL.play(self.shoulderL.getAnimation("uppermidl"))
        self.shoulderR.play(self.shoulderR.getAnimation("uppermidr"))
        self.handL.play(self.handL.getAnimation("midopenl"))
        self.handR.play(self.handR.getAnimation("midopenr"))
        await self.pause(40, lock=lock)
        # fire!
        pos = QPoint(self.pos().x()+32, self.pos().y())
        for i in range(0, 8):
            BossProjectile(pos, i)
        
        self.head.play(self.head.getAnimation("postfire"))
        self.handL.play(self.handL.getAnimation("midupopenl"))
        self.handR.play(self.handR.getAnimation("midupopenr"))
        
        GameState.playSFX("bossattack")
        await self.pause(50, lock=lock)
        self.waitingForMove = False
        
    
    async def spawnMinisTask(self, lock: asyncio.Event):
        self.head.play(self.head.getAnimation("normal"))
        self.shoulderL.play(self.shoulderL.getAnimation("upperupl"))
        self.shoulderR.play(self.shoulderR.getAnimation("upperupr"))
        self.handL.play(self.handL.getAnimation("updownopenl"))
        self.handR.play(self.handR.getAnimation("updownopenr"))
        self.abdomen.play(self.abdomen.getAnimation("inward"))
        await self.pause(50, lock=lock)
        self.shoulderL.play(self.shoulderL.getAnimation("uppermidl"))
        self.shoulderR.play(self.shoulderR.getAnimation("uppermidr"))
        self.handL.play(self.handL.getAnimation("middownopenl"))
        self.handR.play(self.handR.getAnimation("middownopenr"))
        await self.pause(5, lock=lock)
        self.shoulderL.play(self.shoulderL.getAnimation("upperdownl"))
        self.shoulderR.play(self.shoulderR.getAnimation("upperdownr"))
        self.handL.play(self.handL.getAnimation("downopenl"))
        self.handR.play(self.handR.getAnimation("downopenr"))
        self.abdomen.play(self.abdomen.getAnimation("normal"))
        # spawn
        # spawner does NOT get stunned by hits
        self.particle.play(self.particle.getAnimation("spawn"))
        
        spawnPos = self.pos() + QPoint(30, 48)
        BossMini(spawnPos, spawnPos+QPoint(0, -8))
        BossMini(spawnPos, spawnPos+QPoint(8, 0))
        BossMini(spawnPos, spawnPos+QPoint(0, 8))
        BossMini(spawnPos, spawnPos+QPoint(-8, 0))
        BossMini(spawnPos, spawnPos+QPoint(8, -16))
        BossMini(spawnPos, spawnPos+QPoint(16, -8))
        BossMini(spawnPos, spawnPos+QPoint(16, 8))
        BossMini(spawnPos, spawnPos+QPoint(8, 16))
        BossMini(spawnPos, spawnPos+QPoint(-8, 16))
        BossMini(spawnPos, spawnPos+QPoint(-16, -8))
        BossMini(spawnPos, spawnPos+QPoint(-16, 8))
        BossMini(spawnPos, spawnPos+QPoint(-8, -16))
        
        
        GameState.playSFX("bossspawn")
        await self.pause(100) # don't need to lock for this one 
        self.waitingForMove = False
        
    
    async def launchTask(self, lock: asyncio.Event):
        self.head.play(self.head.getAnimation("normal"))
        self.shoulderL.play(self.shoulderL.getAnimation("upperupl"))
        self.shoulderR.play(self.shoulderR.getAnimation("upperupr"))
        self.handL.play(self.handL.getAnimation("updownopenl"))
        self.handR.play(self.handR.getAnimation("updownopenr"))
        self.abdomen.play(self.abdomen.getAnimation("inward"))
        await self.pause(50, lock=lock)
        self.shoulderL.play(self.shoulderL.getAnimation("uppermidl"))
        self.shoulderR.play(self.shoulderR.getAnimation("uppermidr"))
        self.handL.play(self.handL.getAnimation("middownopenl"))
        self.handR.play(self.handR.getAnimation("middownopenr"))
        await self.pause(5, lock=lock)
        self.shoulderL.play(self.shoulderL.getAnimation("upperdownl"))
        self.shoulderR.play(self.shoulderR.getAnimation("upperdownr"))
        self.handL.play(self.handL.getAnimation("downopenl"))
        self.handR.play(self.handR.getAnimation("downopenr"))
        self.abdomen.play(self.abdomen.getAnimation("normal"))
        
        self.particle.play(self.particle.getAnimation("flame"))
        self.particle.damaging = True
        GameState.playSFX("bosslaunch")
        
        self.vy = 3
        await self.pause(13, lock=lock)
        
        if self.x() > 128-30:
            self.vx = -1
        else:
            self.vx = 1
        
        self.vy = 0
        while self.y() > 64:
            self.vy -= 0.02
            if self.vx > 0:
                self.vx -= 0.02
            else:
                self.vx += 0.02
            await self.pause(1, lock=lock)
        
        self.setY(64)
        self.vy = 0
        self.vx = 0
        
        self.particle.play(self.particle.getAnimation("none"))
        self.particle.damaging = False
        
        self.waitingForMove = False
        
    async def script(self):
        bobTaskLock = asyncio.Event()
        bobTaskLock.set()
        bobTask = asyncio.create_task(self.bobTask(bobTaskLock))
        
        currentMove = None
        
        hurtLock = asyncio.Event()
        hurtLock.set()
        
        while True:
            if 0 < self.hitCooldown < 30:
                hurtLock.set()
                self.hitCooldown -= 1
                self.setVisible(not self.isVisible())
            elif self.hitCooldown >= 30:
                hurtLock.clear()
                self.hitCooldown -= 1
            elif self.hitCooldown == 0:
                hurtLock.set()
                self.setVisible(True)    
            
            # goes back to this after every move is complete
            if not self.waitingForMove and self.state == Boss.STATES.NORMAL:
                if currentMove:
                    # reset animations
                    self.head.play(self.head.getAnimation("blink"))
                    self.handL.play(self.handL.getAnimation("idlel"))
                    self.handR.play(self.handR.getAnimation("idler"))
                    self.shoulderL.play(self.shoulderL.getAnimation("upperdownl"))
                    self.shoulderR.play(self.shoulderR.getAnimation("upperdownr"))
                    self.abdomen.play(self.abdomen.getAnimation("normal"))
                    
                    # reset current move
                    currentMove.cancel()
                    currentMove = None
                    
                # choose new move logic
                availableMoves = []
                
                if int(GameState.getScene().handCursor.x()) in range(int(self.x()), int(self.x())+64):
                    if int(GameState.getScene().handCursor.y()) > int(self.y()):
                        availableMoves.append(self.launchTask)
                        availableMoves.append(self.spawnMinisTask)
                    else:
                        availableMoves.append(self.fireProjectilesTask)
                    
                else:
                    availableMoves.append(self.moveToMouseTask)
                    availableMoves.append(self.spawnMinisTask)
                    availableMoves.append(self.fireProjectilesTask)
                
                currentMove = asyncio.create_task(random.choice(availableMoves)(hurtLock))
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
                    
                case Boss.STATES.LAUGHING:
                    for i in GameState.getScene().items():
                        if isinstance(i, BossProjectile) or isinstance(i, BossMini):
                            i.deleteLater()
                    self.particle.damaging = False
                    
                    self.vx = 0
                    self.vy = 0
                    currentMove.cancel()
                    bobTask.cancel()
                    hurtLock.clear()
                    bobTaskLock.clear()
                        
                    self.head.play(self.head.getAnimation("normal"))
                    self.particle.play(self.particle.getAnimation("none"))
                    self.abdomen.play(self.abdomen.getAnimation("normal"))
                    self.shoulderL.play(self.shoulderL.getAnimation("upperdownl"))
                    self.shoulderR.play(self.shoulderR.getAnimation("upperdownr"))
                    self.handL.play(self.handL.getAnimation("downopenl"))
                    self.handR.play(self.handR.getAnimation("downopenr"))
                    await self.pause(45)
                    
                    self.head.play(self.head.getAnimation("angry"))
                    self.handL.play(self.handL.getAnimation("downclosel"))
                    self.handR.play(self.handR.getAnimation("downcloser"))
                    await self.pause(16)
                    
                    self.head.play(self.head.getAnimation("laugh"))
                    while True:
                        self.head.setY(0)
                        self.handL.play(self.handL.getAnimation("downopenl"))
                        self.handR.play(self.handR.getAnimation("downopenr"))
                        await self.pause(4)
                        
                        self.head.setY(2)
                        self.handL.play(self.handL.getAnimation("downclosel"))
                        self.handR.play(self.handR.getAnimation("downcloser"))
                        await self.pause(4)
                
                case Boss.STATES.DYING:
                    def animUp():
                        self.head.play(self.head.getAnimation("hit3"))
                        self.abdomen.play(self.abdomen.getAnimation("inward"))
                        self.shoulderL.play(self.shoulderL.getAnimation("upperupl"))
                        self.shoulderR.play(self.shoulderR.getAnimation("upperupr"))
                        self.handL.play(self.handL.getAnimation("upopenl"))
                        self.handR.play(self.handR.getAnimation("upopenr"))
                    def animMid():
                        self.head.play(self.head.getAnimation("hit2"))
                        self.abdomen.play(self.abdomen.getAnimation("normal"))
                        self.shoulderL.play(self.shoulderL.getAnimation("uppermidl"))
                        self.shoulderR.play(self.shoulderR.getAnimation("uppermidr"))
                        self.handL.play(self.handL.getAnimation("midopenl"))
                        self.handR.play(self.handR.getAnimation("midopenr"))
                    def animDown():
                        self.head.play(self.head.getAnimation("normal"))
                        self.abdomen.play(self.abdomen.getAnimation("normal"))
                        self.shoulderL.play(self.shoulderL.getAnimation("upperdownl"))
                        self.shoulderR.play(self.shoulderR.getAnimation("upperdownr"))
                        self.handL.play(self.handL.getAnimation("downopenl"))
                        self.handR.play(self.handR.getAnimation("downopenr"))
                    
                    self.vx = 0
                    self.vy = 0
                    currentMove.cancel()
                    hurtLock.clear()
                    
                    self.particle.play(self.particle.getAnimation("smoke"))
                    self.wingL.play(self.wingL.getAnimation("fastl"))
                    self.wingR.play(self.wingR.getAnimation("fastr"))
                    self.play(self.getAnimation("hidden"))
                    self.duplicateThorax.show()
                    
                    for i in range(0, 6):
                        animUp()
                        await self.pause(4)
                        animDown()
                        await self.pause(4)
                        animMid()
                        await self.pause(4)
                        animUp()
                        await self.pause(4)
                        animMid()
                        await self.pause(4)
                    
                    explode1 = RandomisedExplosion(self)
                    animDown()
                    await self.pause(3)
                    animMid()
                    await self.pause(1)
                    animUp()
                    await self.pause(5)
                    animDown()
                    await self.pause(5)
                    animMid()
                    await self.pause(6)
                    explode2 = RandomisedExplosion(self)
                    animUp()
                    await self.pause(6)
                    animMid()
                    await self.pause(6)
                    animUp()
                    await self.pause(7)
                    animDown()
                    await self.pause(7)
                    animMid()
                    await self.pause(7)
                    animUp()
                    await self.pause(8)
                    animMid()
                    await self.pause(8)
                    animUp()
                    await self.pause(8)
                    animDown()
                    await self.pause(9)
                    animMid()
                    await self.pause(9)
                    animUp()
                    explode3 = RandomisedExplosion(self)
                    await self.pause(40)
                    
                    explode1.deleteLater()
                    explode2.deleteLater()
                    explode3.deleteLater()
                    
                    self.particle.play(self.particle.getAnimation("none"))
                    self.wingL.play(self.wingL.getAnimation("normall"))
                    self.wingR.play(self.wingR.getAnimation("normalr"))
                    for i in range(0, 70):
                        self.head.setPos(self.head.x()+2, self.head.y()-4)
                        self.handL.setPos(self.handL.x()-4, self.handL.y()-4)
                        self.shoulderL.setPos(self.shoulderL.x()-4, self.shoulderL.y()-4)
                        self.handR.setPos(self.handR.x()+4, self.handR.y()-4)
                        self.shoulderR.setPos(self.shoulderR.x()+4, self.shoulderR.y()-4)
                        self.abdomen.setY(self.abdomen.y() + 4)
                        self.wingL.setPos(self.wingL.x()+4, self.wingL.y()+4)
                        self.wingR.setPos(self.wingR.x()-4, self.wingR.y()+4)
                        self.duplicateThorax.setPos(self.duplicateThorax.x()-2, self.duplicateThorax.y()-4)
                        await self.pause(1)
                    
                    CongratulationsCutsceneHandler(
                    GameState.INSTANCE.level,
                    GameState.INSTANCE.level == 3 and GameState.INSTANCE.rank == 15,
                    GameState.beginNextLevel)
                    
                    self.deleteLater()
            
                case _:
                    await self.pause()

class SaveStateAnimatedGraphicsItem(AnimatedGraphicsItem):
    def onNonLoopingAnimationEnd(self, last):
        if hasattr(self, "_lastAnim"):
            self.currentAnimation = self._lastAnim
            self.frameIndex = self._lastFrameIndex
            self.frameTime = self._lastFrameTime
            self.currentSpriteFrame = self.currentAnimation.frames[self.frameIndex].frame
            
    def play(self, animation):
        self._lastAnim = self.currentAnimation
        self._lastFrameIndex = self.frameIndex
        self._lastFrameTime = self.frameTime
        return super().play(animation)

class BossHead(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_head.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_head.png"), BossHead.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("blink"))

class DuplicateBossThorax(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_thorax.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_thorax.png"), DuplicateBossThorax.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("normal"))
        self.hide()
        
class BossAbdomen(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_abdomen.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_abdomen.png"), BossAbdomen.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("normal"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

class BossWingLeft(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_wings.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_wings.png"), BossWingLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("flyl"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

class BossWingRight(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_wings.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_wings.png"), BossWingRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("flyr"))
        self.setFlag(AnimatedGraphicsItem.GraphicsItemFlag.ItemStacksBehindParent)

class BossShoulderLeft(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossShoulderLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("upperdownl"))
        
class BossShoulderRight(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossShoulderRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("upperdownr"))
        
class BossHandLeft(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossHandLeft.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("idlel"))
        
class BossHandRight(SaveStateAnimatedGraphicsItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_arms.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_arms.png"), BossHandRight.ANIMATIONS)
        self.setParentItem(parent)
        self.play(self.getAnimation("idler"))
        
class BossParticle(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/boss_particle.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/boss_particle.png"), BossParticle.ANIMATIONS)
        self.setParentItem(parent)
        self.setPos(33, 43)
        self.play(self.getAnimation("none"))
        
        self.damaging = False
        
        # dont adopt parent tint
        self.tint = QBrush(QColor(1, 1, 1, 0))
        
    def onNonLoopingAnimationEnd(self, last):
        self.play(self.getAnimation("none"))
        
    async def script(self):
        while True:
            if self.damaging:
                if GameState.getScene().isIntersectingWithHand(self):
                    GameState.getScene().handCursor.hurt()
                
            await self.pause()
            
class RandomisedExplosion(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/bomb.json"))
    def __init__(self, parent: "Boss"):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/bomb.png"), RandomisedExplosion.ANIMATIONS)
        self.setParentItem(parent)
        
        self.play(self.getAnimation("boom1"))
        
    async def script(self):
        while True:
            self.setPos(
                random.randint(0, 48),
                random.randint(-24, 42)
            )
            self.play(self.getAnimation(random.choice(("boom1", "boom2"))))
            await self.pause(1)