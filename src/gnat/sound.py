import asyncio
import json

import pygame

import src.misc.common as common

# Using PyGame here as opposed to Qt because
# Qt's QSoundEffect class causes weird 
# stuttering when sound effects are played
# for some reason, at least for me.

pygame.init()
pygame.mixer.init()

loop = asyncio.get_event_loop()

async def _tick():
    await asyncio.sleep(0)


class SoundEffect(pygame.mixer.Sound):
    def __init__(self, path: str):
        super().__init__(common.absolutePath(path))    


class BGM():
    def __init__(self, path: str, loop: float):
        self.path = path
        self.loop = loop
        self.running = False
    
    def load(self):
        pygame.mixer.music.unload()
        pygame.mixer.music.load(common.absolutePath(self.path), "ogg")
        
    def play(self):
        pygame.mixer.music.play(0)
        self.running = True
        loop.create_task(self._musicLoopTask())
        
    def stop(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        self.running = False # exits loop
        
    def pause(self):
        pygame.mixer.music.pause()
    
    def resume(self):
        pygame.mixer.music.unpause()
        
    async def _musicLoopTask(self):
        while self.running:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.play(0, self.loop)
            await _tick()
                

class SoundManager:
    def __init__(self, path: str):
        self.sfx: dict[str, SoundEffect] = {}
        self.bgm: dict[str, BGM] = {}
        
        self.currentBGM: BGM = None
        
        with open(path) as file:
            sounds = json.load(file)
            
            for i in sounds["sfx"]:
                self.sfx[i["name"]] = SoundEffect(i["path"])
                
            for i in sounds["bgm"]:
                self.bgm[i["name"]] = BGM(i["path"], i["loop"])
                
    def playBGM(self, name: str):
        try:
            bgm = self.bgm[name]
        except KeyError:
            raise ValueError(f"No BGM called {name}!")
        
        if self.currentBGM: self.currentBGM.stop()
        
        self.currentBGM = bgm
        
        self.currentBGM.load()
        self.currentBGM.play()
        
        
    def playSFX(self, name: str):
        try:
            sfx = self.sfx[name]
        except KeyError:
            raise ValueError(f"No SFX called {name}!")
        
        sfx.play()