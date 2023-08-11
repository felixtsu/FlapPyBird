from itertools import cycle
import random
import sys
import pygame
from pygame.locals import *

FPS = 120
SCREENWIDTH = 288
SCREENHEIGHT = 512
PIPEGAPSIZE = 120  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT * 0.79
# image, sound and hitmask  dicts
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# list of all possible players (tuple of 3 positions of flap)
PLAYERS_LIST = (
    # red bird
    (
        'assets/sprites/redbird-upflap.png',
        'assets/sprites/redbird-midflap.png',
        'assets/sprites/redbird-downflap.png',
    ),
    # blue bird
    (
        'assets/sprites/bluebird-upflap.png',
        'assets/sprites/bluebird-midflap.png',
        'assets/sprites/bluebird-downflap.png',
    ),
    # yellow bird
    (
        'assets/sprites/yellowbird-upflap.png',
        'assets/sprites/yellowbird-midflap.png',
        'assets/sprites/yellowbird-downflap.png',
    ),
)

# list of backgrounds
BACKGROUNDS_LIST = (
    'assets/sprites/background-day.png',
    'assets/sprites/background-night.png',
)

# list of pipes
PIPES_LIST = (
    'assets/sprites/pipe-green.png',
    'assets/sprites/pipe-red.png',
)

try:
    xrange
except NameError:
    xrange = range


class FlappyGame:

    def __init__(self):
        pass

    def start(self):
        pygame.init()
        self.FPSLOCK = pygame.time.Clock()
        self.SCREENWIDTH = SCREENWIDTH
        self.SCREENHEIGHT = SCREENHEIGHT
        self.SCREEN = pygame.display.set_mode((self.SCREENWIDTH, self.SCREENHEIGHT))
        pygame.display.set_caption('Flappy Bird')

        # numbers sprites for score display
        IMAGES['numbers'] = (
            pygame.image.load('assets/sprites/0.png').convert_alpha(),
            pygame.image.load('assets/sprites/1.png').convert_alpha(),
            pygame.image.load('assets/sprites/2.png').convert_alpha(),
            pygame.image.load('assets/sprites/3.png').convert_alpha(),
            pygame.image.load('assets/sprites/4.png').convert_alpha(),
            pygame.image.load('assets/sprites/5.png').convert_alpha(),
            pygame.image.load('assets/sprites/6.png').convert_alpha(),
            pygame.image.load('assets/sprites/7.png').convert_alpha(),
            pygame.image.load('assets/sprites/8.png').convert_alpha(),
            pygame.image.load('assets/sprites/9.png').convert_alpha()
        )

        # game over sprite
        IMAGES['gameover'] = pygame.image.load('assets/sprites/gameover.png').convert_alpha()
        # message sprite for welcome self.SCREEN
        IMAGES['message'] = pygame.image.load('assets/sprites/message.png').convert_alpha()
        # base (ground) sprite
        IMAGES['base'] = pygame.image.load('assets/sprites/base.png').convert_alpha()

        # sounds
        if 'win' in sys.platform:
            soundExt = '.wav'
        else:
            soundExt = '.ogg'

        SOUNDS['die'] = pygame.mixer.Sound('assets/audio/die' + soundExt)
        SOUNDS['hit'] = pygame.mixer.Sound('assets/audio/hit' + soundExt)
        SOUNDS['point'] = pygame.mixer.Sound('assets/audio/point' + soundExt)
        SOUNDS['swoosh'] = pygame.mixer.Sound('assets/audio/swoosh' + soundExt)
        SOUNDS['wing'] = pygame.mixer.Sound('assets/audio/wing' + soundExt)

        # select random background sprites
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = pygame.image.load(BACKGROUNDS_LIST[randBg]).convert()

        # select random player sprites
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            pygame.image.load(PLAYERS_LIST[randPlayer][0]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][1]).convert_alpha(),
            pygame.image.load(PLAYERS_LIST[randPlayer][2]).convert_alpha(),
        )

        # select random pipe sprites
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        IMAGES['pipe'] = (
            pygame.transform.flip(
                pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(), False, True),
            pygame.image.load(PIPES_LIST[pipeindex]).convert_alpha(),
        )

        # hitmask for pipes
        HITMASKS['pipe'] = (
            self.getHitMask(IMAGES['pipe'][0]),
            self.getHitMask(IMAGES['pipe'][1]),
        )

        # hitmask for player
        HITMASKS['player'] = (
            self.getHitMask(IMAGES['player'][0]),
            self.getHitMask(IMAGES['player'][1]),
            self.getHitMask(IMAGES['player'][2]),
        )

        movementInfo = self.showWelcomeAnimation()
        crashInfo = self.mainGame(movementInfo)

    def reset(self):
        self.start()

    def passFirstPipe(self):
        playerMidPos = self.playerx + IMAGES['player'][0].get_width() / 2
        pipe = self.lowerPipes[0]
        pipeEndPos = pipe['x'] + IMAGES['pipe'][0].get_width()
        return pipeEndPos <= playerMidPos

    def getNextLowerPipe(self):
        for lp in self.lowerPipes:
            if not lp['pass']:
                return lp
        return None

    # 获取小鸟的垂直坐标x
    def getPlayerX(self):
        return self.playerx

    # 获取小鸟的垂直坐标y
    def getPlayerY(self):
        return self.playery

    # 获取下一根柱子的水平距离
    def getNextPillarDis(self):
        nextLowerPipe = self.getNextLowerPipe()
        # if len(self.lowerPipes) == 0:
        if nextLowerPipe == None:
            return self.SCREENWIDTH - self.playerx
        deltaX = nextLowerPipe['x'] + IMAGES['pipe'][0].get_width() / 2 - self.playerx
        return deltaX

    # 获取下一根柱子的的垂直距离 （y）
    def getNextPillarCenterY(self):
        nextLowerPipe = self.getNextLowerPipe()
        # if len(self.lowerPipes) == 0:
        if nextLowerPipe == None:
            return self.playery + IMAGES['player'][0].get_width() / 2 - BASEY // 2
        return self.playery + IMAGES['player'][0].get_width() / 2 - nextLowerPipe['y']

    # 获取小鸟的垂直速度 vy
    def getPlayerVy(self):
        return self.playerVelY

    def showWelcomeAnimation(self):
        """Shows welcome self.SCREEN animation of flappy bird"""
        # index of player to blit on self.SCREEN
        self.playerIndex = 0
        playerIndexGen = cycle([0, 1, 2, 1])
        # iterator used to change playerIndex after every 5th iteration
        loopIter = 0

        self.playerx = int(self.SCREENWIDTH * 0.2)
        playery = int((self.SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)

        messagex = int((self.SCREENWIDTH - IMAGES['message'].get_width()) / 2)
        messagey = int(self.SCREENHEIGHT * 0.12)

        basex = 0
        # amount by which base can maximum shift to left
        baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

        # player shm for up-down motion on welcome self.SCREEN
        playerShmVals = {'val': 0, 'dir': 1}
        SOUNDS['wing'].play()
        return {
            'playery': playery + playerShmVals['val'],
            'basex': basex,
            'playerIndexGen': playerIndexGen,
        }

    def mainGame(self, movementInfo):
        self.score = self.playerIndex = self.loopIter = 0
        self.playerIndexGen = movementInfo['playerIndexGen']
        self.playerx, self.playery = int(self.SCREENWIDTH * 0.2), movementInfo['playery']

        self.basex = movementInfo['basex']
        self.baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

        # get 2 new pipes to add to upperPipes lowerPipes list
        newPipe1 = self.getRandomPipe()
        newPipe2 = self.getRandomPipe()

        # list of upper pipes
        self.upperPipes = [
            {'x': self.SCREENWIDTH + 200, 'y': newPipe1[0]['y'], 'pass': False},
            {'x': self.SCREENWIDTH + 200 + (self.SCREENWIDTH / 2), 'y': newPipe2[0]['y'], 'pass': False},
        ]

        # list of lowerpipe
        self.lowerPipes = [
            {'x': self.SCREENWIDTH + 200, 'y': newPipe1[1]['y'], 'pass': False},
            {'x': self.SCREENWIDTH + 200 + (self.SCREENWIDTH / 2), 'y': newPipe2[1]['y'], 'pass': False},
        ]

        self.dt = self.FPSLOCK.tick(FPS) / 1000
        self.pipeVelX = -128 * self.dt

        # player velocity, max velocity, downward acceleration, acceleration on flap
        self.playerVelY = -9  # player's velocity along Y, default same as playerFlapped
        self.playerMaxVelY = 10  # max vel along Y, max descend speed
        self.playerMinVelY = -8  # min vel along Y, max ascend speed
        self.playerAccY = 1  # players downward acceleration
        self.playerRot = 45  # player's rotation
        self.playerVelRot = 3  # angular speed
        self.playerRotThr = 20  # rotation threshold
        self.playerFlapAcc = -9  # players speed on flapping
        self.playerFlapped = False  # True when player flaps

    def play_step(self, action):
        if action[1] == 1:
            if self.playery > -2 * IMAGES['player'][0].get_height():
                self.playerVelY = self.playerFlapAcc
                self.playerFlapped = True
                SOUNDS['wing'].play()

        # check for crash here
        crashTest = self.checkCrash({'x': self.playerx, 'y': self.playery, 'index': self.playerIndex},
                                    self.upperPipes, self.lowerPipes)
        if crashTest[0]:
            return -1000, True, self.score, {
                'y': self.playery,
                'groundCrash': crashTest[1],
                'basex': self.basex,
                'upperPipes': self.upperPipes,
                'lowerPipes': self.lowerPipes,
                'score': self.score,
                'playerVelY': self.playerVelY,
                'playerRot': self.playerRot
            }

        # check for score
        reward = 0.5
        playerMidPos = self.playerx + IMAGES['player'][0].get_width() / 2
        for pipe in self.upperPipes:
            if pipe['pass']:
                continue
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 16:
                reward = 5
                self.score += 1
                pipe['pass'] = True
                SOUNDS['point'].play()

        # playerIndex basex change
        if (self.loopIter + 1) % 3 == 0:
            self.playerIndex = next(self.playerIndexGen)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)

        # rotate the player
        if self.playerRot > -90:
            self.playerRot -= self.playerVelRot

        # player's movement
        if self.playerVelY < self.playerMaxVelY and not self.playerFlapped:
            self.playerVelY += self.playerAccY
        if self.playerFlapped:
            self.playerFlapped = False

            # more rotation to cover the threshold (calculated in visible rotation)
            self.playerRot = 45

        playerHeight = IMAGES['player'][self.playerIndex].get_height()
        self.playery += min(self.playerVelY, BASEY - self.playery - playerHeight)

        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        # add new pipe when first pipe is about to touch left of self.SCREEN
        if 3 > len(self.upperPipes) > 0 and 0 < self.upperPipes[0]['x'] < 5:
            newPipe = self.getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the self.SCREEN
        if len(self.upperPipes) > 0 and self.upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)

        # draw sprites
        self.SCREEN.blit(IMAGES['background'], (0, 0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            self.SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            self.SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        self.SCREEN.blit(IMAGES['base'], (self.basex, BASEY))
        # print score so player overlaps the score
        self.showScore(self.score)

        # Player rotation has a threshold
        self.visibleRot = self.playerRotThr
        if self.playerRot <= self.playerRotThr:
            self.visibleRot = self.playerRot

        self.playerSurface = pygame.transform.rotate(IMAGES['player'][self.playerIndex], self.visibleRot)
        self.SCREEN.blit(self.playerSurface, (self.playerx, self.playery))

        pygame.display.update()

        self.FPSLOCK.tick(FPS)
        #
        # ratio = abs(self.getNextPillarDis() / (self.getNextPillarCenterY()+50))
        # reward *= ratio

        return reward, False, self.score, None

    def showGameOverScreen(self, crashInfo):
        """crashes the player down and shows gameover image"""
        score = crashInfo['score']
        self.playerx = self.SCREENWIDTH * 0.2
        self.playery = crashInfo['y']
        self.playerHeight = IMAGES['player'][0].get_height()
        self.playerVelY = crashInfo['playerVelY']
        self.playerAccY = 2
        self.playerRot = crashInfo['playerRot']
        self.playerVelRot = 7

        self.basex = crashInfo['basex']

        self.upperPipes, self.lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']

        # play hit and die sounds
        SOUNDS['hit'].play()
        if not crashInfo['groundCrash']:
            SOUNDS['die'].play()

        while True:
            for event in pygame.event.get():
                if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    pygame.quit()
                    sys.exit()
                if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP):
                    if self.playery + self.playerHeight >= BASEY - 1:
                        return

            # player y shift
            if self.playery + self.playerHeight < BASEY - 1:
                self.playery += min(self.playerVelY, BASEY - self.playery - self.playerHeight)

            # player velocity change
            if self.playerVelY < 15:
                self.playerVelY += self.playerAccY

            # rotate only when it's a pipe crash
            if not crashInfo['groundCrash']:
                if self.playerRot > -90:
                    self.playerRot -= self.playerVelRot

            # draw sprites
            self.SCREEN.blit(IMAGES['background'], (0, 0))

            for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
                self.SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
                self.SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

            self.SCREEN.blit(IMAGES['base'], (self.basex, BASEY))
            self.showScore(score)

            playerSurface = pygame.transform.rotate(IMAGES['player'][1], self.playerRot)
            self.SCREEN.blit(playerSurface, (self.playerx, self.playery))
            self.SCREEN.blit(IMAGES['gameover'], (50, 180))

            self.FPSLOCK.tick(FPS)
            pygame.display.update()

    def playerShm(self, playerShm):
        """oscillates the value of playerShm['val'] between 8 and -8"""
        if abs(playerShm['val']) == 8:
            playerShm['dir'] *= -1

        if playerShm['dir'] == 1:
            playerShm['val'] += 1
        else:
            playerShm['val'] -= 1

    def getRandomPipe(self):
        """returns a randomly generated pipe"""
        # y of gap between upper and lower pipe
        gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
        gapY += int(BASEY * 0.2)
        pipeHeight = IMAGES['pipe'][0].get_height()
        pipeX = self.SCREENWIDTH + 10

        return [
            {'x': pipeX, 'y': gapY - pipeHeight, 'pass': False},  # upper pipe
            {'x': pipeX, 'y': gapY + PIPEGAPSIZE, 'pass': False},  # lower pipe
        ]

    def showScore(self, score):
        """displays score in center of self.SCREEN"""
        scoreDigits = [int(x) for x in list(str(score))]
        totalWidth = 0  # total width of all numbers to be printed

        for digit in scoreDigits:
            totalWidth += IMAGES['numbers'][digit].get_width()

        Xoffset = (self.SCREENWIDTH - totalWidth) / 2

        for digit in scoreDigits:
            self.SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, self.SCREENHEIGHT * 0.1))
            Xoffset += IMAGES['numbers'][digit].get_width()

    def checkCrash(self, player, upperPipes, lowerPipes):
        """returns True if player collides with base or pipes."""
        pi = player['index']
        player['w'] = IMAGES['player'][0].get_width()
        player['h'] = IMAGES['player'][0].get_height()

        # if player crashes into ground
        if player['y'] + player['h'] >= BASEY - 1 or player['y'] <= 16:
            return [True, True]
        else:

            playerRect = pygame.Rect(player['x'], player['y'],
                                     player['w'], player['h'])
            pipeW = IMAGES['pipe'][0].get_width()
            pipeH = IMAGES['pipe'][0].get_height()

            for uPipe, lPipe in zip(upperPipes, lowerPipes):
                # upper and lower pipe rects
                uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
                lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

                # player and upper/lower pipe hitmasks
                pHitMask = HITMASKS['player'][pi]
                uHitmask = HITMASKS['pipe'][0]
                lHitmask = HITMASKS['pipe'][1]

                # if bird collided with upipe or lpipe
                uCollide = self.pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
                lCollide = self.pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

                if uCollide or lCollide:
                    return [True, False]

        return [False, False]

    def pixelCollision(self, rect1, rect2, hitmask1, hitmask2):
        """Checks if two objects collide and not just their rects"""
        rect = rect1.clip(rect2)

        if rect.width == 0 or rect.height == 0:
            return False

        x1, y1 = rect.x - rect1.x, rect.y - rect1.y
        x2, y2 = rect.x - rect2.x, rect.y - rect2.y

        for x in xrange(rect.width):
            for y in xrange(rect.height):
                if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                    return True
        return False

    def getHitMask(self, image):
        """returns a hitmask using an image's alpha."""
        mask = []
        for x in xrange(image.get_width()):
            mask.append([])
            for y in xrange(image.get_height()):
                mask[x].append(bool(image.get_at((x, y))[3]))
        return mask
