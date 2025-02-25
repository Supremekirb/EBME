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
        
        GameState.INSTANCE.gameScene.addItem(self)
        
    async def script(self):
        while True:
            # for the first few moments, our turning radius is limited
            # 
            if self.initialMovementTimer > 0:
                self.angle += (GameState.INSTANCE.gameScene.getAngleToHand(self.pos()) - self.angle) / 10
                self.vx = math.sin(self.angle) * 2
                self.vy = math.cos(self.angle) * 2
                self.initialMovementTimer -= 1
                
            # afterwards we just chase the hand perfectly
            elif self.chaseTimer > 0:
                angle = GameState.INSTANCE.gameScene.getAngleToHand(self.pos())
                self.vx = math.sin(angle) * 2
                self.vy = math.cos(angle) * 2
                self.chaseTimer -= 1
                
                if GameState.INSTANCE.gameScene.isIntersectingWithHand(self):
                    # unique behaviour where we disappear if we hurt the hand
                    # (not if we don't hurt it though...)
                    if not GameState.INSTANCE.gameScene.handCursor.hurting and not GameState.INSTANCE.gameScene.handCursor.respawnInvincible:
                        GameState.INSTANCE.gameScene.removeItem(self)
                        GameState.INSTANCE.gameScene.handCursor.hurt()
                        return
            
            if not (0 < self.x() < 256 and 0 < self.y() < 224):
                GameState.INSTANCE.gameScene.removeItem(self)
                return
            
            await self.pause()