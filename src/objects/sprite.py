from PIL import Image, ImageQt


class Sprite:
    """Sprite image and rendering methods"""
    def __init__(self, id: int, size: tuple[int, int], length: int, collisionHorizontal: tuple[int, int],
                 collisionVertical: tuple[int, int], swimFlags: tuple[bool], img: Image.Image):
        self.id = id
        self.size = size
        self.length = length
        self.collisionHorizontal = collisionHorizontal
        self.collisionVertical = collisionVertical
        self.swimFlags = swimFlags
        
        self.img = img
        
    def renderFacingImg(self, dir: int, anim: int=0) -> Image.Image:
        """Get the image of a frame from a sprite group, given direction

        Args:
            dir (int): direction (see DIRECTION8 in common.py)

        Returns:
            Image: the image
        """
        
        if anim != 0 and anim != 1:
            raise ValueError("Animation value must be 0 or 1!")

        match dir:
            # sprite group layout:
            # UU RR
            # DD LL
            # UR DR
            # DL UL
            # note that each has two frames also
            case 0: # up
                topLeftX = 0 + anim*self.size[0]
                topLeftY = 0
            case 1: # up-right
                topLeftX = 0 + anim*self.size[0]
                topLeftY = self.size[1]*2
            case 2: # right
                topLeftX = self.size[0]*2 + anim*self.size[0]
                topLeftY = 0
            case 3: # down-right
                topLeftX = self.size[0]*2 + anim*self.size[0]
                topLeftY = self.size[1]*2
            case 4: # down
                topLeftX = 0 + anim*self.size[0]
                topLeftY = self.size[1]
            case 5: # down-left
                topLeftX = 0 + anim*self.size[0]
                topLeftY = self.size[1]*3
            case 6: # left
                topLeftX = self.size[0]*2 + anim*self.size[0]
                topLeftY = self.size[1]
            case 7: # up-left
                topLeftX = self.size[0]*2 + anim*self.size[0]
                topLeftY = self.size[1]*3

            case _:
                raise ValueError(f"Invalid direction (must be 0-7, recieved {dir})")

        # topLeftX = dir*self.size[0]*2 if dir < 2 else (dir-2)*self.size[0]*2
        # topLeftY = 0 if dir < 2 else self.size[1]
        return self.img.crop((topLeftX, topLeftY, topLeftX+self.size[0], topLeftY+self.size[1]))
    
    def getFacingCollision(self, dir: int) -> tuple[int, int]:
        if (dir == 0 or 2) or dir >= 4: # TODO test if this is so
            return self.collisionVertical
        else: return self.collisionHorizontal
        
    def getSwimFlag(self, dir: int, anim: int) -> bool:
        dir %= 8
        anim %= 1
        if len(self.swimFlags) == 9:
            if dir == 5:
                return self.swimFlags[8]
            dir -= dir%2
            return self.swimFlags[dir + anim]
        elif len(self.swimFlags) == 8:
            dir -= dir%2
            return self.swimFlags[dir + anim]
        return self.swimFlags[dir*2 + anim]

class BattleSprite:
    """Battle sprite. mostly just the image tbh"""
    def __init__(self, id: int, img: ImageQt.ImageQt):
        self.id = id
        self.img = img