import math

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import loadAnimations
from src.gnat.game_state import GameState
from src.gnat.scripting import ScriptedAnimatedItem


class Mini(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/mini.json"))
    def __init__(self, pos: QPoint, spawnAngle: float=0):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/mini.png"), Mini.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.ATTACKS)
        
        self.play(self.getAnimation("fly"))
        
        self.initialMovementTimer = 30
        self.chaseTimer = 80 - self.initialMovementTimer
        
        self.angle = spawnAngle
        
        self.setPos(pos)
        
        GameState.getScene().addItem(self)
        
    async def script(self):
        while True:
            # for the first few moments, our turning radius is limited
            # 
            if self.initialMovementTimer > 0:
                self.angle += (GameState.getScene().getAngleToHand(self.pos()) - self.angle) / 10
                self.vx = math.sin(self.angle) * 2 * GameState.getSpeedMultiplier() 
                self.vy = math.cos(self.angle) * 2 * GameState.getSpeedMultiplier() 
                self.initialMovementTimer -= 1
                
            # afterwards we just chase the hand perfectly
            elif self.chaseTimer > 0:
                angle = GameState.getScene().getAngleToHand(self.pos())
                self.vx = math.sin(angle) * 2 * GameState.getSpeedMultiplier() 
                self.vy = math.cos(angle) * 2 * GameState.getSpeedMultiplier() 
                self.chaseTimer -= 1
                
            
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                self.deleteLater()
                return
            
            if GameState.getScene().isIntersectingWithHand(self):
                # unique behaviour where we disappear if we hurt the hand
                # (not if we don't hurt it though...)
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    self.deleteLater()
                    GameState.getScene().handCursor.hurt()
                    return
            
            await self.pause()

class BossMini(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/mini.json"))
    def __init__(self, origin: QPoint, target: QPoint):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/mini.png"), Mini.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.BOSSATTACKS)
        
        self.play(self.getAnimation("fly"))
        
        self.waitUntilSpawn = 101
        self.initialMovementTimer = 50
        self.chaseTimer = 80
        self.timeTillNextTurn = 10
        
        self.target = target
        
        self.initAngle = math.atan2(self.target.x() - origin.x(), self.target.y() - origin.y())
        
        self.setPos(origin)
        self.hide()
        
        GameState.getScene().addItem(self)
        
    async def script(self):
        while True:
            if self.waitUntilSpawn > 0:
                self.waitUntilSpawn -= 1
            
            # for the first few moments, go to our target pos
            elif self.initialMovementTimer > 0:
                self.show()
                self.vx = math.sin(self.initAngle) / 2
                self.vy = math.cos(self.initAngle) / 2
                if abs(self.x() - self.target.x()) < 2 and abs(self.y() - self.target.y()) < 2:
                    self.vx = 0
                    self.vy = 0
                    self.setPos(self.target)
                self.initialMovementTimer -= 1
                
                if self.initialMovementTimer == 0:
                    self.vx = math.sin(self.initAngle) * GameState.getSpeedMultiplier() 
                    self.vy = math.cos(self.initAngle) * GameState.getSpeedMultiplier() 
                
            # afterwards we just chase the hand perfectly
            elif self.chaseTimer > 0:
                if self.timeTillNextTurn == 0:
                    angle = GameState.getScene().getAngleToHand(self.pos())
                    self.vx = math.sin(angle) * 2 * GameState.getSpeedMultiplier() 
                    self.vy = math.cos(angle) * 2 * GameState.getSpeedMultiplier() 
                    self.timeTillNextTurn = 10
                self.timeTillNextTurn -= 1
                self.chaseTimer -= 1
                
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                self.deleteLater()
                return
            
            if not self.initialMovementTimer and self.isVisible() and GameState.getScene().isIntersectingWithHand(self):
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    self.deleteLater()
                    GameState.getScene().handCursor.hurt()
                    return
            
            await self.pause()
    
class AttackProjectile(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/projectile.json"))
    def __init__(self, pos: QPoint, vx: float, vy: float):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/projectile.png"), AttackProjectile.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.ATTACKS)
        
        self.play(self.getAnimation("regular"))
        
        self.setPos(pos)
        
        self.vx = vx * GameState.getSpeedMultiplier() 
        self.vy = vy * GameState.getSpeedMultiplier() 
        
        GameState.getScene().addItem(self)
    
    async def script(self):
        while True:
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                self.deleteLater()
                return

            if GameState.getScene().isIntersectingWithHand(self):
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    self.deleteLater()
                    GameState.getScene().handCursor.hurt()

            await self.pause()
    
class BossProjectile(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/projectile.json"))
    def __init__(self, pos: QPoint, num: int):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/projectile.png"), BossProjectile.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.BOSSATTACKS)
        
        self.play(self.getAnimation("boss"))
        
        self.setPos(pos)
        
        self.origin = pos
        self.num = num
        self.trigIncrement = 1
        
        GameState.getScene().addItem(self)
        
    
    async def script(self):
        while True:
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                self.deleteLater()
                return
            
            self.setPos(
                self.origin.x()+(math.sin((self.trigIncrement/400)+math.radians(45*self.num))*self.trigIncrement),
                self.origin.y()+(math.cos((self.trigIncrement/400)+math.radians(45*self.num))*self.trigIncrement)
            )
            
            if self.trigIncrement < 75:
                self.trigIncrement += 2 * GameState.getSpeedMultiplier()
            else:
                self.trigIncrement += 2.5 * GameState.getSpeedMultiplier()

            if GameState.getScene().isIntersectingWithHand(self):
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    self.deleteLater()
                    GameState.getScene().handCursor.hurt()

            await self.pause()