from typing import TYPE_CHECKING

import src.misc.common as common
from src.gnat.animation import AnimationTimer
from src.gnat.scripting import ScriptedAnimatedItem

if TYPE_CHECKING:
    from src.gnat.game_scene import GameScene

# messing around with some interesting
# singleton implementations in python

class GameState:
    INSTANCE = None
    
    def __init__(self, scene: "GameScene", animationTimer: AnimationTimer):
        GameState.INSTANCE = self
        
        self.gameScene = scene
        self.animationTimer = animationTimer
        
        self.score = 100
        self.lives = 3
        self.level = 1
        self.rank = 0
        
        self.enemiesOnScreen: set[ScriptedAnimatedItem] = set()
        
        
    @staticmethod
    def getAnimationTimer():
        inst = GameState.INSTANCE
        return inst.animationTimer
        
    @staticmethod
    def addEnemy(enemy: ScriptedAnimatedItem):
        inst = GameState.INSTANCE
        inst.enemiesOnScreen.add(enemy)
        inst.gameScene.addItem(enemy)   
    @staticmethod
    def removeEnemy(enemy: ScriptedAnimatedItem):
        inst = GameState.INSTANCE
        inst.enemiesOnScreen.discard(enemy)
        inst.gameScene.removeItem(enemy)
        inst.gameScene.levelSpawnManager.onEnemyDeath(enemy)
        
        
    @staticmethod
    def addLife():
        inst = GameState.INSTANCE
        if inst.lives <= 6:
            inst.lives += 1
            inst.gameScene.livesItem.setLifeCount(inst.lives)
    @staticmethod
    def takeLife():
        inst = GameState.INSTANCE
        if inst.lives > 0:
            inst.lives -= 1
            inst.gameScene.livesItem.setLifeCount(inst.lives)
            
        if inst.lives == 0:
            pass # game over logic 
    
    
    @staticmethod
    def resetScore():
        inst = GameState.INSTANCE
        inst.score = 100
        inst.gameScene.scoreItem.setScore(inst.score)
    @staticmethod
    def takeScore():
        inst = GameState.INSTANCE
        if inst.score > 0:
            inst.score -= 1
            inst.gameScene.scoreItem.setScore(inst.score)
            if inst.score in (25, 50, 75):
                inst.gameScene.spawnLife()
        else:
            inst.nextLevel()
        
        
    @staticmethod
    def nextLevel():
        inst = GameState.INSTANCE
        if inst.level < 3:
            inst.level += 1
            pass # other next level logic
        else:
            inst.addRank()
            inst.level = 1
            pass # other next level logic
        
        inst.gameScene.newLevel(inst.level)
        inst.resetScore()
        
    @staticmethod
    def addRank():
        inst = GameState.INSTANCE
        if inst.rank < 16:
            inst.rank += 1
            inst.gameScene.rankItem.setRank(inst.rank)
        else:
            pass # win logic
    @staticmethod
    def resetRank():
        inst = GameState.INSTANCE
        inst.rank = 0
        inst.gameScene.rankItem.setRank(0)
        