from enum import IntEnum
from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush, QColor

class SpriteObjectOrigin(IntEnum):
    BOTTOM_LEFT = 0
    TOP_LEFT = 1
    BOTTOM_RIGHT = 2
    TOP_RIGHT = 3

class HitBoxType(IntEnum):
    RECT = 0
    ELLIPSE = 1
    POLYGON = 2

class SpriteItem:
    def __init__(self, view, rect, brush):
        self.rect = rect
        self.brush = brush
        self.view = view
        self.graphicsItem = None

        self.addToView()

    def addToView(self):
        self.graphicsItem = self.view.addRect(self.rect, QPen(Qt.black, 0), self.brush)

    def removeFromView(self):
        if self.graphicsItem:
            self.view.removeItem(self.graphicsItem)
            self.graphicsItem = None

class HitBox:
    def __init__(self, hitBoxType = HitBoxType.RECT):
        self.hitBoxType = hitBoxType
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0
        self.shape = None

    def asdict(self):
        return {
            'type': self.hitBoxType,
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'shape': self.shape
        }

    @staticmethod
    def fromdict(obj):
        return HitBox()

class SpriteObject:
    def __init__(self,
                 name,
                 key = None,
                 objType = None,
                 tiles = [],
                 originMode = SpriteObjectOrigin.BOTTOM_LEFT,
                 renderTiles = True,
                 hasCollision = False,
                 extraProperties = {}):
        self.name = name

        if key is None:
           key = lower(name).replace(' ', '_')

        self.key = key
        self.objType = objType
        self.tiles = tiles
        self.originMode = originMode
        self.renderTiles = renderTiles
        self.hasCollision = hasCollision
        if self.hasCollision:
            self.hitBox = HitBox()

        self.extraProperties = extraProperties

    def asdict(self):
        data = {
            'name': self.name,
            'key': self.key,
            'type': self.objType,
            'tiles': self.tiles,
            'originMode': int(self.originMode),
            'renderTiles': self.renderTiles,
            'hasCollision': self.hasCollision
        }

        if self.hasCollision:
            data['hitbox'] = self.hitBox.asdict()

        return data

    @staticmethod
    def fromdict(obj):
        return SpriteObject(name = obj['name'],
                            key = obj['key'],
                            objType = obj['type'],
                            tiles = obj['tiles'],
                            originMode = SpriteObjectOrigin(obj['originMode']),
                            renderTiles = obj['renderTiles'],
                            hasCollision = obj['hasCollision'])