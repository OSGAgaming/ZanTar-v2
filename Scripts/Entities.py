import math
from MyLib import *


class EntityHost:
    """
    An object which stores entities, and appends entities to their respective systems
    """
    def __init__(self, window):
        self.entities = []
        self.window = window
        self.onInit()

        self.systems = {}
        self.updating = True
        # Adding systems
        self.appendSystem("VerletBody", VerletSystem())
        self.appendSystem("Body2D", CollisionSystem())

    def queryEntity(self, entity):
        """
        Checks modules entities has, and appends entity to list of systems defined on initialising
        :param entity: Entity being queried
        :return:
        """
        for module in entity.modules.keys():
            if module in self.systems.keys():
                self.systems[module].appendEntity(entity)

    def appendSystem(self, name, system):
        system.parent = self
        self.systems[name] = system

    def update(self):
        """
        Updates all entities and systems
        :return:
        """
        if self.updating:
            for entity in self.entities:
                entity.deltaTime = self.window.deltaAverage
                entity.update()

            for key in self.systems:
                self.systems[key].update()

    def addEntity(self, entity):
        """Adds and queries entities"""
        entity.window = self.window
        entity.onInit(entity)
        self.entities.append(entity)

        self.queryEntity(entity)

    def onInit(self):
        pass


class EntityModifier:
    """Otherwise known as a module, it helps entity host subscribe entities to systems
       Can also have fields"""
    def __init__(self):
        self.entity = None

    def onInit(self):
        pass

    def onUpdate(self, entity):
        pass


class EntitySystem:
    """Centralised host that controls behaviour of entities with a specific module"""
    def __init__(self):
        self.entities = []
        self.parent = None

    def onInit(self):
        pass

    def update(self):
        pass

    def appendEntity(self, entity):
        self.entities.append(entity)


class VerletSystem(EntitySystem):
    """System for Verlet Integration"""
    def __init__(self):
        self.constraints = []
        self.lines = {}

        self.debugColor = "black"

        EntitySystem.__init__(self)

    def appendEntity(self, entity):
        self.entities.append(entity)

    def updatePoints(self):
        """Verlet integration uses delta position for velocity
           This method also applies an entity adjustable gravity
           and air resistance"""
        for entity in self.entities:
            vb = entity.getModule("VerletBody")
            if not vb.isStatic:
                rb = entity.getModule("RigidBody")

                # velocity for rigid body will no longer be called

                rb.vel.x = (rb.pos.x - vb.oldPos.x)
                rb.vel.y = (rb.pos.y - vb.oldPos.y)

                vb.oldPos.x = rb.pos.x
                vb.oldPos.y = rb.pos.y

                if not entity.updating:
                    continue

                rb.pos.x += rb.vel.x
                rb.pos.y += rb.vel.y

                rb.pos.y += rb.mass * entity.deltaTime

    def bindPoints(self, p1, p2, length):
        """Adds constraints to two points"""

        self.constraints.append(Constraint((p1, p2), length))

        p1rb = p1.getModule("RigidBody")
        p2rb = p2.getModule("RigidBody")

        self.lines[(p1, p2)] = self.parent.window.canvas.create_line(p1rb.pos.x, p1rb.pos.y, p2rb.pos.x, p2rb.pos.y,
                                                                     fill="black", width=3)

    def updateConstraints(self):
        """Acts on constraints"""
        for constraint in self.constraints:

            p1 = constraint.points[0]
            p2 = constraint.points[1]

            p1rb = p1.getModule("RigidBody")
            p1vb = p1.getModule("VerletBody")

            p2rb = p2.getModule("RigidBody")
            p2vb = p2.getModule("VerletBody")

            dx = p2rb.pos.x - p1rb.pos.x
            dy = p2rb.pos.y - p1rb.pos.y

            # gets percentage increase of length a constraint has increased by, it then
            # reconfigures the two constrained points such that the new distance
            # is the (old distance + percIncrease * dxdy)

            # It works surprisingly well!

            currentLength = math.sqrt(dx * dx + dy * dy)
            deltaLength = currentLength - constraint.length
            perc = deltaLength / currentLength * 0.5

            offsetX = perc * dx
            offsetY = perc * dy

            # Check if point is static

            if not p1vb.isStatic:
                p1rb.pos.x += offsetX
                p1rb.pos.y += offsetY

            if not p2vb.isStatic:
                p2rb.pos.x -= offsetX
                p2rb.pos.y -= offsetY

            win = self.parent.window
            cPos = win.scene.getCameraPosition()

            win.canvas.coords(self.lines[(p1, p2)], p1rb.pos.x - cPos.x, p1rb.pos.y - cPos.y, p2rb.pos.x - cPos.x,
                              p2rb.pos.y - cPos.y)
            win.canvas.itemconfig(self.lines[(p1, p2)], fill=self.debugColor)

    def update(self):
        self.updatePoints()
        self.updateConstraints()


class CollisionSystem(EntitySystem):
    """System for AABB collision and collision response"""
    def __init__(self):
        EntitySystem.__init__(self)

    def broadPhase(self):
        """
        Every entity is checked for collision with every other entity :(
        :return:
        """
        # n^2 implementation, not enough time for partitioning
        for bodies in self.entities:
            bodies.getModule("Body2D").colliding = False
            bodies.getModule("Body2D").collidingDown = False

        for body1 in self.entities:
            for body2 in self.entities:
                if body1 != body2 and rectIntersecting(body1, body2):
                    AABBresolution(body1, body2)

    def update(self):
        self.broadPhase()


class RigidBody(EntityModifier):
    """
    Defines position in space, velocity, gravity and drag
    """
    def __init__(self, pos=Vector2(0, 0), vel=Vector2(0, 0), ifSimulated=True, mass=0.001, drag=1):
        self.pos = pos
        self.vel = vel
        self.mass = mass
        self.drag = drag
        self.ifSimulated = ifSimulated
        EntityModifier.__init__(self)

    def onUpdate(self, entity):
        if self.ifSimulated:
            self.pos.x += self.vel.x
            self.pos.y += self.vel.y
            self.vel.y += self.mass * entity.deltaTime

            self.vel.x *= self.drag
            self.vel.y *= self.drag


class VerletBody(EntityModifier):
    """Extension of a rigid body that creates extra fields for
       Verlet Integration (see VerletSystem)"""
    def __init__(self, oldPos, isStatic=False, hasGravity=True):
        self.oldPos = oldPos
        self.isStatic = isStatic
        self.hasGravity = hasGravity
        EntityModifier.__init__(self)


class Body2D(EntityModifier):
    """Defines area for an entity"""
    def __init__(self, bounds):
        self.bounds = bounds
        self.colliding = False
        self.collidingDown = False

        EntityModifier.__init__(self)

    def width(self):
        return self.bounds.x

    def height(self):
        return self.bounds.y

    def right(self, entity):
        return entity.getModule("RigidBody").pos.x + self.bounds.x

    def bottom(self, entity):
        return entity.getModule("RigidBody").pos.y + self.bounds.y


class Constraint:
    """A class for holding points and target length
       To be used in tandem with VerletSystem"""
    def __init__(self, points, length):
        self.points = points
        self.length = length


class Entity:
    """Entity that only holds modules
       It unfortunately holds rb for ease of use,
       which breaks the ESC-Esque architecture
       """
    def __init__(self, modules):
        self.window = None
        # TODO: Move to Entity Host
        self.deltaTime = 1

        self.entityFields = {}
        self.modules = {}

        self.onUpdate = Event()
        self.onInit = Event()
        self.updating = True
        for module in modules:
            self.modules[module.__class__.__name__] = module

        self.rb = None
        if self.hasModule("RigidBody"):
            self.rb = self.getModule("RigidBody")

    def getCanvas(self):
        return self.window.canvas

    def getModule(self, moduleName):
        return self.modules[moduleName]

    def hasModule(self, moduleName):
        return moduleName in self.modules

    def update(self):
        self.onUpdate(self)

        if not self.updating:
            return

        for key in self.modules:
            self.modules[key].onUpdate(self)

    # Gets velocity if pos exists
    def pos(self):
        if self.rb is not None:
            return self.rb.pos
        else:
            return None

    # Gets velocity if rb exists
    def vel(self):
        if self.rb is not None:
            return self.rb.vel
        else:
            return None
