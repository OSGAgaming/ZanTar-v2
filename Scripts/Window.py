from tkinter import Tk, Canvas
from Entities import *
import importlib
from typing import Type, TypeVar
import time


class Scene:
    """
    Defines where entities will be stored that encompasses more than EntityHost
    Also defines a camera and a transition instance
    On Update and MiscUpdate are simply so all inherited classes from scene can get
    Their own update loop without calling their base
    """
    def __init__(self, win, transtionSpeed=200, delay=0):
        self.entityHost = EntityHost(win)
        self.cameraPosition = Vector2(0, 0)
        self.onStart()
        self.sceneTransition = Transition(transtionSpeed, win, delay)

    def onUpdate(self):
        self.sceneTransition.update()

    def onStart(self):
        pass

    def miscUpdate(self):
        pass

    def update(self):
        self.miscUpdate()
        self.onUpdate()
        self.sceneTransition.update()


class Transition:
    """
    Defines transition data, such as the speed anb delay of transition
    """

    # Generic to specify that type must be of Scene
    T = TypeVar("T", bound=Scene)

    def __init__(self, speed, window, delay=0):
        self.window = window
        self.tranistionBox = self.window.canvas.create_rectangle(0, 0,
                                                                 self.window.width,
                                                                 self.window.height + 100,
                                                                 outline="black",
                                                                 fill="black")
        self.speed = speed
        self.transitioning = False
        self.transitionScene = None
        self.lastScene = None
        self.delay = delay
        self.delaying = False
        self.delayLeft = delay

    def startTransition(self, scene: Type[T], lastScene: Type[T] = None) -> T:
        """
        Will start transition to next scene
        Also has optional last scene param incase a scene needs to access it (such as Options
        :param scene: Scene we are going to
        :param lastScene: Scene we were just at
        :return:
        """
        if not self.transitioning:
            self.transitioning = True
            self.transitionScene = scene
            self.lastScene = lastScene
            self.window.canvas.moveto(self.tranistionBox, 0, self.window.height)

    def update(self):

        """
        'Coroutine' that waits for duration of transition + delay time, and the moves to next scene
        :return:
        """

        transitionPos = self.window.canvas.coords(self.tranistionBox)

        if not self.transitioning:
            self.window.canvas.move(self.tranistionBox, 0, (-self.window.height - 100 - transitionPos[1]) / self.speed)
        else:
            if len(transitionPos) > 0:
                self.window.canvas.move(self.tranistionBox, 0, (-50 - transitionPos[1]) / self.speed)
                if transitionPos[1] < 0:
                    self.delaying = True
                    if self.delayLeft > 0:
                        self.delayLeft -= 1
                    else:
                        self.window.nextScene(self.transitionScene, self.lastScene)


class GameWindow:
    """
    This is the class that wraps around the tkinter Window. This is the main host
    of the game, and contains the scene, widgets, the canvas, and window data
    """
    T = TypeVar("T", bound=Scene)

    def __init__(self, width, height, bkg="white"):
        self.updating = True
        self.refreshRate = 1
        self.win = Tk()
        self.win.geometry(str(width) + "x" + str(height))
        self.canvas = Canvas(self.win, bg=bkg, height=height, width=width)
        self.canvas.pack()
        self.widgets = []
        self.scene = None

        self.width = width
        self.height = height

        self.currentTime = time.time()
        self.lastTime = time.time()

        self.deltaTimeAccumulator = 0
        self.deltaTime = 1
        self.deltaAverage = 1
        self.deltaTimeRefresh = 20
        self.deltaTimeRefreshTimer = 0

    def addWidget(self, widget):
        # This simply adds widgets for the purpose of have references to them
        # When we want to dispose all widgets
        self.widgets.append(widget)

    # An extension to next Scene in transition that changes the scene in the window
    def nextScene(self, scene: Type[T], lastScene: Type[T] = None) -> T:
        self.canvas.delete("all")
        for widget in self.widgets:
            widget.destroy()

        if lastScene is not None:
            self.scene = scene(self, lastScene)
        else:
            self.scene = scene(self)

    def onUpdate(self):
        # Delta time that takes average across self.deltaTimeRefresh amount of frames
        # Very useful for physics calculations
        self.currentTime = time.time()
        self.deltaTime = (self.currentTime - self.lastTime) * 1000

        self.deltaTimeRefreshTimer += 1
        self.deltaTimeAccumulator += self.deltaTime
        if self.deltaTimeRefreshTimer % self.deltaTimeRefresh == 0:
            self.deltaAverage = self.deltaTimeAccumulator / self.deltaTimeRefresh
            self.deltaTimeAccumulator = 0

        # Updates entities
        self.scene.entityHost.update()
        self.scene.update()
        # Calls itself after refresh rate to create update logic
        self.win.after(self.refreshRate, self.onUpdate)

        # Grab the time at the end so the value is delayed for the deltatime calculations
        self.lastTime = time.time()

    def update(self):
        """ Main update loop.
        Calls onUpdate, which then uses a similar technique to call itself after self.refreshRate"""
        if self.updating:
            self.win.after(0, self.onUpdate)

    def start(self):
        """Starts window element updating"""
        self.updating = True

    def stop(self):
        """Stops window elements from updating"""
        self.updating = False

    def close(self):
        """Closes window"""
        self.win.quit()
