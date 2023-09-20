import copy
from tkinter import PhotoImage, NW
from Window import *
from PIL import Image, ImageTk
# This is file stores all assets, and window dimensions
# It also stores the player animation dictionary, which is referenced in comments in GameData.py
# TODO: autoload to dict?

WINDOW_DIMENSIONS = (1280, 720)
Window = GameWindow(WINDOW_DIMENSIONS[0], WINDOW_DIMENSIONS[1])

# =======================MENU BUTTONS===============================
startButton = PhotoImage(file='startbutton.png')
optionsButton = PhotoImage(file='optionsbutton.png')
exitButton = PhotoImage(file='exitbutton.png')

optionsPauseButton = PhotoImage(file='optionspause.png')
exitPauseButton = PhotoImage(file='exitpause.png')
menuPauseButton = PhotoImage(file='menupause.png')
continueButton = PhotoImage(file='continuebutton.png')
scoresButton = PhotoImage(file='scoresbutton.png')

CheatDesc = PhotoImage(file='CheatDesc.png')
EnterSkip = PhotoImage(file='EnterSkip.png')

arrow = PhotoImage(file='arrow.png')

pausePanels = []
for i in range(5):
    pausePanels.append(PhotoImage(file='pause' + str(i + 1) + '.png'))
# =======================FOLIAGE===============================
IntroFoliage = PhotoImage(file='IntroFoliage.png')
IntroFoliageInvert = PhotoImage(file='IntroFoliageInvert.png')

TutorialFoliage = PhotoImage(file='TutorialFoliage.png')
TutorialFoliageInvert = PhotoImage(file='TutorialFoliageInvert.png')

Level0Foliage = PhotoImage(file='Level0Foliage.png')
Level0FoliageInvert = PhotoImage(file='Level0FoliageInvert.png')

Level1Foliage = PhotoImage(file='Level1Foliage.png')
Level1FoliageInvert = PhotoImage(file='Level1FoliageInvert.png')

Level2Foliage = PhotoImage(file='Level2Foliage.png')
Level2FoliageInvert = PhotoImage(file='Level2FoliageInvert.png')

Level3Foliage = PhotoImage(file='Level3Foliage.png')
Level3FoliageInvert = PhotoImage(file='Level3FoliageInvert.png')

Level4Foliage = PhotoImage(file='Level4Foliage.png')
Level4FoliageInvert = PhotoImage(file='Level4FoliageInvert.png')
# =======================MENU BGS===============================

OptionsMenu = PhotoImage(file='OptionScreen.png')
ExpositionImage = PhotoImage(file='Exposition.png').zoom(2, 2)
ConclusionImage = PhotoImage(file='ConclusionText.png')

ConclusionImage = PhotoImage(file='ConclusionText.png')
BossKey = PhotoImage(file='bossKey.png')

LeaderboardScreen = PhotoImage(file='LeadboardScreen.png')
titleScreen = PhotoImage(file='titlescreen.png')
HomeScreen = PhotoImage(file='HomeScreen.png')
# =======================PLAYER ANIMATIONS===============================

# Player anim
# After the dictionary has been manually filled
# It then duplicates all images but flipped, and appends "f" to the end of the key for easy retrieval
playerAnimationsTemp = {"playerstand": ImageTk.PhotoImage(Image.open('playerstand.png')),

                        "playerup": ImageTk.PhotoImage(Image.open('playerup.png')),
                        "playerdown": ImageTk.PhotoImage(Image.open('playerdown.png')),

                        "playerrun0": ImageTk.PhotoImage(Image.open('playerrun0.png')),
                        "playerrun1": ImageTk.PhotoImage(Image.open('playerrun1.png')),
                        "playerrun2": ImageTk.PhotoImage(Image.open('playerrun2.png')),
                        "playerrun3": ImageTk.PhotoImage(Image.open('playerrun3.png')),
                        "playerrun4": ImageTk.PhotoImage(Image.open('playerrun4.png')),
                        "playerrun5": ImageTk.PhotoImage(Image.open('playerrun5.png')),
                        "playerrun6": ImageTk.PhotoImage(Image.open('playerrun6.png')),
                        "playerrun7": ImageTk.PhotoImage(Image.open('playerrun7.png')),

                        "playergrapple": ImageTk.PhotoImage(Image.open('playergrapple.png'))}
playerAnimations = {}

for key, value in playerAnimationsTemp.items():
    playerAnimations[f"{key}f"] = ImageTk.PhotoImage(
        Image.open(f"{key}.png").transpose(Image.FLIP_LEFT_RIGHT))

    playerAnimations[f"{key}"] = ImageTk.PhotoImage(Image.open(f"{key}.png"))
Bot = PhotoImage(file='bot.png')
