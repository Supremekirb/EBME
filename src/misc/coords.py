import src.misc.common as common


class EBCoords():
    """Class for storing coordinate information. Coordinates are stored as integers in pixel scale.
    
    Create an EBCoords object by passing x and y directly, or using one of the creation functions `EBCoords.fromTYPE(x, y)`.
    Creating an EBCoords object with no arguments will default to (0, 0).
    
    Retrieve coordinate information by accessing `x` and `y` directly, using `coords()` for a tuple, or using `coordsTYPE` functions to get coordinates in a different scale.
    
    Get pixel coordinates rounded to a specific scale using `roundToTYPE()`.
    
    EBCoords supports the following operations with other EBCoords objects:
        - Addition (adds to x and y)
        - Subtraction (subtracts from x and y)
        - Multiplication (multiplies x and y)
        - Division (divides x and y)
        - Floor division (divides x and y and rounds down)
        - Equality (checks if both x and y are the same)
        - Comparison (checks if both x and y are >, <, >=, or <=)
    
    You can also convert it to a string, which returns "(x, y)".
        
    Storing coordinates in this manner helps reduce ambiguity when handling data in different scales.
    Additionally, as it lets objects be placed on the scene without conversion functions being needed."""
    def __init__(self, x: int = 0, y: int = 0):
        self.x = int(x)
        self.y = int(y)
        
    def __add__(self, other: "EBCoords"):
        return EBCoords(self.x + other.x, self.y + other.y)
    def __sub__(self, other: "EBCoords"):
        return EBCoords(self.x - other.x, self.y - other.y)
    def __mul__(self, other: "EBCoords"):
        return EBCoords(self.x * other.x, self.y * other.y)
    def __div__(self, other: "EBCoords"):
        return EBCoords(self.x / other.x, self.y / other.y)
    def __floordiv__(self, other: "EBCoords"):
        return EBCoords(self.x // other.x, self.y // other.y)
    def __eq__(self, other: "EBCoords"):
        return self.x == other.x and self.y == other.y
    def __gt__(self, other: "EBCoords"):
        return self.x > other.x and self.y > other.y
    def __ge__(self, other: "EBCoords"):
        return self.x >= other.x and self.y >= other.y
    def __lt__(self, other: "EBCoords"):
        return self.x < other.x and self.y < other.y
    def __le__(self, other: "EBCoords"):
        return self.x <= other.x and self.y <= other.y
    def __str__(self):
        return f"({self.x}, {self.y})"
    
    def restrictToMap(self) -> None:
        """If coordinates fall outside the EB map range, reduce/increase them to that size."""
        self.x = common.cap(self.x, 0, common.EBMAPWIDTH-1)
        self.y = common.cap(self.y, 0, common.EBMAPHEIGHT-1)
        
    def coords(self) -> tuple[int, int]:
        """Return the coordinates as a tuple."""
        return (self.x, self.y)
    
    def coordsWarp(self) -> tuple[int, int]:
        """Return the coordinates as a tuple of warp coordinates."""
        return (self.x//8, self.y//8)
    
    def coordsTile(self) -> tuple[int, int]:
        """Return the coordinates as a tuple of tile coordinates."""
        return (self.x//32, self.y//32)
    
    def coordsEnemy(self) -> tuple[int, int]:
        """Return the coordinates as a tuple of enemy coordinates."""
        return (self.x//64, self.y//64)
    
    def coordsSector(self) -> tuple[int, int]:
        """Return the coordinates as a tuple of sector coordinates."""
        return (self.x//256, self.y//128)
    
    def coordsBisector(self) -> tuple[int, int]:
        """Return the coordinates as a tuple of bisector coordinates."""
        return (self.x//256, self.y//256)
    
    def roundToWarp(self) -> tuple[int, int]:
        """Return coordinates in pixel scale rounded to warp coordinates."""
        return (self.x-(self.x%8), self.y-(self.y%8))
    
    def roundToTile(self) -> tuple[int, int]:
        """Return coordinates in pixel scale rounded to tile coordinates."""
        return (self.x-(self.x%32), self.y-(self.y%32))
    
    def roundToEnemy(self) -> tuple[int, int]:
        """Return coordinates in pixel scale rounded to enemy coordinates."""
        return (self.x-(self.x%64), self.y-(self.y%64))
    
    def roundToSector(self) -> tuple[int, int]:
        """Return coordinates in pixel scale rounded to sector coordinates."""
        return (self.x-(self.x%256), self.y-(self.y%128))
    
    def roundToBisector(self) -> tuple[int, int]:
        """Return coordinates in pixel scale rounded to bisector coordinates."""
        return (self.x-(self.x%256), self.y-(self.y%256))
    
    @staticmethod
    def fromWarp(x: int, y: int):
        """Create an EBCoords object from warp coordinates."""
        return EBCoords(x*8, y*8)
    
    @staticmethod
    def fromTile(x: int, y: int):
        """Create an EBCoords object from tile coordinates."""
        return EBCoords(x*32, y*32)
    
    @staticmethod
    def fromEnemy(x: int, y: int):
        """Create an EBCoords object from enemy coordinates."""
        return EBCoords(x*64, y*64)
    
    @staticmethod
    def fromSector(x: int, y: int):
        """Create an EBCoords object from sector coordinates."""
        return EBCoords(x*256, y*128)
    
    @staticmethod
    def fromBisector(x: int, y: int):
        """Create an EBCoords object from bisector coordinates."""
        return EBCoords(x*256, y*256)