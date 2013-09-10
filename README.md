Bitcraft's PyWeek 17 Entry: Tetris Tower Defense!
=================================================    
    

Gameplay
--------

*Place tetris blocks on the map to build a strong base.  Organize the base and work with AI minions.*

Each block color has a different purpose.  AI minions will mine blocks and transform them into different things.  In this unfinished game, the minions can only create more minions.

Waves of enemies will appear after a delay.  Try to survive!  (actually, it is really easy to survive since the game didn't get balanced at all!)

Running the Game
----------------

This game was developed with python 2.7 and pygame 1.9.1.  Please make sure you are using python 2.7 to run the game.

Controls
--------

use the mouse to place tetris blocks on the isometric landscape.  
right mouse button rotates the block, left button places the block.

blocks can be placed on top of an existing block, however, any overlapping areas will be converted into a 'barren' tile, which has no benefits to the player.

If a 5x5 square is created of any color besides 'barren' (the default color), the blocks will be converted to a color not accessible by dropping blocks.  this color has no use, however.

Game Elements
-------------

Four cannons are already placed on the map.  They require energy to fire.  You can produce energy by placing blue blocks.  The more blue blocks that are one the map, the more energy you will have for your cannons.  Your current energy and capacity is measured by the lowest bar on the HUD.

The cannons will automatically fire at enemies.  Just make sure you have enough blue energy tile to keep them firing quickly.

The thief is a large light blue colored block. It will mine your energy blocks and lower your ability ot fire your cannons.  As it mines blue energy blocks, it will grow in size and will be more difficult to kill.

The hunter is a large dark blue block.  It will consume your minions.


Minions
=======

The minions will mine green resource blocks and fill yellow blocks.  Once a yellow block is filled, a new minion will appear.  Minions will gain experience points as they carry out tasks.  This will cause them to grow slightly larger and will more faster.


## Notable Features ##
* Complex AI is possible
* Drawing engine is 3D (can be rotated)
* Small code size

## Missing Features ##
* There is no introduction to gameplay concepts
* The game is not balanced
* There are no real animations to enhance the game
* Minions are missing a graphic element to show that they are carrying blocks
