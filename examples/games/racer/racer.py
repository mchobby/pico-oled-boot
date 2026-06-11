# Retro Racer with OLED Display 128x64 - Comments in English
# Original https://www.makerblog.at
# Adapted to Pico-Oled-Boot
#
# Hardware Requirement:
# - Pico-Oled-Boot
# - Buzzer wired to xxx
#
# Optimization:
#   To avoid floating point numbers (float), all relevant4 positions and speeds are scaled by a factor of 10 and stored as integers.
#   This improves performance and prevents rounding errors.
#
# Scaled Values:
# - All x and y coordinates are stored multiplied by 10.
# - All speeds are stored multiplied by 10.
# - For display rendering, these values are divided by 10.
# Example:
# - A car with x = 150 is actually at 15.0 pixels on the display.
# - A speed of playerSpeed = 25 means a movement of 2.5 px per frame.
#
# This scaling is used in all calculations but is converted back to the actual pixel value when displayed
# (using functions like drawBitmap, drawFastHLine, etc.) by dividing x / 10.
from micropython import const
from oledboot import *
from fbutil import FBUtil
import machine, random, time
display = OledBoot(rotate=90)
display_util = FBUtil( display ) # Utility methods on the target FrameBuffer

PIN_BUZZER = 16

DEBUG_PRINT = False
# Player and lanes
PLAYER_X = display.width-10      # X position of the player's car
PLAYER_WIDTH = const(10)  # Width of the player sprite in pixels
PLAYER_HEIGHT = const(8)  # Height of the cars in pixels

LANES = const(4)                       # Number of lanes
LANE_HEIGHT = (display.height// LANES) # Height of a lane (I replaced Width by height)
OBSTACLE_WIDTH = const(10)             # Width of obstacles in pixels
OBSTACLE_HEIGHT = const(8)             # Height of obstacles in pixels
MAX_OBSTACLES   = const(10)            # Maximum number of possible opponent cars

FRAME_TIME = const(40)  # Target frame rate: 40 ms per frame = 25 FPS
frameCounter = 0  # long
lastFrameTime = 0 # unsigned long

GAME_OVER_DELAY = const(1000)  # 1 second delay after game over
gameOverTime = 0               # Stores the timestamp of game over

# Enumeration for possible game states : enum GameState 
STARTSCREEN = const(0)
HIGHSCORE   = const(1)
PLAYING     = const(2)

gameState = STARTSCREEN

# Note: X coordinates, speeds, and traveled distances are scaled by a factor of 10.
# Calculations are done using integers to avoid floating point numbers.
# Before displaying on the screen, values are divided by 10.

# Data type for opponent properties
class Obstacle:
    __slot__ = ('x','lane','cartype','active') # int, int, int, bool

# High score list
highscores = [0,0,0,0,0,0,0,0,0,0]
newHighscoreIndex = -1
highscoreTime = 0 # unsigned long 
lastBlinkTime = 0 
showBlink = True

# Intro Screen Animation
BITMAP_SPEED = const(5) # Pixels per frame
introSpeedX1 = BITMAP_SPEED
introSpeedX2 = BITMAP_SPEED
introBitmapX1 = 12      # Image 1 starts on-screen on left side
introBitmapX2 = -52     # Image 2 starts off-screen (left)
lastBitmapMove = 0      # unsigned long

# Properties for player, opponents, and lanes
obstacles=[] # Array for opponents
for i in range( MAX_OBSTACLES ):
    obstacles.append( Obstacle() )
playerLane = 2          # Player starts in lane 2
gameOver = False
spawnProbability = 5    # Initial spawn probability for new opponents (1-100)
maxActiveObstacles = 5  # Start with 5 opponents
dashedLineOffset = 0    # Offset for moving dashed lines
distanceCounter = 0     # Total distance traveled in pixels
playerSpeed = 15        # Player speed (px/frame) * factor 10
laneSpeeds = [ 13, 10, 8, 5 ]   # laneSpeeds[LANES] Opponent speeds (px/frame) * factor 10
laneCooldown = [0,0,0,0] # laneCooldown[LANES] Counter for cooldown per lane
MIN_FRAMES_BETWEEN_SPAWNS = const(20) # Minimum waiting time per lane before spawning a new opponent

DEBOUNCE_FRAMES = const(3)  # Number of frames in which no new button input is accepted
debounceCounter = 0

buzzer = machine.PWM( Pin(PIN_BUZZER) )
lastBuzzerFreq  = 0  # Last used frequency for the buzzer

# Graphics for intro, player, and opponents. Converted from PNG using https://javl.github.io/image2cpp/
# 
# Intro car, 24x40px = 120 bytes
intro_bitmap = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x1f\xfe\x00\x00\x000\x03\x00\x00\x01\xe0\x01\x80\x00\x02 \x01\xff\x00\x04 \x01\xc0\x80\x08 \x01\xc0\xf030\x03\xc0\x08#\x1f\xfe\xc1\xcc#\x0c\xfc\xc1\xe4#\x1c\xfe@\x04#<\xff\x03\x84"<\xff\x03\xc4 \x00\x00\x00\x04 \x00\x00\x00\x0c!\xe0\x00\x1e\x0830\x003\x10>\x10\x00!0\x1e\x1f\xff\xe1\xe0\x030\x003\x00\x01\xe0\x00\x1e\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xe0\x00\x80p\x01\x000\x02\x000\x04\xfcx\x08\xf8\xcc\x08\x00\x84\x08\x00\x84\x1f\x8c\xcc0\xdcx |\x10 |\x10 @\x10 @\x10 |\x10 |\x10 |\x10 |\x10 |\x10 |\x100\xdc\x10\x1f\x8c\x10\x0f\xe0\x10\x07\xf0\x10\x04\x00x\x04\x00\xcc\x04\x00\x84\x04\x00\x84\x04\x0c\xcc\x04lx\x03l\x10\x01d\x10\x01 0\x01\x00`\x00\xc1\x80\x00\x7f\x00\x00\x00\x00\x00\x00\x00'
# 10x8px
player_car_ =  b'<f\xc3\xdb~B\xdb\xc3~$' # b'3\x00\x7f\x80\xc4\xc0V@V@\xc4\xc0\x7f\x803\x00' 
# 8x10px = 10 bytes each: SpeedCar, Truck, rock, Truck
cars = [b'~\xc3\xc3f$f\xff\xdbB<' ,b'~\xc3\xc3BBB\xff\xc3B<' ,b'\x00\x008~[{\xe7\xdf~<',
        b'\xc3\xff\xdb\x18\x18\xdb\xc3\xc3$<']
MAX_CAR = len(cars)-1

# Setup
button_left = display.a
button_tight = display.b 

buzzer = machine.PWM( Pin(PIN_BUZZER) )

random.seed(0) # Use Pico Hardware Entropy Pool

def map(value, istart, istop, ostart, ostop):
	# map value between [istart-istop] input interval to its [ostart-ostop] output interval
	# float compatible. Use int() to remove decimal part
	return ostart + (ostop - ostart) * ((value - istart) / (istop - istart))

def saveHighscores(newScore):
    global newHighscoreIndex
    highscores.append( newScore ) # Append a 11th element
    highscores.sort( reverse=True )
    del( highscores[len(highscores)-1] ) # remove the 11th element
    # Identify newHighscoreIndex
    newHighscoreIndex = -1
    for i in range(10):
        if highscores[i]==newScore:
             newHighscoreIndex = i

def resetObstacles():
    global obstacles
    for i in range(MAX_OBSTACLES):
        obstacles[i].x = 0 # X-Position = Position entlang der Fahrspur
        obstacles[i].lane = 0 # zugewiesene Fahrspur
        obstacles[i].cartype = 0 # 2 verschiedene Sprites
        obstacles[i].active = False # gerade aktiv oder nicht?

def resetGame():
    global gameOver,playerLane,playerSpeed,spawnProbability,frameCounter,dashedLineOffset,distanceCounter,maxActiveObstacles,laneCooldown
    gameOver = False
    playerLane = 2       
    playerSpeed = 15   
    spawnProbability = 5
    frameCounter = 0
    dashedLineOffset = 0
    distanceCounter = 0
    maxActiveObstacles = 5
    for i in range(LANES):
        laneCooldown[i] = 0
    resetObstacles()

def renderStartScreen():
    global display,lastBitmapMove,introBitmapX1,introBitmapX2, introSpeedX1, introSpeedX2
    display.fill(0)
    # rotate is mentionned at creation
    # Calculate positions for two bitmaps to create an endless driving effect 
    if time.ticks_diff( time.ticks_ms(),  lastBitmapMove) > 50:
        introBitmapX1 += introSpeedX1
    if introBitmapX1 > (display.height + 12):
        introBitmapX1 = -52
        introSpeedX1 = random.randint(3,8)
    introBitmapX2 += introSpeedX2         
    if introBitmapX2 > (display.height + 12):
        introBitmapX2 = -52
        introSpeedX2 = random.randint(3,8)
    lastBitmapMove = time.ticks_ms()

    display_util.draw_bitmap(introBitmapX1, 3, intro_bitmap, 40, 24, 1) # Last parameter is the color
    display_util.draw_bitmap(introBitmapX2, 16, intro_bitmap, 40, 24, 1)

    display.text( "Pixel", 4, 46, 1)
    display.text( "Racer", 24, 56, 1)
    
    display.text( "~~~"  , 20, 75, 1 )
    
    display.text("Click A", 3,  90, 1)
    display.text("or B to", 3, 100, 1)
    display.text("start"  , 3, 110, 1)
    display.text("  game!", 3, 120, 1)
    
    display.show()

def handleInput():
    global debounceCounter, playerLane
    if debounceCounter > 0:
        debounceCounter -= 1
        return # no input during debounce frames
    
    # Change lane to left if possible
    if display.a.value()==0 and playerLane > 0:
        playerLane -= 1
        debounceCounter = DEBOUNCE_FRAMES

    if display.b.value()==0 and playerLane<(LANES-1):
        playerLane += 1
        debounceCounter = DEBOUNCE_FRAMES

def updateObstacles():
    global obstacles
    for i in range(MAX_OBSTACLES):
        if obstacles[i].active:
            # Calculate the new position of the obstacle relative to the player based on the speed difference
            obstacles[i].x = obstacles[i].x + playerSpeed - laneSpeeds[obstacles[i].lane]
            # If the obstacle moves out of the display area, deactivate it (scale factor 10!)
            if obstacles[i].x > display.width*10: # (-1*OBSTACLE_WIDTH * 10):
                obstacles[i].active = False
     
def updateBuzzer():
    global lastBuzzerFreq
    buzzerFreq = int(map(playerSpeed, 10, 100, 50, 70)) # Map playerSpeed to frequency
    if buzzerFreq != lastBuzzerFreq:               # Update only if frequency has changed
        # tone(PIN_BUZZER, buzzerFreq)
        buzzer.freq( buzzerFreq )
        buzzer.duty_u16( 21000 )
        lastBuzzerFreq = buzzerFreq

def spawnNewObstacle():
    global obstacles
    activeObstacles = 0 # Local 
    for i in range( MAX_OBSTACLES ):
        if obstacles[i].active:
            activeObstacles += 1
    
    if activeObstacles >= maxActiveObstacles:
        return # Do not spawn new obstacles if the limit is reached

    selectedLane = random.randint(0, LANES-1)

    if laneCooldown[selectedLane] > 0:
        return # Do not spawn on this lane if cooldown is still active

    # Find a free slot in the array for a new obstacle
    for i in range( MAX_OBSTACLES ):
        if not obstacles[i].active:
            if random.randint(0,100) < spawnProbability:        
                obstacles[i].x = 10 * 10 #(display.height + 10) * 10  
                obstacles[i].lane = selectedLane
                obstacles[i].cartype = random.randint(0,MAX_CAR)           
                obstacles[i].active = True

                laneCooldown[selectedLane] = MIN_FRAMES_BETWEEN_SPAWNS # Cooldown
                return
    

def checkCollision():
    global gameOver, gameOverTime, distanceCounter
    for i in range(MAX_OBSTACLES):
        # collisionMargin makes collision area more graceful
        collisionMargin = 2 * 10 # local: Scaling *10!
        if obstacles[i].active and obstacles[i].x <= (PLAYER_X*10+PLAYER_WIDTH*10-collisionMargin) and (obstacles[i].x+OBSTACLE_WIDTH*10) >= (PLAYER_X*10+collisionMargin) and obstacles[i].lane==playerLane:            
            gameOver = True
            gameOverTime = time.ticks_ms()
            saveHighscores( distanceCounter )
            buzzer.duty_u16( 0 )

    # When no collision in this frame, add to score
    if not gameOver:
        distanceCounter += playerSpeed


def updateDashedLines():
    global dashedLineOffset
    dashedLineOffset -= playerSpeed
    if dashedLineOffset < -100:
        dashedLineOffset = 0

def updateGameLogic():
    global frameCounter, playerSpeed, laneCooldown, maxActiveObstacles
    updateObstacles()
    updateBuzzer()
    spawnNewObstacle()
    checkCollision()
    updateDashedLines()

    # More speed every 20 frames
    frameCounter += 1
    if (frameCounter % 20) == 0: # Alle 20 Frames
        playerSpeed += 1

    # Cooldown per lane, should prevent 2 cars being generated too close
    for i in range( LANES ):
        if laneCooldown[i] > 0:
            laneCooldown[i] -= 1

    # 1 enemy when starting, raising to 4 quite fast, then raising up to 10 every 500 pixel of player movement
    if distanceCounter < 500:
        maxActiveObstacles = 1
    elif distanceCounter < 1000:
        maxActiveObstacles = 2
    elif distanceCounter < 2000:
        maxActiveObstacles = 3
    elif distanceCounter < 3000:
        maxActiveObstacles = 4
    elif (distanceCounter / 5000 + 5) <= 10:
        maxActiveObstacles = distanceCounter / 5000 + 5

def drawDashedLines():
    for i in range( LANES ):
        for j in range( 0, display.width, 10 ): # was width
            #display.drawFastHLine((j + dashedLineOffset / 10) % SCREEN_WIDTH, i * LANE_HEIGHT, 6, SSD1306_WHITE);
            display.vline( i * LANE_HEIGHT, int((j - dashedLineOffset / 10)) % display.width, 6, 1 )
            


def drawObstacles():
    for i in range(MAX_OBSTACLES):
        if obstacles[i].active:
            # x-coordinate is divided by scale factor 10 to draw in actual pixels
            display_util.draw_bitmap( lanePosition(obstacles[i].lane), obstacles[i].x // 10, cars[obstacles[i].cartype], 8, 10, 1)


def drawPlayer():
    display_util.draw_bitmap(lanePosition(playerLane), PLAYER_X, player_car_, 8, 10, 1)

def drawGameOver():
    display.fill_rect(1, 30, 62, 60, 1)
    display.text("GAME" ,  4, 34, 0)
    display.text("OVER" , 29, 43, 0)
    display.text("Score", 13, 55, 0)
    score = "%i" % (distanceCounter//10)
    display.text( score, 32-len(score)*8//2, 66, 0 ) # Divide by scaling factor 10

def renderHighscoreScreen():
    global showBlink, lastBlinkTime 
    display.fill(0)
    # display.setCursor(2, 6);
    display.hline( 2, 16, 60, 1);
    display.text("HIGHSCORES",2,6,1)

    # The latest score should blink if in the top 10, switching state every 100m
    if time.ticks_diff( time.ticks_ms(), lastBlinkTime > 200):
        showBlink = not( showBlink )
        lastBlinkTime = time.ticks_ms()

    for i in range(10):
        s = "%i. %i" % (i+1, highscores[i]//10)        
        textWidth = len(s)*8
        x = 55-textWidth # Set cursor for left-aligned display
        y = 20+(i*10)

        # If this is the current score, make it blink (not displayed every 100ms)
        # The continue statement skips the next iteration so that the score is not displayed, creating a blinking effect
        if (i==newHighscoreIndex) and not(showBlink):
            continue
        display.text( s, x, y )

    display.show()


def lanePosition( lane ):
      return lane * LANE_HEIGHT + (LANE_HEIGHT - PLAYER_HEIGHT) // 2

def drawDistanceCounter():
    score = "%i" % (distanceCounter//10) # Convert number to string, divide by scaling factor 10
    # MicroPython standard text is 8x8 px
    textWidth, textHeight = len(score)*8, 8
    display.fill_rect( display.height//2 - textWidth//2 - 2, 0, textWidth+4, 8, 0) # Clear rectangle for score display
    #display.setCursor(SCREEN_HEIGHT / 2 - textWidth / 2, 0); # Set cursor to display score text centered
    display.text( score, display.height// 2 - textWidth // 2, 0 ) # Set cursor to display score text centered
    

def renderGame():
    display.fill(0)
    drawDashedLines()
    drawObstacles()
    drawPlayer()
    if gameOver:
        drawGameOver()
    drawDistanceCounter()
    display.show()

def anyKeyPressed():
    return display.a.value()==0 or display.b.value()==0

def loop():
    global gameState, highscoreTime, lastFrameTime
    currentTime = time.ticks_ms()

    # If FRAME_TIME has passed, process the next frame
    if time.ticks_diff( currentTime, lastFrameTime ) < FRAME_TIME:
        return

    # Output frame time if needed:
    if DEBUG_PRINT:
      print("FR: ", time.ticks_diff(currentTime, lastFrameTime) )

    lastFrameTime = currentTime;

    if gameState==STARTSCREEN:
        renderStartScreen()
        if anyKeyPressed():
          resetGame()
          gameState = PLAYING
    
    elif gameState==PLAYING:
        # If gameOver, change state based on elapsed time
        if gameOver:
            if time.ticks_diff( currentTime, gameOverTime ) > 3000: # 3 seconds after Game Over, switch to Highscore screen
                gameState = HIGHSCORE
                highscoreTime = time.ticks_ms()
            # Ignore button presses for 1 second, then allow restarting the game
            if (time.ticks_diff( currentTime, gameOverTime) > 1000) and anyKeyPressed():
                resetGame()
                gameState = PLAYING
        else:
            handleInput()
            updateGameLogic()
        renderGame()
        
    elif gameState==HIGHSCORE:
        renderHighscoreScreen();
        if time.ticks_diff( currentTime, gameOverTime) > 8000: # After 3s Game Over + 5s on Highscore screen, return to Startscreen
            gameState = STARTSCREEN

        if anyKeyPressed():
            resetGame()
            gameState = PLAYING
        

# Start the game
# Reset game data and set status to STARTSCREEN
resetGame()
gameState = STARTSCREEN
while True:
    loop()
