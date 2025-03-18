import math

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import loadAnimations
from src.gnat.game_state import GameState
from src.gnat.scripting import ScriptedAnimatedItem


# the mini flies that attack you
# spawned by the spawner and the boss
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
                self.vx = math.sin(self.angle) * 2
                self.vy = math.cos(self.angle) * 2
                self.initialMovementTimer -= 1
                
            # afterwards we just chase the hand perfectly
            elif self.chaseTimer > 0:
                angle = GameState.getScene().getAngleToHand(self.pos())
                self.vx = math.sin(angle) * 2
                self.vy = math.cos(angle) * 2
                self.chaseTimer -= 1
                
            
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                GameState.getScene().removeItem(self)
                return
            
            if GameState.getScene().isIntersectingWithHand(self):
                # unique behaviour where we disappear if we hurt the hand
                # (not if we don't hurt it though...)
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    GameState.getScene().removeItem(self)
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
        
        self.vx = vx
        self.vy = vy
        
        GameState.getScene().addItem(self)
    
    async def script(self):
        while True:
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                GameState.getScene().removeItem(self)
                return

            if GameState.getScene().isIntersectingWithHand(self):
                if not GameState.getScene().handCursor.hurting and not GameState.getScene().handCursor.respawnInvincible:
                    GameState.getScene().removeItem(self)
                    GameState.getScene().handCursor.hurt()
                    return

            await self.pause()