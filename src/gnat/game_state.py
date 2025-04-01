from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPixmap

import src.misc.common as common
from src.gnat.cutscene import (GameOverCutsceneHandler,
                               RoundStartCutsceneHandler)
from src.gnat.levels import LevelManager
from src.gnat.scripting import ScriptedAnimatedItem
from src.gnat.sound import SoundManager

if TYPE_CHECKING:
    from src.gnat.game_scene import GameScene

# messing around with some interesting
# singleton implementations in python

class GameState:
    INSTANCE = None
    
    def __init__(self, scene: "GameScene"):
        GameState.INSTANCE = self
        
        self.scene = scene
        self.animationTimer = self.scene.animationTimer
        
        self.levelManager = LevelManager(common.absolutePath("assets/gnat/levels/1.json"))
        self.soundManager = SoundManager(common.absolutePath("assets/gnat/sound/sound.json"))
        
        self.score = 100
        self.lives = 3
        self.level = 0 # increments to 1
        self.rank = 0
        
        # After init, we need to wait until
        # the user opens this tab for the first time,
        # then we will start for real.
        self.awaitingFirstBoot = True
        self.scene.screenFaderItem.alpha = 255
        self.scene.screenFaderItem.targetAlpha = 255
    
    @staticmethod
    def switchedToTab():
        inst = GameState.INSTANCE
        if inst.awaitingFirstBoot:
            GameState.beginNextLevel()
            inst.awaitingFirstBoot = False
    
    @staticmethod
    def playSFX(name: str):
        inst = GameState.INSTANCE
        inst.soundManager.playSFX(name)
    @staticmethod
    def playBGM(name: str):
        inst = GameState.INSTANCE
        inst.soundManager.playBGM(name)
    @staticmethod
    def playBossBGM():
        inst = GameState.INSTANCE
        if inst.rank == 15:
            if inst.level == 3:
                GameState.playBGM("finalboss")
            else:
                GameState.playBGM("hardboss")
        else:
            GameState.playBGM("boss")
    
    @staticmethod
    def pauseBGM():
        inst = GameState.INSTANCE
        inst.soundManager.pauseBGM()
    @staticmethod
    def resumeBGM():
        inst = GameState.INSTANCE
        inst.soundManager.resumeBGM()
    @staticmethod
    def stopBGM():
        inst = GameState.INSTANCE
        inst.soundManager.stopBGM()
        
    @staticmethod
    def playCurrentLevelBGM():
        inst = GameState.INSTANCE
        if inst.rank == 15:
            inst.soundManager.playBGM(f"hard{str(inst.level)}")
        else:
            inst.soundManager.playBGM(f"regular{str(inst.level)}")
        
        
    @staticmethod
    def getAnimationTimer():
        inst = GameState.INSTANCE
        return inst.animationTimer

    @staticmethod
    def getScene():
        inst = GameState.INSTANCE
        return inst.scene
    
    @staticmethod
    def resetGame():
        inst = GameState.INSTANCE
        inst.getScene().clearEnemies()
        inst.resetRank()
        inst.resetScore()
        inst.level = 0
        inst.lives = 3
        inst.getScene().livesItem.setLifeCount(inst.lives)
        inst.beginNextLevel()
    
    @staticmethod
    def pauseGame(pos: QPoint = QPoint(128, 122)):
        inst = GameState.INSTANCE
        if not inst.awaitingFirstBoot:
            inst.animationTimer.pause()
            inst.scene.handCursor.hide()
            inst.scene.pauseScreen.onPause(pos)
            inst.pauseBGM()
    @staticmethod
    def resumeGame():
        inst = GameState.INSTANCE
        inst.animationTimer.resume()
        inst.resumeBGM()
        
        
    @staticmethod
    def addEnemy(enemy: ScriptedAnimatedItem):
        inst = GameState.INSTANCE
        inst.scene.addItem(enemy)   
    @staticmethod
    def removeEnemy(enemy: ScriptedAnimatedItem):
        inst = GameState.INSTANCE
        # inst.gameScene.removeItem(enemy)
        inst.levelManager.onEnemyDeath(enemy)
        enemy.deleteLater()
        
        
    @staticmethod
    def addLife():
        inst = GameState.INSTANCE
        if inst.lives < 6:
            inst.lives += 1
            inst.scene.livesItem.setLifeCount(inst.lives)
    @staticmethod
    def takeLife():
        inst = GameState.INSTANCE
        if inst.lives >= 0:
            inst.lives -= 1
            inst.scene.livesItem.setLifeCount(inst.lives)
            
        if inst.lives < 0:
            for i in inst.getScene().items():
                # if you're writing code like this,
                # then it's time to throw in the towel    
                if hasattr(i, "STATES") and hasattr(i, "state"):
                    try:
                        i.state = i.STATES.LAUGHING
                    except AttributeError:
                        pass
            GameOverCutsceneHandler(inst.resetGame)
    
    
    @staticmethod
    def resetScore():
        inst = GameState.INSTANCE
        inst.score = 100
        inst.scene.scoreItem.setScore(inst.score)
        inst.scene.scoreItem.show()
    @staticmethod
    def takeScore():
        inst = GameState.INSTANCE
        if inst.score > 1:
            inst.score -= 1
            inst.scene.scoreItem.setScore(inst.score)
            if inst.rank == 0:
                if inst.score in (25, 50, 75):
                    inst.scene.spawnLife()
            else:
                if inst.score == 90:
                    inst.scene.spawnLife()
        else:
            inst.scene.scoreItem.hide()
            inst.getScene().spawnBoss()
    
    @staticmethod
    def beginNextLevel():
        inst = GameState.INSTANCE       
        if inst.level < 3:
            inst.level += 1
            pass # other next level logic
        else:
            inst.addRank()
            inst.level = 1
            pass # other next level logic
        
        inst.resetScore()
        inst.getScene().clearEnemies()
        RoundStartCutsceneHandler("LEVEL", str(inst.level), callback=GameState._nextLevel)
    
    @staticmethod
    def setLevelBackground():
        inst = GameState.INSTANCE
        inst.getScene().setBackgroundBrush(QPixmap(f":/gnat/spritesheets/bg{inst.level}.png"))
        
    @staticmethod
    def _nextLevel():
        inst = GameState.INSTANCE
        inst.levelManager = LevelManager(common.absolutePath(f"assets/gnat/levels/{str(inst.level)}.json"))
        inst.levelManager.startSpawning()
        
        # Boss debug
        # (comment out above stuff and uncomment this)
        # inst.score = 1
        # inst.takeScore()
        
    @staticmethod
    def getSpeedMultiplier():
        inst = GameState.INSTANCE
        return (inst.level * 0.5) + 0.5
        # lv1 --> x1
        # lv2 --> x1.5
        # lv3 --> x2
        
    @staticmethod
    def addRank():
        inst = GameState.INSTANCE
        if inst.rank < 15:
            inst.rank += 1
            inst.scene.rankItem.setRank(inst.rank)
        else:
            pass # win logic
    @staticmethod
    def resetRank():
        inst = GameState.INSTANCE
        inst.rank = 0
        inst.scene.rankItem.setRank(0)
        