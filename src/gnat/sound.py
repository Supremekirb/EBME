import json

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

import src.misc.common as common


class OneShotSoundEffect(QSoundEffect):
    def __init__(self, path: str):
        super().__init__()
        self.setSource(QUrl.fromLocalFile(common.absolutePath(path)))
        self.setLoopCount(0)
        self.setVolume(0.25)

class BGMSoundEffect(QSoundEffect):
    def __init__(self, path: str):
        super().__init__()
        self.setSource(path)
        self.setLoopCount(QSoundEffect.Loop.Infinite)
        self.setVolume(0.25)
    
class SoundManager:
    def __init__(self, path: str):
        self.sfx: dict[str, OneShotSoundEffect] = {}
        self.bgm: dict[str, BGMSoundEffect] = {}
        
        self.currentBGM: BGMSoundEffect = None
        
        with open(path) as file:
            sounds = json.load(file)
            
            for i in sounds["sfx"]:
                self.sfx[i["name"]] = OneShotSoundEffect(i["path"])
                
            for i in sounds["bgm"]:
                self.bgm[i["name"]] = BGMSoundEffect(i["path"])
                
    def pauseBGM(self):
        if self.currentBGM:
            self.currentBGM.setVolume(0)
    
    def resumeBGM(self):
        if self.currentBGM:
            self.currentBGM.setVolume(0.25)
                
    def playBGM(self, name: str):
        """Pass an empty string to stop BGM playback"""
        if name == "":
            bgm = None
        else:
            try:
                bgm = self.bgm[name]
            except KeyError:
                raise ValueError(f"No BGM called {name}!")
        
        if self.currentBGM:
            self.currentBGM.stop()
        
        if bgm:
            bgm.play()
        
        self.currentBGM = bgm
        
        
    def playSFX(self, name: str):
        try:
            sfx = self.sfx[name]
        except KeyError:
            raise ValueError(f"No SFX called {name}!")
        
        sfx.play()