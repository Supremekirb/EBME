import math
import random
import time
from enum import IntEnum

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import loadAnimations
from src.gnat.game_state import GameState
from src.gnat.misc import AttackProjectile, Mini
from src.gnat.scripting import ScriptedAnimatedItem


class Attack(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/attack.json"))
    STATES = IntEnum("STATES", ["FLYING",
                                "PREPARING",
                                "ATTACKING",
                                "SPAWNING",
                                "DYING"])
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/attack.png"), Attack.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.play(self.getAnimation("fly"))
        
        self.trigIncrement = 1
        self.trigIncrementFactor = 1
        self.speedFactor = 0
        self.targetSpeedFactor = 3
        
        self.state = Attack.STATES.SPAWNING
        
        # random position on the sides
        self.setX(random.choice(list(range(-32, -16)) + list(range(256, 272))))
        self.setY(random.randint(-32, 256))
        
        GameState.addEnemy(self)
    
    def swatted(self):
        if self.state != Attack.STATES.DYING:
            self.vx = 0
            self.vy = 0
            self.state = Attack.STATES.DYING
            self.play(self.getAnimation("death"))
            GameState.playSFX("attackdie")
            GameState.takeScore()
            # remove after we have fallen
            return True
        return False
        
    async def script(self):
        while True:
            match self.state:
                case Attack.STATES.DYING:
                    self.vy += 0.5
                    if self.y() > 224:
                        GameState.playSFX("attackland")
                        GameState.removeEnemy(self)
                        return
                    await self.pause()
                    
                case Attack.STATES.SPAWNING:                       
                    if int(self.x()) in range(36, 220) and int(self.y()) in range(36, 188):
                        self.state = Attack.STATES.FLYING
                        
                    if self.x() <= 64:
                        self.vx = 3
                    elif self.x() >= 129:
                        self.vx = -3
                    else:
                        self.vx = 0
                    
                    if self.y() <= 64:
                        self.vy = 3
                    elif self.y() >= 160:
                        self.vy = -3
                    else:
                        self.vy = 0
                        
                    await self.pause(2, False)
                    
                case Attack.STATES.PREPARING:
                    targetPos = self.calculateTargetPos()
                    
                    if self.vx > 0:
                        self.vx -= 0.2
                    if self.vx < 0:
                        self.vx += 0.2
                    if abs(self.vx) < 0.3:
                        self.vx = 0
                    
                    if self.vy > 0:
                        self.vy -= 0.2
                    if self.vy < 0:
                        self.vy += 0.2
                    if abs(self.vy) < 0.3:
                        self.vy = 0
                        
                    self.vx = 0
                    self.vy = 0
                    
                    didWeDie = False
                    for i in range(0, 120):
                        if self.state == Attack.STATES.DYING:
                            didWeDie = True
                            break
                        await self.pause()     
                                           
                    if didWeDie:
                        continue
                    
                    velocities = ((1, 1), (-1, 1), (1, -1), (-1, -1))
                    for i in range(0, 4):
                        AttackProjectile(self.scenePos(), velocities[i][0], velocities[i][1])
                    GameState.playSFX("attack")
                    
                    self.play(self.getAnimation("fly"))
                    self.state = Attack.STATES.FLYING
                    
                case Attack.STATES.FLYING:
                    targetPos = self.calculateTargetPos()
                    
                    self.trigIncrement += 0.1 * self.trigIncrementFactor
                    
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
                    self.vx = math.sin(self.trigIncrement)*self.speedFactor*(GameState.getSpeedMultiplier()-0.3) 
                    self.vy = math.cos(self.trigIncrement)*self.speedFactor*(GameState.getSpeedMultiplier()-0.3) 
                    
                    # failsafe
                    if not 0 < self.x() < 255:
                        self.setX(128)
                    if not 0 < self.y() < 255:
                        self.setY(128)
                        
                    # sometimes randomly invert our movement
                    if not random.randint(0, 200):
                        self.speedFactor *= -1
                        self.targetSpeedFactor *= -1
                        self.trigIncrementFactor *= -1
                    
                    # and make sure to bounce off the walls
                    if not 16 < targetPos.x() < 224:
                        self.speedFactor *= -1
                        self.vx *= -1
                    if not 16 < targetPos.y() < 192:
                        self.speedFactor *= -1
                        self.vy *= -1
                        
                    if not random.randint(0, 200): # sometimes start slowing to attack
                        self.targetSpeedFactor = 0
                        self.play(self.getAnimation("shoot"))
                        self.state = Attack.STATES.PREPARING
                    
                    await self.pause(2, False)
        