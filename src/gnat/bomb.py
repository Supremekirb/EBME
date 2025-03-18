import math
import random
from enum import IntEnum

from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.animation import loadAnimations
from src.gnat.game_state import GameState
from src.gnat.scripting import ScriptedAnimatedItem


class Bomb(ScriptedAnimatedItem):
    ANIMATIONS = loadAnimations(common.absolutePath("assets/gnat/animations/bomb.json"))
    STATES = IntEnum("STATES", ["FLYING",
                                "CHASING",
                                "SPAWNING",
                                "EXPLODING",
                                "DYING"])
    
    def __init__(self):
        super().__init__(GameState.getAnimationTimer(), QPixmap(":/gnat/spritesheets/bomb.png"), Bomb.ANIMATIONS)
        self.setZValue(common.GNATZVALUES.GAMEPLAY)
        
        self.play(self.getAnimation("fly"))
        
        self.trigIncrement = 1
        self.trigIncrementFactor = 1
        self.speedFactor = 0
        self.targetSpeedFactor = 0
        
        self.fuseTimer = 60
        self.justExploded = False
        
        self.state = Bomb.STATES.SPAWNING
        
        # random position on the sides
        self.setX(random.choice(list(range(-32, -16)) + list(range(256, 272))))
        self.setY(random.randint(-32, 256))
        
        GameState.addEnemy(self)

    def swatted(self):
        if self.state not in (Bomb.STATES.DYING, Bomb.STATES.EXPLODING):
            self.vx = 0
            self.vy = 0
            self.state = Bomb.STATES.DYING
            self.play(self.getAnimation("death"))
            GameState.playSFX("bombdie")
            GameState.takeScore()
            # remove after we have fallen
            return True
        return False
    
    def onNonLoopingAnimationEnd(self, last):
        if last == self.getAnimation("boom"):
            self.state = Bomb.STATES.SPAWNING
            # reset pos
            self.setX(random.choice(list(range(-32, -16)) + list(range(256, 272))))
            self.setY(random.randint(-32, 256))
            self.play(self.getAnimation("fly"))
            self.fuseTimer = 60
    
    async def script(self):
        while True:
            match self.state:
                case Bomb.STATES.DYING:
                    self.vy += 0.5
                    if self.y() > 224:
                        GameState.playSFX("bombland")
                        GameState.removeEnemy(self)
                        return
                    await self.pause()
                
                case Bomb.STATES.SPAWNING:
                    if int(self.x()) in range(36, 220) and int(self.y()) in range(36, 188):
                        self.state = Bomb.STATES.FLYING
                        
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
                
                case Bomb.STATES.FLYING:
                    if GameState.getScene().getProximityToHand(self.pos()) < 50:
                        self.play(self.getAnimation("fuse"))
                        self.state = Bomb.STATES.CHASING
                    
                    else:
                        targetPos = self.calculateTargetPos()
                    
                        self.trigIncrement += 0.2 * self.trigIncrementFactor
                        
                        if self.speedFactor > self.targetSpeedFactor:
                            self.speedFactor -= 1
                        elif self.speedFactor < self.targetSpeedFactor:
                            self.speedFactor += 1
                        else: # they're equal
                            if not random.randint(0, 50) or self.targetSpeedFactor == 0:
                                # can stay going in a circle, but dont stay still
                                # goes a little slower than the regular gnat's max
                                self.targetSpeedFactor = random.randint(-7, 7)
                        
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
                            self.trigIncrementFactor *= -1
                        
                        # and make sure to bounce off the walls
                        if not 16 < targetPos.x() < 224:
                            self.speedFactor *= -1
                            self.vx *= -1
                        if not 16 < targetPos.y() < 192:
                            self.speedFactor *= -1
                            self.vy *= -1
                    
                    await self.pause(2, False)            
                    
                
                case Bomb.STATES.CHASING:
                    self.fuseTimer -= 1
                    
                    if self.fuseTimer < 1:
                        self.play(self.getAnimation("boom"))
                        GameState.playSFX("boom")
                        self.state = Bomb.STATES.EXPLODING
                        
                    # move towards hand
                    angle = GameState.getScene().getAngleToHand(self.pos())
                    self.vx = math.sin(angle) * 6
                    self.vy = math.cos(angle) * 6 
                    
                    await self.pause(2, False)
                
                case Bomb.STATES.EXPLODING:
                    # move towards hand also
                    angle = GameState.getScene().getAngleToHand(self.pos())
                    self.vx = math.sin(angle) * 6
                    self.vy = math.cos(angle) * 6
                    
                    if GameState.getScene().isIntersectingWithHand(self):
                        GameState.getScene().handCursor.hurt()
                    
                    await self.pause(2, False)
                        