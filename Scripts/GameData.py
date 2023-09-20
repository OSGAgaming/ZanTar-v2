import copy
import math
import random
import time

from Entities import *
from MyLib import *
from Window import *
from Assets import *


class GameData:
    """
    A class that represents all data to be saved
    Can be thought of as an instantiable save file

    SAVE DATA INCLUDES
    levelsUnlocked: level index of last completed level
    controls: Game controls. Not encompassing Menu controls
    bossKey, cheatCode (not all are in here)
    leaderboard: dict of initals -> score (not sorted)
    initials: current initials to see where you are on leaderboard at any given time
    currentScore: Score accumulated when progressing. Will always be stored if continue is always pressed
    """

    def __init__(self):
        # default bindings
        self.metaData = {"levelsUnlocked": 0,
                         "controls": {"left": "a", "right": "d", "jump": "w", "grapple": "e", "flip": "f"},
                         "bossKey": "1",
                         "cheatCode": "2",
                         "leaderBoard": {},
                         "initials": "NA",
                         "currentScore": 0
                         }

    def dataFromHeader(self, header, data):
        index = data.find(header)
        return data[data.find("[", index + 1) + 1:data.find("]", index + 1)]

    def read(self, file):
        with open(file, 'r') as f:

            data = f.read()

            levelHeader = "Levels:"
            controlHeader = "Controls:"
            bossHeader = "BossKey:"
            cheatHeader = "CheatCode:"
            scoreHeader = "Scores:"
            initialHeader = "Initials:"
            currentScoreHeader = "CurrentScore:"

            levelData = self.dataFromHeader(levelHeader, data)
            self.metaData["levelsUnlocked"] = int(levelData)

            controlData = self.dataFromHeader(controlHeader, data)
            controlDict = controlData.split(",")
            for i in range(int(len(controlDict) / 2)):
                index = i * 2
                self.metaData["controls"][controlDict[index]] = controlDict[index + 1]

            self.metaData["bossKey"] = self.dataFromHeader(bossHeader, data)
            self.metaData["cheatCode"] = self.dataFromHeader(cheatHeader, data)

            scoreData = self.dataFromHeader(scoreHeader, data)
            scoreDict = scoreData.split(",")
            for i in range(int(len(scoreDict) / 2)):
                index = i * 2
                self.metaData["leaderBoard"][scoreDict[index]] = scoreDict[index + 1]

            self.metaData["initials"] = self.dataFromHeader(initialHeader, data)
            self.metaData["currentScore"] = int(self.dataFromHeader(currentScoreHeader, data))

    def write(self, file):
        with open(file, 'w') as f:
            f.writelines("Levels:[" + str(self.metaData["levelsUnlocked"]) + "]\n")

            controls = ""
            for key, value in self.metaData["controls"].items():
                controls += ("" if controls == "" else ",") + key + "," + value
            f.writelines("Controls:[" + controls + "]\n")

            f.writelines("BossKey:[" + self.metaData["bossKey"] + "]\n")
            f.writelines("CheatCode:[" + self.metaData["cheatCode"] + "]\n")

            scores = ""
            for key, value in self.metaData["leaderBoard"].items():
                scores += ("" if scores == "" else ",") + key + "," + str(value)

            f.writelines("Scores:[" + scores + "]\n")

            f.writelines("Initials:[" + self.metaData["initials"] + "]\n")
            f.writelines("CurrentScore:[" + str(self.metaData["currentScore"]) + "]\n")


# Game data to use
data = GameData()

# All game states
FlipMode = False
CheatMode = False
BossMode = False

# Array containing all keys pressed
# Does not work for linux???
# Pray that they do not tell me to do it in lab systems
currentKeysPressed = []

mouseX = 0
mouseY = 0


def motion(event):
    """
    Event that updates mouseX and Y every time the mouse is moved
    :param event: Passed mouse info
    :return:
    """
    global mouseX
    global mouseY
    mouseX, mouseY = event.x, event.y


def on_event(event):
    """
    Event that tracks if key presses, and adds them to an array
    :param event: Passed key info
    :return:
    """
    global currentKeysPressed
    text = event.char if event.num == '??' else event.num
    if text not in currentKeysPressed:
        currentKeysPressed.append(text)


def on_release(event):
    """
    Event that tracks if key is released, then removes key from array
    :param event: Passed key info
    :return:
    """
    global currentKeysPressed
    text = event.char if event.num == '??' else event.num
    if text in currentKeysPressed:
        currentKeysPressed.remove(text)


def sqaureEntityUpdate(entity, camera):
    """
    Update info for squares
    :param entity: Bound entity
    :param camera: Offset
    :return:
    """
    rb = entity.getModule("RigidBody")
    entity.getCanvas().moveto(entity.entityFields["rect"], rb.pos.x - camera.x, rb.pos.y - camera.y)

    entity.window.canvas.itemconfig(entity.entityFields["rect"], fill="white" if FlipMode else "black",
                                    outline="white" if FlipMode else "black")
    if FlipMode:
        entity.updating = False
    else:
        entity.updating = True


def sqaureEntityInitialise(entity):
    """
    Load info for squares
    :param entity: Bound entity
    :return:
    """
    sizeOfBox = Vector2(2, 2)
    if entity.hasModule("Body2D"):
        sizeOfBox = entity.getModule("Body2D").bounds
    entity.entityFields["rect"] = entity.window.canvas.create_rectangle(0, 0, sizeOfBox.x, sizeOfBox.y, outline="black",
                                                                        fill="black")


def spriteEntityInitialise(entity, image):
    """
    Sprite Load event
    :param entity: Bound entity
    :param image: Sprite attached
    :return:
    """
    entity.entityFields["sprite"] = image
    entity.entityFields["rect"] = entity.window.canvas.create_image(0, 0, image=entity.entityFields["sprite"],
                                                                    anchor=NW)


def spriteEntityUpdate(entity, camera):
    """
    Sprite Update Logic
    :param entity: Bound entity
    :param camera: Sprite attached
    :return:
    """
    rb = entity.getModule("RigidBody")

    entity.window.canvas.itemconfig(entity.entityFields["rect"], image=entity.entityFields["sprite"], anchor=NW)
    entity.getCanvas().moveto(entity.entityFields["rect"], rb.pos.x - camera.x, rb.pos.y - camera.y)

    if FlipMode:
        entity.updating = False
    else:
        entity.updating = True


def playerInit(entity):
    """
    Sets player attributes
    :param entity: Bound entity
    :return:
    """
    entity.entityFields["playerMovement"] = 0.0015
    entity.entityFields["canJump"] = False
    entity.entityFields["JumpForce"] = 0.485
    entity.entityFields["JumpCooldown"] = 0
    entity.entityFields["HoldingVine"] = None
    entity.entityFields["HoldCooldown"] = 0

    entity.entityFields["AnimFrame"] = 0
    entity.entityFields["lastVel"] = 0
    entity.entityFields["animSpeed"] = 0

    entity.getModule("RigidBody").mass = 0.004


def playerMovement(entity, scene):
    """
    Manages player movement and some update logic
    :param entity: Player
    :param scene: Scene player belongs to
    :return:
    """
    rb = entity.getModule("RigidBody")

    animSheet = "playerstand"
    entity.entityFields["AnimFrame"] += 1

    if not CheatMode:
        col = entity.getModule("Body2D")
        entity.entityFields["canJump"] = False
        heldVine = entity.entityFields["HoldingVine"]
        global currentKeysPressed

        # Cooldowns

        if entity.entityFields["HoldCooldown"] > 0:
            entity.entityFields["HoldCooldown"] -= 1
        if entity.entityFields["JumpCooldown"] > 0:
            entity.entityFields["JumpCooldown"] -= 1

        if heldVine is None:
            currentDist = -1
            closestVine = None

            for vine in scene.vines:
                vineRb = vine[1].getModule("RigidBody")
                dist = math.dist([vineRb.pos.x, vineRb.pos.y],
                                 [rb.pos.x + col.width() / 2, rb.pos.y + col.height() / 2])
                if dist < currentDist or currentDist == -1:
                    currentDist = dist
                    closestVine = vine[1]

            # Gets the closest vine, and player is able to latch to said vine
            # if close enough

            if closestVine is not None and currentDist < 38:
                coolDown = entity.entityFields["HoldCooldown"] == 0
                grappled = data.metaData["controls"]["grapple"] in currentKeysPressed
                if grappled and coolDown and entity.updating:
                    entity.entityFields["HoldingVine"] = closestVine
                    entity.entityFields["HoldCooldown"] = 120

            if data.metaData["controls"]["right"] in currentKeysPressed:
                rb.vel.x += entity.entityFields["playerMovement"] * entity.deltaTime
            if data.metaData["controls"]["left"] in currentKeysPressed:
                rb.vel.x -= entity.entityFields["playerMovement"] * entity.deltaTime

            colliding = col.colliding and col.collidingDown
            # handles jump conditions
            if colliding or (entity.vel().y == 0 or entity.entityFields["lastVel"] == 0):
                absVel = abs(entity.vel().x)
                if absVel > 0.15:
                    animSheet = "playerrun"
                    animSheet += str(int(time.time() * 7) % 8)
                else:
                    animSheet = "playerstand"
            else:
                if entity.vel().y > 0:
                    animSheet = "playerdown"
                else:
                    animSheet = "playerup"

            if colliding:
                if entity.entityFields["JumpCooldown"] == 0:
                    entity.entityFields["canJump"] = True

                if random.randint(0, 10) < max(abs(rb.vel.x * 2) - 0.75, 0):
                    negVel = Vector2(-rb.vel.x * 0.5, -rb.vel.y * 0.5 - 0.05)

                    particle = Entity([RigidBody(copy.copy(rb.pos), negVel, drag=0.998, mass=0)])

                    particle.onInit += lambda e=particle: groundParticleInit(e)
                    particle.onUpdate += lambda e=particle: groundParticleUpdate(e, scene)

                    scene.entityHost.addEntity(particle)

            if data.metaData["controls"]["jump"] in currentKeysPressed and entity.entityFields["canJump"]:
                rb.vel.y -= entity.entityFields["JumpForce"] * entity.deltaTime
                entity.entityFields["JumpCooldown"] = 10
        else:
            vineRb = heldVine.getModule("RigidBody")

            rb.pos.x += (vineRb.pos.x - col.width() / 2 - rb.pos.x) / 9
            rb.pos.y += (vineRb.pos.y - col.height() / 2 - rb.pos.y) / 9

            rb.vel.x = 0
            rb.vel.y = 0

            grappled = data.metaData["controls"]["grapple"] in currentKeysPressed

            animSheet = "playergrapple"

            if grappled and entity.entityFields["HoldCooldown"] == 0 and entity.updating:
                entity.entityFields["HoldingVine"] = None
                entity.entityFields["HoldCooldown"] = 120
                rb.vel.x = vineRb.vel.x * 1.5
                rb.vel.y = vineRb.vel.y * 1.5
    else:

        # GOD MODE MOVEMENT
        # S not included in controls and there has to be manually checked
        # TODO: Make a down control config?

        if data.metaData["controls"]["right"] in currentKeysPressed:
            rb.pos.x += entity.entityFields["playerMovement"] * 200 * entity.deltaTime
        if data.metaData["controls"]["left"] in currentKeysPressed:
            rb.pos.x -= entity.entityFields["playerMovement"] * 200 * entity.deltaTime
        if "s" in currentKeysPressed:
            rb.pos.y += entity.entityFields["playerMovement"] * 200 * entity.deltaTime
        if data.metaData["controls"]["jump"] in currentKeysPressed:
            rb.pos.y -= entity.entityFields["playerMovement"] * 200 * entity.deltaTime

    # if velocity is less than 0, append f to anim sheet
    # anim dictionary copies all entries and appends f for flipped entries

    if rb.vel.x < 0:
        animSheet += "f"

    entity.entityFields["sprite"] = playerAnimations[animSheet]
    entity.entityFields["lastVel"] = entity.vel().y


def tipIndicatorsUpdate(entity, camera, player):
    """
    The event that hanldes the circles at the tip of vines to indicate proximity
    :param entity: Tip circle
    :param camera: Offset
    :param player: Proximity entity
    :return:
    """

    rb = entity.getModule("RigidBody")
    rbPlayer = player.getModule("RigidBody")

    dist = math.sqrt((rbPlayer.pos.x - rb.pos.x) ** 2 + (rbPlayer.pos.y - rb.pos.y) ** 2)
    radius = max(0, (100 - dist) / 25)
    edit_circle(rb.pos.x - camera.x, rb.pos.y - camera.y, radius, entity.entityFields["circle"], entity.window.canvas)

    if FlipMode:
        entity.updating = False
    else:
        entity.updating = True


def tipIndicatorsInit(entity):
    """
    The event that handles the initialisation circles at the tip of vines to indicate proximity
    :param entity: Tip circle
    :return:
    """
    rb = entity.getModule("RigidBody")
    entity.entityFields["circle"] = create_circle(rb.pos.x, rb.pos.y, 4, entity.window.canvas, "black")


def groundParticleUpdate(entity, scene):
    """
    Particle effects for moving fast on the ground
    :param entity: Particle
    :param scene: Scene that holds player
    :return:
    """
    rb = entity.getModule("RigidBody")

    if entity.entityFields["timeLeft"] > 0:
        entity.entityFields["timeLeft"] -= 1
    else:
        # Dispose particle or get lag :(
        entity.getCanvas().delete(entity.entityFields["rect"])
        scene.entityHost.entities.remove(entity)

    camera = scene.getCameraPosition()

    scale = entity.entityFields["timeLeft"] / entity.entityFields["lifeTime"]

    # Place particles at the players feet
    # TODO: make it work with getModule("Body2D").height/width()
    x = rb.pos.x - camera.x + 31
    y = rb.pos.y - camera.y + 63

    entity.getCanvas().coords(entity.entityFields["rect"], x, y, x + 5 * scale, y + 5 * scale)


def groundParticleInit(entity):
    """
    Ground particle effect initialization
    :param entity: Particle
    :return:
    """
    entity.entityFields["rect"] = entity.window.canvas.create_rectangle(0, 0, 0, 0, outline="black", fill="black")
    entity.entityFields["lifeTime"] = 90
    entity.entityFields["timeLeft"] = entity.entityFields["lifeTime"]


def botInit(entity, image):
    """
    Bot attributes and spawn point
    :param entity: Bot
    :param image: Bot sprite
    :return:
    """

    # TODO: Make bot sprite work with spriteInit

    entity.entityFields["currentVine"] = entity.window.canvas.create_rectangle(0, 0, 8, 8, outline="white",
                                                                               fill="white")

    # Bot attribs and spawn point
    # Also initialises line used to move things

    entity.entityFields["attachVine"] = None
    entity.entityFields["vineMaxDist"] = None
    entity.rb.pos.x = 640
    entity.rb.pos.y = 800
    entity.entityFields["attatchCooldown"] = 0
    entity.entityFields["botSprite"] = entity.window.canvas.create_image(0, 0, anchor=NW, image=image)
    entity.entityFields["line"] = entity.window.canvas.create_line(0, 0, 0, 0, fill="white", width=1)


def botUpdate(entity, scene):
    """
    Bot update logic
    :param entity: Bot
    :param scene: Bot scene
    :return:
    """

    # Follows cursor if flip, and goes back to spawn if not flipped

    if FlipMode:
        currentDist = -1
        closestVine = None

        # set vine end to mouse
        if entity.entityFields["attachVine"] is not None:

            vineTopPos = entity.entityFields["attachVine"][0].rb.pos
            vineBottomPos = entity.entityFields["attachVine"][1].rb.pos

            maxDist = entity.entityFields["attachVine"][2]
            currentDist = math.dist([vineTopPos.x, vineTopPos.y], [mouseX, mouseY])

            if currentDist > maxDist:
                vineBottomPos.x = ((mouseX - vineTopPos.x) / currentDist) * maxDist + vineTopPos.x
                vineBottomPos.y = ((mouseY - vineTopPos.y) / currentDist) * maxDist + vineTopPos.y
            else:
                vineBottomPos.x = mouseX
                vineBottomPos.y = mouseY

            entity.getCanvas().coords(entity.entityFields["line"], mouseX, mouseY, entity.pos().x + 20,
                                      entity.pos().y + 20)
        else:
            entity.getCanvas().coords(entity.entityFields["line"], 0, 0, 0, 0)

        entity.vel().x += (mouseX - entity.pos().x) / 5000 - entity.vel().x / 100
        entity.vel().y += (mouseY - entity.pos().y) / 5000 - entity.vel().y / 100

        # cooldown
        if entity.entityFields["attatchCooldown"] > 0:
            entity.entityFields["attatchCooldown"] -= 1

        # find closest vine
        for vine in scene.vines:
            vineRb = vine[1].getModule("RigidBody")
            dist = math.dist([vineRb.pos.x, vineRb.pos.y], [mouseX, mouseY])
            if dist < currentDist or currentDist == -1:
                currentDist = dist
                closestVine = vine

        # attatch and indicator logic
        if closestVine is not None:
            closestVinePos = closestVine[1].pos()
            x = closestVinePos.x
            y = closestVinePos.y

            grappled = data.metaData["controls"]["grapple"] in currentKeysPressed

            if grappled and entity.entityFields["attatchCooldown"] == 0:
                if entity.entityFields["attachVine"] is None:
                    entity.entityFields["attachVine"] = closestVine
                else:
                    entity.entityFields["attachVine"] = None

                entity.entityFields["attatchCooldown"] = 120

            entity.getCanvas().coords(entity.entityFields["currentVine"], x - 4, y - 4, x + 4, y + 4)
    else:
        entity.vel().x += (640 - entity.pos().x) / 5000 - entity.vel().x / 100
        entity.vel().y += (800 - entity.pos().y) / 5000 - entity.vel().y / 100

        entity.entityFields["attachVine"] = None

    entity.getCanvas().moveto(entity.entityFields["botSprite"], entity.pos().x, entity.pos().y)


def createVine(posX, posY, sepX, sepY, noOfChains, scene):
    """
    Create vine in scene
    :param posX: X position of root
    :param posY: Y position of root
    :param sepX: X separation between vine points
    :param sepY: Y separation between vine points
    :param noOfChains: Chain number
    :param scene: Scene that holds vine
    :return:
    """
    boxes = []

    for i in range(noOfChains):
        box = Entity([RigidBody(
            Vector2(posX + i * sepX, posY + i * sepY),
            Vector2(0, 0), False, 0.002, 0.001), VerletBody(
            Vector2(posX + i * sepX, posY + i * sepY),
            True if i == 0 else False)])

        if i > 0:
            scene.entityHost.systems["VerletBody"].bindPoints(boxes[i - 1], box, math.sqrt(sepX * sepX + sepY * sepY))
            if i == noOfChains - 1:
                box.onInit += lambda e=box: tipIndicatorsInit(e)
                box.onUpdate += lambda e=box: tipIndicatorsUpdate(e, scene.getCameraPosition(), scene.player)

        scene.entityHost.addEntity(box)
        boxes.append(box)

    scene.vines.append(
        (boxes[0], boxes[noOfChains - 1], math.sqrt((sepX * noOfChains) ** 2 + (sepY * noOfChains) ** 2)))


def createTerrain(posX, posY, width, height, scene):
    """
    Creates rect that player collides with
    :param posX: Left rect coords
    :param posY: Top rect coords
    :param width: Rect width
    :param height: Rect height
    :param scene: Scene that holds terrain
    :return:
    """
    terrain = Entity([RigidBody(Vector2(posX, posY), Vector2(0, 0), False), Body2D(Vector2(width, height))])
    terrain.onInit += lambda e=terrain: sqaureEntityInitialise(e)
    terrain.onUpdate += lambda e=terrain: sqaureEntityUpdate(e, scene.getCameraPosition())
    scene.entityHost.addEntity(terrain)


def serializeRectanglesIntoTerrain(text, scene):
    """
    Reads rectangle from file and uses createTerrain() to append them to scene
    :param text: text file
    :param scene: scene that terrain will be in
    :return:
    """
    txtContent = open(text).read()
    rects = txtContent.split("|")
    for rect in rects:
        coords = rect.split(" ")
        createTerrain(int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3]), scene)
