import math
import time
import random
import copy

from GameData import *
import GameData

from Assets import *


class GameScene(Scene):
    """
    This specifies a scene that has a pause screen, and a bossKey overlay
    This game obejct should only be applied to scenes where there is gameplay
    """

    def __init__(self, win, transtionSpeed=200, delay=0):
        Scene.__init__(self, win, transtionSpeed, delay)

        self.buttonSelection = 0
        self.buttonChangeCooldown = 250

        self.paused = False
        self.pauseImages = []
        for i in range(len(pausePanels)):
            self.pauseImages.append(win.canvas.create_image(-win.width, 0, anchor=NW, image=pausePanels[i]))

        self.pauseCooldown = 300
        # menu options
        self.menu = Window.canvas.create_image(-win.width, 420, anchor=NW, image=menuPauseButton)
        self.option = Window.canvas.create_image(-win.width, 570, anchor=NW, image=optionsPauseButton)
        self.exit = Window.canvas.create_image(-win.width, 520, anchor=NW, image=exitPauseButton)
        self.arrow = Window.canvas.create_image(-win.width, 430, anchor=NW, image=arrow)

        self.bossImage = Window.canvas.create_image(-3000, -3000, anchor=NW, image=BossKey)

    def miscUpdate(self):

        if self.buttonChangeCooldown > 0:
            self.buttonChangeCooldown -= 1
        # Pause menu scrolling
        if 's' in currentKeysPressed and self.buttonChangeCooldown == 0:
            self.buttonChangeCooldown = 250
            self.buttonSelection = (self.buttonSelection + 1) % 3

        if 'w' in currentKeysPressed and self.buttonChangeCooldown == 0:
            self.buttonChangeCooldown = 250
            self.buttonSelection = (self.buttonSelection - 1) % 3

        if self.pauseCooldown > 0:
            self.pauseCooldown -= 1

        if '\t' in currentKeysPressed and self.pauseCooldown == 0:
            self.pauseCooldown = 300
            self.paused = not self.paused

        # Pause selection
        if self.paused:
            if '\r' in currentKeysPressed:
                self.sceneTransition.delayLeft = 0
                self.paused = False
                if self.buttonSelection == 0:
                    self.sceneTransition.startTransition(MainMenu)
                if self.buttonSelection == 1:
                    self.sceneTransition.startTransition(Options, type(self))
                if self.buttonSelection == 2:
                    data.write("metadata.txt")
                    Window.close()

            # TODO: Switch to interpolation method
            startCoords = Window.canvas.coords(self.menu)
            Window.canvas.move(self.menu, (120 - startCoords[0]) / 60, (420 - startCoords[1]) / 50)

            optionCoords = Window.canvas.coords(self.option)
            Window.canvas.move(self.option, (120 - optionCoords[0]) / 80, (470 - optionCoords[1]) / 50)

            exitCoords = Window.canvas.coords(self.exit)
            Window.canvas.move(self.exit, (120 - exitCoords[0]) / 100, (520 - exitCoords[1]) / 50)

            arrowCoords = Window.canvas.coords(self.arrow)
            Window.canvas.move(self.arrow, (60 - arrowCoords[0]) / 100,
                               (430 + (self.buttonSelection * 50) - arrowCoords[1]) / 50)

            self.entityHost.updating = False
            i = 0
            for pauseImage in self.pauseImages:
                imgCoords = Window.canvas.coords(pauseImage)
                Window.canvas.move(pauseImage, (0 - imgCoords[0]) / 70, 0)
                i += 1
        else:
            startCoords = Window.canvas.coords(self.menu)
            Window.canvas.move(self.menu, (-Window.width - startCoords[0]) / 50, (450 - startCoords[1]) / 50)

            optionCoords = Window.canvas.coords(self.option)
            Window.canvas.move(self.option, (-Window.width - optionCoords[0]) / 50, (500 - optionCoords[1]) / 50)

            exitCoords = Window.canvas.coords(self.exit)
            Window.canvas.move(self.exit, (-Window.width - exitCoords[0]) / 50, (550 - exitCoords[1]) / 50)

            arrowCoords = Window.canvas.coords(self.arrow)
            Window.canvas.move(self.arrow, (-Window.width - arrowCoords[0]) / 50,
                               (460 + (self.buttonSelection * 50) - arrowCoords[1]) / 50)

            # Pause logic.
            # Smoothly interpolates in pause menu images and buttons
            # Stops entities from updating
            if not GameData.BossMode:
                self.entityHost.updating = True
            else:
                self.entityHost.updating = False
            for pauseImage in self.pauseImages:
                imgCoords = Window.canvas.coords(pauseImage)
                Window.canvas.move(pauseImage, (-Window.width - imgCoords[0]) / 140, 0)

        # Boss key switch ins
        if data.metaData["bossKey"] in currentKeysPressed and self.pauseCooldown == 0:
            self.pauseCooldown = 300
            GameData.BossMode = not GameData.BossMode

        if GameData.BossMode:
            Window.canvas.coords(self.bossImage, 0, 0)
        else:
            Window.canvas.coords(self.bossImage, -3000, -3000)


class Level(GameScene):
    """
    These are only for the core levels.
    Level has added camera functionality such as screen shake
    It also has a vine host, as well as an end score screen
    """

    def __init__(self, win, spawn, speed=100, delay=0, foliage=None):

        if foliage is None:
            foliage = []

        self.vines = []
        self.foliage = foliage
        self.player = None
        self.spawnPoint = spawn
        self.scoreCheatCooldown = 0

        self.levelCompleted = False

        self.screenShake = 0
        self.shakeIntensity = 0.1
        self.flipCooldown = 120

        self.score = 0
        self.scoreAdded = False
        self.startTime = time.time()
        self.endTime = time.time()

        self.timesSwitched = 0
        self.foliageIndex = 0

        if len(self.foliage) > 0:
            self.foliageIndex = Window.canvas.create_image(0, 0, anchor=NW, image=foliage[0])

        GameScene.__init__(self, win, speed, delay)

        GameData.CheatMode = False
        GameData.FlipMode = False

        self.timesSwitchedText = Window.canvas.create_text(0, 0, text="", fill="white", font='Helvetica 15 bold')
        self.timeTakenText = Window.canvas.create_text(0, 0, text="", fill="white", font='Helvetica 15 bold')
        self.scoreText = Window.canvas.create_text(0, 0, text="", fill="white", font='Helvetica 30 bold')
        self.scoreCheatText = Window.canvas.create_text(-200, 20, text="Score increased by 1000", fill="gold",
                                                        font='Helvetica 15 bold')

    def getCameraPosition(self):
        """
        Simply getting a copy of the camera with screen shake
        :return:
        """
        shake = Vector2(
            random.uniform(-self.screenShake, self.screenShake) * self.shakeIntensity,
            random.uniform(-self.screenShake, self.screenShake) * self.shakeIntensity)

        return copy.copy(self.cameraPosition) + shake

    def deathLevelRestart(self):
        """
        Death sequence
        Functions as a couritine that starts a transition to the same scene
        :return:
        """
        if self.levelCompleted:
            return

        self.screenShake = 50
        self.sceneTransition.startTransition(type(self))
        self.sceneTransition.delayLeft = 0

    def progressToNextLevel(self, level):
        """
        Progress sequence
        Starts a "couritine" that displays the end sequence where the score is displayed.
        It then transitions to the level parameter
        :param level: Next level
        :return:
        """
        self.levelCompleted = True
        if levels.count(level) > 0:
            # Updates level unlocked to where current level is in the level array (see bottom of file)
            data.metaData["levelsUnlocked"] = levels.index(level)
        self.sceneTransition.startTransition(level)
        if self.endTime == self.startTime:
            self.endTime = time.time()

    def onStart(self):
        """
        Should be homogeneous across all Level initialisation.
        Will instantiate must haves such as the player, the bot and the terrain
        :return:
        """
        self.player = Entity(
            [RigidBody(copy.copy(self.spawnPoint), Vector2(0, 0), drag=0.998), Body2D(Vector2(32, 63))])

        bot = Entity([RigidBody(Vector2(0, 0), Vector2(0, 0), mass=0)])
        bot.onInit += lambda e=bot: botInit(e, Bot)
        bot.onUpdate += lambda e=bot: botUpdate(e, self)

        self.entityHost.addEntity(bot)

        self.initializeLevel()

        self.player.onInit += lambda e=self.player: spriteEntityInitialise(e, playerAnimations["playerstand"])
        self.player.onUpdate += lambda e=self.player: spriteEntityUpdate(e, self.getCameraPosition())
        self.player.onInit += lambda e=self.player: playerInit(e)
        self.player.onUpdate += lambda e=self.player: playerMovement(e, self)

        self.entityHost.addEntity(self.player)

    def flip(self):
        """
        Will do a number of things:
        Flips GameData.FlipMode
        Releases ZanTar of any vine when switching back
        Switched appropriate sprites to their inverted variants
        :return:
        """
        GameData.FlipMode = not GameData.FlipMode
        self.flipCooldown = 80
        self.screenShake = 50

        if not GameData.FlipMode:
            self.player.entityFields["HoldingVine"] = None
        else:
            self.timesSwitched += 1

        if len(self.foliage) > 1:
            Window.canvas.itemconfig(self.foliageIndex, image=self.foliage[1 if GameData.FlipMode else 0])

    def onUpdate(self):

        # Restarts level if player is holding vine and you touch terrain
        if self.player.entityFields["HoldingVine"] is not None and self.player.getModule("Body2D").colliding:
            self.deathLevelRestart()

        # Flips if flip key is pressed and cooldown is 0
        if data.metaData["controls"]["flip"] in currentKeysPressed and self.flipCooldown == 0:
            self.flip()

        # Flips and activates cheat code when cheat Key pressed
        if data.metaData["cheatCode"] in currentKeysPressed and self.flipCooldown == 0:
            self.flip()
            GameData.CheatMode = not GameData.CheatMode

        if "n" in currentKeysPressed:
            self.progressToNextLevel(levels[levels.index(type(self)) + 1])

        if "m" in currentKeysPressed and self.scoreCheatCooldown == 0:
            data.metaData["currentScore"] += 1000
            self.scoreCheatCooldown = 1000

        interpolateCanvasItem(self.scoreCheatText, Window.canvas, -200 + self.scoreCheatCooldown * 0.6, 20, 300)

        if self.scoreCheatCooldown > 0:
            self.scoreCheatCooldown -= 1

        Window.canvas.configure(bg="black" if GameData.FlipMode else "white")
        self.entityHost.systems["VerletBody"].debugColor = "white" if GameData.FlipMode else "black"

        if self.flipCooldown > 0:
            self.flipCooldown -= 1

        # Screen shake decrements to zero
        if self.screenShake > 0:
            self.screenShake -= 1

        self.onLevelUpdate()

        if self.sceneTransition.delaying:

            if self.sceneTransition.delayLeft < self.sceneTransition.delay * 0.8:
                # If block will calculate number of times switched and display
                if Window.canvas.coords(self.timesSwitchedText)[0] == 0:
                    self.screenShake = 30

                Window.canvas.coords(self.timesSwitchedText, 640 + self.getCameraPosition().x,
                                     300 + self.getCameraPosition().y)
                Window.canvas.itemconfig(self.timesSwitchedText,
                                         text="Number of times switched: " + str(self.timesSwitched))
                if self.sceneTransition.delayLeft < self.sceneTransition.delay * 0.6:
                    # If block will calculate time taken and display
                    if Window.canvas.coords(self.timeTakenText)[0] == 0:
                        self.screenShake = 40

                    Window.canvas.coords(self.timeTakenText, 640 + self.getCameraPosition().x,
                                         350 + self.getCameraPosition().y)
                    totalTime = math.ceil((self.endTime - self.startTime) * 100) / 100
                    Window.canvas.itemconfig(self.timeTakenText,
                                             text="Time taken: " + str(totalTime))
                    if self.sceneTransition.delayLeft < self.sceneTransition.delay * 0.4:
                        # This calculates score
                        if Window.canvas.coords(self.scoreText)[0] == 0:
                            self.screenShake = 50

                        Window.canvas.coords(self.scoreText, 640 + self.getCameraPosition().x,
                                             450 + self.getCameraPosition().y)
                        # SCORE FORMULA
                        score = 1000 + max((60 - totalTime), 0) * (1000 / 60) - self.timesSwitched * 100
                        Window.canvas.itemconfig(self.scoreText,
                                                 text="Score: " + str(math.ceil(score)))

                        if not self.scoreAdded:
                            data.metaData["currentScore"] += math.ceil(score)
                            self.scoreAdded = True


# The following classes will have no docstrings, as they represent the most front level of the game's architecture
class MainMenu(Scene):
    def __init__(self, win):
        Window.canvas.create_image(0, 0, anchor=NW, image=HomeScreen)
        self.title = Window.canvas.create_image(0, -1000, anchor=NW, image=titleScreen)

        # All menu buttons initialised off-screen
        self.continueButton = Window.canvas.create_image(-300, 350, anchor=NW, image=continueButton)
        self.start = Window.canvas.create_image(-300, 400, anchor=NW, image=startButton)
        self.option = Window.canvas.create_image(-300, 450, anchor=NW, image=optionsButton)
        self.scores = Window.canvas.create_image(-300, 500, anchor=NW, image=scoresButton)
        self.exit = Window.canvas.create_image(-300, 550, anchor=NW, image=exitButton)

        self.arrow = Window.canvas.create_image(-300, 410, anchor=NW, image=arrow)

        Scene.__init__(self, win)

        self.buttonSelection = 0
        self.buttonChangeCooldown = 250

    def onUpdate(self):

        if self.buttonChangeCooldown > 0:
            self.buttonChangeCooldown -= 1
        hasGame = data.metaData["levelsUnlocked"] > -1

        # Move selection with S and W
        if 's' in currentKeysPressed and self.buttonChangeCooldown == 0:
            self.buttonChangeCooldown = 250
            self.buttonSelection = (self.buttonSelection + 1) % (5 if hasGame else 4)
        if 'w' in currentKeysPressed and self.buttonChangeCooldown == 0:
            self.buttonChangeCooldown = 250
            self.buttonSelection = (self.buttonSelection - 1) % (5 if hasGame else 4)
        gameShift = 1 if hasGame else 0

        # Select with enter (Tkinter buttons are ugly)
        if '\r' in currentKeysPressed:
            if self.buttonSelection == -1 + gameShift:
                self.sceneTransition.startTransition(levels[data.metaData["levelsUnlocked"]])
            if self.buttonSelection == 0 + gameShift:
                self.sceneTransition.startTransition(Exposition)
                data.metaData["currentScore"] = 0
            if self.buttonSelection == 1 + gameShift:
                self.sceneTransition.startTransition(Options, type(self))
            if self.buttonSelection == 2 + gameShift:
                self.sceneTransition.startTransition(Leaderboard)
            if self.buttonSelection == 3 + gameShift:
                data.write("metadata.txt")
                Window.close()

        titleCoords = Window.canvas.coords(self.title)
        Window.canvas.move(self.title, (20 - titleCoords[0]) / 100, (50 - titleCoords[1]) / 100)

        if data.metaData["levelsUnlocked"] > -1:
            interpolateCanvasItem(self.continueButton, Window.canvas, 150, 350, 100)

        # Interpolate buttons to the right place
        # More about interpolate will be in MyLib

        interpolateCanvasItem(self.start, Window.canvas, 150, 400, 120)

        interpolateCanvasItem(self.option, Window.canvas, 150, 450, 140)

        interpolateCanvasItem(self.scores, Window.canvas, 150, 500, 160)

        interpolateCanvasItem(self.exit, Window.canvas, 150, 550, 180)

        interpolateCanvasItem(self.arrow, Window.canvas, 90, 410 + (self.buttonSelection - gameShift) * 50, 100)


class IntroLevel(GameScene):
    def __init__(self, win):
        Window.canvas.configure(bg="white")
        data.metaData["levelsUnlocked"] = 0

        self.player = None
        self.spawnPoint = Vector2(140, 30)
        self.vines = []

        self.foliage = [IntroFoliage, IntroFoliageInvert]

        if len(self.foliage) > 0:
            self.foliageIndex = Window.canvas.create_image(0, 0, anchor=NW, image=self.foliage[0])

        self.screenShake = 0
        self.shakeIntensity = 0.1
        self.nextPrompt = ""
        GameScene.__init__(self, win)
        Window.win.bind('<Key>', self.textPropagate)
        self.yTarget = 300
        self.promptIndex = 0
        self.prompts = Window.canvas.create_text(1000, -100,
                                                 text="Enter a key to jump",
                                                 fill="black",
                                                 font='Helvetica 15 bold')

    def textPropagate(self, event):
        # Input sequence
        if self.yTarget == 300:
            text = event.char if event.num == '??' else event.num
            self.promptIndex += 1
            if self.promptIndex == 1:
                self.nextPrompt = "Enter a left key"
                self.player.getModule("RigidBody").vel.y = -1
                data.metaData["controls"]["jump"] = text
            if self.promptIndex == 2:
                self.nextPrompt = "Enter a right key"
                self.player.getModule("RigidBody").vel.y = -0.7
                self.player.getModule("RigidBody").vel.x = -0.1
                data.metaData["controls"]["left"] = text
            if self.promptIndex == 3:
                self.nextPrompt = "Enter a grapple key"
                self.player.getModule("RigidBody").vel.y = -0.7
                self.player.getModule("RigidBody").vel.x = 0.1
                data.metaData["controls"]["right"] = text
            if self.promptIndex == 4:
                self.nextPrompt = "And finally a button to flip time"
                data.metaData["controls"]["grapple"] = text

                GameData.FlipMode = not GameData.FlipMode
                Window.canvas.itemconfig(self.foliageIndex, image=self.foliage[1])

                Window.canvas.configure(bg="black")
                Window.canvas.itemconfig(self.prompts, fill="white")
                self.screenShake = 50
            if self.promptIndex == 5:
                self.nextPrompt = " "
                data.metaData["controls"]["flip"] = text

                GameData.FlipMode = not GameData.FlipMode
                Window.canvas.itemconfig(self.foliageIndex, image=self.foliage[0])

                Window.canvas.configure(bg="white")
                Window.canvas.itemconfig(self.prompts, fill="black")
                self.screenShake = 0

                self.sceneTransition.startTransition(Tutorial)

                Window.win.bind('<Key>', on_event)
                Window.win.bind("<KeyRelease>", on_release)
                Window.win.bind("<Motion>", motion)

        self.yTarget = 1300

    def getCameraPosition(self):
        shake = Vector2(
            random.uniform(-self.screenShake, self.screenShake) * self.shakeIntensity,
            random.uniform(-self.screenShake, self.screenShake) * self.shakeIntensity)

        return copy.copy(self.cameraPosition) + shake

    def onStart(self):
        # Re-instantiate player, as it is not a typical level with the bot and vines.
        # Could break the tree a bit more to account for this
        self.player = Entity(
            [RigidBody(copy.copy(self.spawnPoint), Vector2(0, 0), drag=0.998), Body2D(Vector2(32, 64))])
        self.player.onInit += lambda e=self.player: spriteEntityInitialise(e, playerAnimations["playerstand"])
        self.player.onUpdate += lambda e=self.player: spriteEntityUpdate(e, self.getCameraPosition())
        self.player.onInit += lambda e=self.player: playerInit(e)
        self.player.onUpdate += lambda e=self.player: playerMovement(e, self)

        self.entityHost.addEntity(self.player)
        self.cameraPosition.y = 2000
        createTerrain(0, 600, 1280, 3000, self)

    def onUpdate(self):
        # Prompt interpolation
        self.cameraPosition.y *= 0.994

        promptCoords = Window.canvas.coords(self.prompts)
        Window.canvas.move(self.prompts, 0, (self.yTarget - promptCoords[1]) / 200)
        if promptCoords[1] > 700:
            Window.canvas.coords(self.prompts, promptCoords[0], -100)
            Window.canvas.itemconfig(self.prompts, text=self.nextPrompt)
            self.yTarget = 300


class Options(Scene):
    # Contains all the options to change keys except b, n, m
    # TODO: make the un-changeable keys
    def __init__(self, win, lastScene):
        Window.canvas.configure(bg="black")

        self.buttonSelection = 0
        self.buttonChangeCooldown = 250
        self.overlay = Window.canvas.create_image(0, 0, anchor=NW, image=OptionsMenu)
        self.arrow = Window.canvas.create_image(-200, 146, image=arrow)
        self.cheatdesc = Window.canvas.create_image(640, 650, image=CheatDesc)

        self.optionButtons = [IntroFoliage, IntroFoliageInvert]
        self.lastScene = lastScene

        self.optionButtons.append(Window.canvas.create_text(424, 146, text=data.metaData["bossKey"], fill="white",
                                                            font='Helvetica 15 bold'))
        self.optionButtons.append(
            Window.canvas.create_text(424, 146 + 62,
                                      text=data.metaData["cheatCode"],
                                      fill="white",
                                      font='Helvetica 15 bold'))
        i = 0
        for key, value in data.metaData["controls"].items():
            controls = value
            self.optionButtons.append(
                Window.canvas.create_text(424, 146 + (i + 2) * 62,
                                          text=controls,
                                          fill="white",
                                          font='Helvetica 15 bold'))
            i += 1

        # Dictionary entries in metadata to change
        # This is to automize the data entry process (kinda) instead of
        # making a huge conditional

        self.fieldValues = [
            "bossKey",
            "cheatCode",
            "controls,left",
            "controls,right",
            "controls,jump",
            "controls,grapple",
            "controls,flip"]

        self.listening = False

        Scene.__init__(self, win)

    def listenForInput(self):
        # Listens for key input and changes appropriate metadata field
        Window.canvas.itemconfig(self.optionButtons[self.buttonSelection], fill="green")
        if len(currentKeysPressed) > 0:
            self.listening = False
            # If not equal to special keys/Enter
            if currentKeysPressed[0] != '\r' and currentKeysPressed[0] != 'm' and currentKeysPressed[0] != 'n':
                Window.canvas.itemconfig(self.optionButtons[self.buttonSelection],
                                         text=currentKeysPressed[0],
                                         fill="white")
                if self.buttonSelection < 2:
                    data.metaData[self.fieldValues[self.buttonSelection]] = currentKeysPressed[0]
                else:
                    keyValue = self.fieldValues[self.buttonSelection].split(",")
                    data.metaData[keyValue[0]][keyValue[1]] = currentKeysPressed[0]
            else:
                Window.canvas.itemconfig(self.optionButtons[self.buttonSelection], fill="white")

    def onUpdate(self):
        if self.buttonChangeCooldown > 0:
            self.buttonChangeCooldown -= 1

        if self.listening and self.buttonChangeCooldown == 0:
            self.listenForInput()
            self.buttonChangeCooldown = 120
        # Cycle through all options with s and w
        # b to go back (could parameterize?)
        else:
            if 's' in currentKeysPressed and self.buttonChangeCooldown == 0:
                self.buttonChangeCooldown = 250
                self.buttonSelection = (self.buttonSelection + 1) % 7

            if 'w' in currentKeysPressed and self.buttonChangeCooldown == 0:
                self.buttonChangeCooldown = 250
                self.buttonSelection = (self.buttonSelection - 1) % 7

            if 'b' in currentKeysPressed and self.buttonChangeCooldown == 0:
                self.buttonChangeCooldown = 250
                self.sceneTransition.startTransition(self.lastScene)

        if '\r' in currentKeysPressed and not self.listening and self.buttonChangeCooldown == 0:
            self.listening = True
            self.buttonChangeCooldown = 120

        # Interpolate items
        interpolateCanvasItem(self.arrow, Window.canvas, 100 + math.sin(time.time() * 3) * 10,
                              146 + self.buttonSelection * 62, 100)


class InitialInput(Scene):
    def __init__(self, win):
        Window.canvas.configure(bg="black")

        self.buttonSelection = 0
        self.buttonChangeCooldown = 250

        self.optionButtons = []

        self.initialsText = Window.canvas.create_text(640, 360, text="", fill="white", font='Helvetica 15 bold')
        self.initialsPrompt = Window.canvas.create_text(640, 160, text="Enter the first letter of your first name",
                                                        fill="white", font='Helvetica 15 bold')

        self.initials = ""

        self.listening = True

        Scene.__init__(self, win)

    def listenForInput(self):
        # See Options.listenForInput() for explanation.
        # Only difference is there are no fields to pick from as it just appends to a string
        if len(currentKeysPressed) > 0 and self.buttonSelection < 2:
            if currentKeysPressed[0].isalpha():
                self.initials += currentKeysPressed[0].upper()
                self.buttonChangeCooldown = 300
                if self.buttonSelection == 0:
                    self.buttonSelection += 1
                    Window.canvas.itemconfig(self.initialsPrompt, text="Now the first letter of your surname")
                else:
                    data.metaData["initials"] = self.initials
                    data.metaData["leaderBoard"][self.initials] = data.metaData["currentScore"]
                    self.sceneTransition.startTransition(Leaderboard)
                    data.metaData["currentScore"] = 0
                    data.metaData["levelsUnlocked"] = -1
                    self.buttonSelection += 1

    def onUpdate(self):
        if self.buttonChangeCooldown > 0:
            self.buttonChangeCooldown -= 1

        if self.buttonChangeCooldown == 0:
            self.listenForInput()

        Window.canvas.itemconfig(self.initialsText, text=str(self.initials))


class Leaderboard(Scene):
    def __init__(self, win):
        Window.canvas.configure(bg="black")

        self.overlay = Window.canvas.create_image(0, 0, anchor=NW, image=LeaderboardScreen)
        self.leaderBoardShow = 1000

        position = 1
        self.leaderBoardTexts = []

        # Sort leaderboard

        sortedLeaderboard = {
            k: v for k, v in sorted(data.metaData["leaderBoard"].items(),
                                    key=lambda item: int(item[1]))}

        # Append leaderboard entries
        # Cute little colours for 1-3rd place

        for key, value in reversed(list(sortedLeaderboard.items())):
            leaderBoardText = f"{position}. {key} :      {value}\n"
            color = "white"
            if position == 1:
                color = "gold"
            elif position == 2:
                color = "silver"
            elif position == 3:
                color = "brown"
            position += 1
            self.leaderBoardTexts.append(Window.canvas.create_text(640, -600 + position * 40,
                                                                   text=leaderBoardText,
                                                                   fill=color,
                                                                   font='Helvetica 15 italic'))
            # Only show Top 10

            if position > 10:
                break

        # Show your score at the bottom

        if data.metaData['initials'] in data.metaData['leaderBoard'].keys():

            place = (len(data.metaData['leaderBoard']) - list(sortedLeaderboard.keys()).index(
                data.metaData['initials']))

            color = "white"
            if place == 1:
                color = "gold"
            elif place == 2:
                color = "silver"
            elif place == 3:
                color = "brown"

            initials = data.metaData['leaderBoard'][data.metaData['initials']]

            Window.canvas.create_text(640, 600,
                                      text=f"Your Score: {initials}  #{place}",
                                      fill=color,
                                      font='Helvetica 15 italic')
        Scene.__init__(self, win)

    def onUpdate(self):
        self.leaderBoardShow -= 1

        # Display leaderboard entries in a stagger (100ms)

        for i, element in enumerate(self.leaderBoardTexts):
            if i > math.floor(self.leaderBoardShow / 100):
                Window.canvas.coords(element, 640, 250 + i * 40)

        if 'b' in currentKeysPressed:
            self.sceneTransition.startTransition(MainMenu)


class Exposition(GameScene):
    def __init__(self, win):
        Window.canvas.configure(bg="black")
        # Text for exposition is in image
        self.exposition = Window.canvas.create_image(0, 600, anchor=NW, image=ExpositionImage)
        self.EnterSkip = Window.canvas.create_image(20, 30, anchor=NW, image=EnterSkip)

        GameScene.__init__(self, win)

    def onUpdate(self):
        Window.canvas.move(self.exposition, 0, -0.04)
        # Enter to skip
        if "\r" in currentKeysPressed:
            self.sceneTransition.startTransition(IntroLevel)


class Conclusion(GameScene):
    # Identical to Exposition but with a different image
    def __init__(self, win):
        Window.canvas.configure(bg="black")
        self.exposition = Window.canvas.create_image(0, 600, anchor=NW, image=ConclusionImage)
        self.EnterSkip = Window.canvas.create_image(20, 30, anchor=NW, image=EnterSkip)

        GameScene.__init__(self, win)

    def onUpdate(self):
        Window.canvas.move(self.exposition, 0, -0.04)

        if "\r" in currentKeysPressed and not self.paused:
            self.sceneTransition.startTransition(InitialInput)


# HERE AND BEYOND ARE LEVELS.
# They follow the same format of reading a terrain file and appending vines
# They also set death and progress conditions
# Will only show where these are for the tutorial
# May also have prompt text

class Tutorial(Level):
    def __init__(self, win):
        Level.__init__(self, win, Vector2(20, 64), 100, 1200, [TutorialFoliage, TutorialFoliageInvert])

        # Prompt text
        self.helpText = Window.canvas.create_text(1000, 200,
                                                  text=f"Press [{data.metaData['controls']['grapple']}] "
                                                       f"when near the end of a vine to grapple on to it",
                                                  fill="black",
                                                  font='Helvetica 15 bold')

    def initializeLevel(self):
        # Reading from terrain
        serializeRectanglesIntoTerrain("TutorialLevel.txt", self)
        # Vine creation
        createVine(620, 32, 30, 25, 9, self)

    def onLevelUpdate(self):
        # 2nd prompt
        secondPrompt = f"Press [{data.metaData['controls']['grapple']}] to release"

        if self.player.entityFields["HoldingVine"] is not None:
            Window.canvas.itemconfig(self.helpText, text=secondPrompt)

        if self.player.entityFields["HoldingVine"] is None and Window.canvas.itemcget(self.helpText,
                                                                                      "text") == secondPrompt:
            Window.canvas.itemconfig(self.helpText, text="")

        # DEATH CONDITIONS

        if self.player.pos().y > 720:
            self.deathLevelRestart()
        if self.player.pos().x > 1280:
            self.progressToNextLevel(Level1)


class Level1(Level):
    def __init__(self, win):
        self.promptIndex = 0

        self.promptCooldown = 0

        Level.__init__(self, win, Vector2(20, 64), 100, 1200, [Level0Foliage, Level0FoliageInvert])

        self.helpText = Window.canvas.create_text(1000, 100,
                                                  text=f"Call on the mysterious object by pressing "
                                                       f"[{data.metaData['controls']['flip']}]",
                                                  fill="black",
                                                  font='Helvetica 10 bold')

    def initializeLevel(self):
        serializeRectanglesIntoTerrain("Level0Terrain.txt", self)
        createVine(620, 32, 4, 40, 9, self)

    def onLevelUpdate(self):
        if self.player.pos().y > 720:
            if self.player.pos().x > 1000:
                self.progressToNextLevel(Level2)
            else:
                self.deathLevelRestart()

        if self.promptCooldown > 0:
            self.promptCooldown -= 1

        if GameData.FlipMode and self.promptIndex == 0 and self.promptCooldown == 0:
            Window.canvas.itemconfig(self.helpText,
                                     text=f"This invokes the time rift. \n Now press "
                                          f"[{data.metaData['controls']['grapple']}] "
                                          f"to move the ends of a vine",
                                     fill="white")
            self.promptIndex = 1
            self.promptCooldown = 120

        grappling = data.metaData['controls']['grapple'] in currentKeysPressed
        # More complex prompt conditions where player might need to grapple
        if self.promptIndex == 1 and grappling and self.promptCooldown == 0:
            Window.canvas.itemconfig(self.helpText,
                                     text=f"Move your mouse to where you want the vine to be, "
                                          f"then press [{data.metaData['controls']['grapple']}] again to release")
            self.promptIndex = 2
            self.promptCooldown = 120
            return

        if self.promptIndex == 2 and grappling and self.promptCooldown == 0:
            Window.canvas.itemconfig(self.helpText,
                                     text=f"Press [{data.metaData['controls']['flip']}] to flip back time")
            self.promptIndex = 3

        if self.promptIndex == 3 and data.metaData['controls']['flip'] in currentKeysPressed:
            Window.canvas.itemconfig(self.helpText,
                                     text="", fill="black")


class Level2(Level):
    def __init__(self, win):
        Level.__init__(self, win, Vector2(140, 30), 100, 1200, [Level1Foliage, Level1FoliageInvert])

    def initializeLevel(self):
        serializeRectanglesIntoTerrain("Level1Terrain.txt", self)

        createVine(600, 304, 4, 38, 6, self)
        createVine(900, 304, -4, 30, 6, self)

    def onLevelUpdate(self):
        if self.player.pos().y > 720:
            self.deathLevelRestart()
        if self.player.pos().x > 1280:
            self.progressToNextLevel(Level3)


class Level3(Level):
    def __init__(self, win):
        Level.__init__(self, win, Vector2(10, 500), 100, 1200, [Level2Foliage, Level2FoliageInvert])

        self.helpText = Window.canvas.create_text(1000, 100,
                                                  text=f"Be cautious of hitting terrain when swinging",
                                                  fill="black",
                                                  font='Helvetica 10 bold')

        self.helpText2 = Window.canvas.create_text(200, 500,
                                                   text=f"Try to think about different times you can call your friend",
                                                   fill="black",
                                                   font='Helvetica 10 bold')

        self.helpText3 = Window.canvas.create_text(500, -320,
                                                   text=f"You will let go of vines when going back to Zantar time",
                                                   fill="white",
                                                   font='Helvetica 10 bold')

    def initializeLevel(self):
        serializeRectanglesIntoTerrain("Level2Terrain.txt", self)

        createVine(464 + 32, 352 + 32, 2, 30, 5, self)
        createVine(464 + 32, 112 + 32, 2, 30, 6, self)
        createVine(670, 16, 2, 18, 7, self)

    def onLevelUpdate(self):

        if self.player.entityFields["HoldingVine"] is not None and GameData.FlipMode:
            Window.canvas.coords(self.helpText3, 500, 320)
        else:
            Window.canvas.coords(self.helpText3, 500, -320)

        if self.player.pos().y > 720:
            self.deathLevelRestart()
        if self.player.pos().x > 1280:
            self.progressToNextLevel(Level4)
            Window.canvas.delete(self.helpText3)


class Level4(Level):
    def __init__(self, win):
        Level.__init__(self, win, Vector2(60, 60), 100, 1200, [Level3Foliage, Level3FoliageInvert])

    def initializeLevel(self):
        serializeRectanglesIntoTerrain("Level3Terrain.txt", self)

        createVine(570, 16, 2, 50, 6, self)

    def onLevelUpdate(self):
        if self.player.pos().y > 720:
            self.deathLevelRestart()
        if self.player.pos().x > 1280:
            self.progressToNextLevel(Level5)


class Level5(Level):
    def __init__(self, win):
        Level.__init__(self, win, Vector2(10, 600), 100, 1200, [Level4Foliage, Level4FoliageInvert])

    def initializeLevel(self):
        serializeRectanglesIntoTerrain("Level4Terrain.txt", self)

        # WILL LAG ON LAB MACHINES. BE WARNED

        createVine(192 + 40, 320 + 40, 2, 36, 6, self)
        createVine(416 + 40, 320 + 40, 2, 50, 7, self)
        createVine(670, -10, 2, 34, 6, self)
        createVine(928 + 110, -10, 2, 70, 7, self)
        createVine(928 + 32, 540, 2, 40, 4, self)

    def onLevelUpdate(self):
        if self.player.pos().y > 720:
            self.deathLevelRestart()
        if self.player.pos().x > 1280:
            self.progressToNextLevel(Conclusion)


data.read("metadata.txt")
# Level array will be the reference to know which index the levels are at
levels = [Tutorial, Level1, Level2, Level3, Level4, Level5, Conclusion]

# Bind all the input events to their respective methods
Window.win.bind('<Key>', on_event)
Window.win.bind("<KeyRelease>", on_release)
Window.win.bind("<Motion>", motion)

# Always start in Main Menu
Window.nextScene(MainMenu)

Window.update()
Window.win.mainloop()

# Write to metadata.txt after window is exited to save progress
data.write("metadata.txt")
