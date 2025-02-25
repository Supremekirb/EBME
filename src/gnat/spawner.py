import random
import time
from enum import IntEnum

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import loadAnimations
from src.gnat.game_state import GameState
from src.gnat.misc import Mini
from src.gnat.scripting import ScriptedAnimatedItem


class Spawner(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/spawner.json"))
    STATES = IntEnum("STATES", ["FLYING",
                                "SLOWING",
                                "DOSPAWN",
                                "SPAWNING", # that's confusing...
                                "DYING"])
        
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/spawner.png"), Spawner.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.play(self.getAnimation("fly"))
        
        self.targetSpeed = 3
        self.spawnTimer = 0
        self.spawnCount = 0
        
        self.state = Spawner.STATES.SPAWNING
        
        # relevant in dospawn behaviour
        self.firstSpawned = None
        
        # random position off the left or right
        # but NOT above or below
        self.setX(random.choice((-32, 272)))
        self.setY(random.randint(16, 184))
        
        GameState.addEnemy(self)
    
    def swatted(self):
        if self.state != Spawner.STATES.DYING:
            self.vx = 0
            self.vy = 0
            self.state = Spawner.STATES.DYING
            self.play(self.getAnimation("death"))
            GameState.playSFX("spawnerdie")
            GameState.takeScore()
            # remove after we have fallen
            return True
        return False
    
    def onNonLoopingAnimationEnd(self, last):
        if last == self.getAnimation("prepareSpawn"):
            self.state = Spawner.STATES.DOSPAWN
            GameState.playSFX("spawn")
            self.play(self.getAnimation("spawn"))
        if last == self.getAnimation("spawn"):
            self.state = Spawner.STATES.FLYING
            dirFactor = random.choice((1, -1))
            self.targetSpeed = 3 * dirFactor
            self.vx = 3 * dirFactor
            self.spawnTimer = 0
            self.spawnCount = 0
            self.firstSpawned = None
            self.play(self.getAnimation("fly"))
    
    async def script(self):
        while True:
            match self.state:
                case Spawner.STATES.DYING:
                    self.vy += 0.5
                    if self.y() > 224:
                        GameState.playSFX("spawnerland")
                        GameState.removeEnemy(self)
                        return
                    await self.pause()
                
                case Spawner.STATES.SPAWNING:
                    if int(self.x()) in range(36, 200):
                        self.state = Spawner.STATES.FLYING
                        
                    if self.x() <= 64:
                        self.vx = 3
                        self.targetSpeed = 3
                    else:
                        self.vx = -3
                        self.targetSpeed = -3
                    
                    await self.pause(2, False)
                
                case Spawner.STATES.FLYING:
                    targetPos = self.calculateTargetPos()
                    
                    if self.vx > self.targetSpeed:
                        self.vx -= 0.2
                        
                    if self.vx < self.targetSpeed:
                        self.vx += 0.2
                        
                    # round to target speed if we're really close anyway
                    if abs(self.vx - self.targetSpeed) < 0.3:
                        self.vx = self.targetSpeed
                        
                    if not random.randint(0, 500): # sometimes start slowing to spawn
                        self.targetSpeed = 0
                        self.play(self.getAnimation("prepareSpawn"))                        
                        
                     # bounce off walls (only horizontally)
                    if not 16 < targetPos.x() < 200:
                        self.vx *= -1
                        self.targetSpeed *= -1
                        
                    await self.pause(2, False)
                
                case Spawner.STATES.DOSPAWN:
                    self.vx = 0
                    if self.spawnTimer <= 0 and self.spawnCount < 4:
                        # the mini guys actually all animate at the same time
                        # so let's keep a reference to the first one and have the
                        # following ones sync their animation timers+frames
                        if not self.firstSpawned:
                            self.firstSpawned = Mini(QPoint(int(self.x() + 10), int(self.y() + 14)))
                        else:
                            new = Mini(QPoint(int(self.x() + 10), int(self.y() + 14)))
                            new.frameIndex = self.firstSpawned.frameIndex
                            new.frameTime = self.firstSpawned.frameTime
                            new.currentSpriteFrame = self.firstSpawned.currentSpriteFrame
                        self.spawnTimer = 4
                        self.spawnCount += 1
                    self.spawnTimer -= 1
                    await self.pause(1, False)