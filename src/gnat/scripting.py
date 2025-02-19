import asyncio

from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QPixmap

from src.gnat.animation import AnimatedGraphicsItem, Animation, AnimationTimer

loop = asyncio.get_event_loop()

def step():
    loop.call_soon(loop.stop)
    loop.run_forever()
    
async def _frame():
    # 0 awaits the next iteration
    await asyncio.sleep(0)
    
    
class ScriptedAnimatedItem(AnimatedGraphicsItem):
    def __init__(self, animationTimer: AnimationTimer, pixmap: QPixmap, animations: list[Animation]):
        super().__init__(animationTimer, pixmap, animations)
        
        self.vx = 0
        self.vy = 0
        
        loop.create_task(self.script())
    
    async def script(self): # virtual
        while True:
            await self.pause()
    
    async def pause(self, length: int=1, velocityEachFrame: bool = True):
        # set velocityEachFrame to False and length to 2 to replicate the
        # kinda weirdly jerky two-frame movement of the gnats
        # in the original game
        if not velocityEachFrame:
            self.setPos(self.calculateTargetPos())
            
        for i in range(0, length):
            if velocityEachFrame:
                self.setPos(self.calculateTargetPos())
            await _frame()
            
    def calculateTargetPos(self):
        return QPointF(self.pos().x()+self.vx, self.pos().y()+self.vy)