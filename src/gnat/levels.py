import json
import typing

from src.gnat.gnat import Gnat
from src.gnat.spawner import Spawner
from src.gnat.bomb import Bomb
from src.gnat.attack import Attack


class LevelSpawnManger:
    def __init__(self, fp: str):
        self.waves: list[Wave] = []
        self.currentWave: Wave = None
        
        self.read(fp)
        
    def read(self, fp: str):
        with open(fp) as file:
            levelObj = json.load(file)
            for wave in levelObj["waves"]:
                enemies = []
                for enemy in wave["enemies"]:
                    enemies.append(EnemyFactory(enemy["name"], enemy["max"], enemy["count"]))
                
                self.waves.append(Wave(enemies))
            self.currentWave = self.waves[0]
                
    def onEnemyDeath(self, enemy):
        self.currentWave.onEnemyDeath(enemy) # signal/slot design pattern could come in handy but im lazy
        
        if self.currentWave.finished:
            currentIndex = self.waves.index(self.currentWave)
            if currentIndex+1 < len(self.waves):
                self.currentWave = self.waves[currentIndex+1]
                self.startSpawning()
                
    def startSpawning(self):
        self.currentWave.onEnemyDeath(None) # this is a hacky way to trigger enemy spawns.
                # why am I making hacky solutions in a file less than 100 lines long?
                # april fool's, I guess
        
class EnemyFactory:
    # i dont think this is actually what a factory is but uhhh i dont care
    def __init__(self, type: typing.Literal["gnat", "spawner", "bomb", "attack"], max: int, count: int):
        match type:
            case "gnat":
                self.enemyType = Gnat
            case "spawner":
                self.enemyType = Spawner
            case "bomb":
                self.enemyType = Bomb
            case "attack":
                self.enemyType = Attack
            case _:
                raise ValueError(f"'{type}' not a valid enemy type!")
        
        self.max = max
        self.count = count
        
        self.used = 0
        self.current = 0
        
        self.finished = False
        
    def onEnemyDeath(self, enemy):
        if isinstance(enemy, self.enemyType):
            self.current -= 1

        while self.used < self.count and self.current < self.max:
            self.enemyType() # create a new one, automatially adds to scene
            self.used += 1
            self.current += 1
        
        if self.used == self.count and self.current == 0:
            self.finished = True
            

class Wave:
    def __init__(self, enemyFactories: list[EnemyFactory]):
        self.factories = enemyFactories
        self.finished = False
    
    def onEnemyDeath(self, enemy):
        for i in self.factories:
            i.onEnemyDeath(enemy)
            
        if all(i.finished for i in self.factories):
            self.finished = True