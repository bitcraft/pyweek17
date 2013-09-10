Bitcraft's PyWeek 17 Entry: Tetris Tower Defense!
=================================================    
    

Gameplay
--------

*Place tetris blocks on the map to build a strong base.  Organize the base and work with AI minions.*

Waves of enemies will appear after a delay.  Try to survive!  (actually, it is really easy to survive since the game isn't balanced at all yet!)


Running the Game
----------------

This game was developed with python 2.7 and pygame 1.9.1.  Please make sure you are using python 2.7 to run the game.


Controls
--------

Use the mouse to place tetris blocks on the landscape.  
The right mouse button rotates the block, left button places the block.

Blocks can be placed on top of an existing block, however, any overlapping areas will be converted into a 'barren' tile, which has no benefits to the player.

If a 5x5 square is created of any color besides 'barren' (the default color), the blocks will be converted to a color not accessible by dropping blocks.

Turrets automatically attack incomming enemies.  Each tower has a 7 tile radius and can target up to 3 enemies at once.  Each barrage of shots (up to 3) will be randomly chosen enemies.  If there are fewer than 3 enemies near the tower, the 3 shots will be given to the 2 or 1 enemies, dealing more damage per enemy.


Game Elements
-------------

Four cannons are already placed on the map.  They require energy to fire.  You can produce energy by placing blue blocks.  The more blue blocks that are one the map, the more energy you will have for your cannons.  Your current energy and capacity is measured by right bar on the HUD.

The cannons will automatically fire at enemies.  Just make sure you have enough blue energy tile to keep them firing quickly.

The thief is a large light blue colored block. It will mine your energy blocks and lower your ability to fire your cannons.  As it mines blue energy blocks, it will grow in size and will be more difficult to kill.

The hunter is a large dark blue block.  It will consume your minions.


Minions
-------

The minions will mine green resource blocks and fill yellow blocks.  Once a yellow block is filled, a new minion will appear.  Minions will gain experience points as they carry out tasks.  This will cause them to grow slightly larger and will more faster.


Strategy
--------

Minions will fill yellow block that they are closest to.  Since you want to fill the yellow blocks quickly, you can place blocks on unused yellow blocks to destory them.  This will encourge the minions to fill yellow blocks faster (since there will be less).

Red blocks have no utility except as pathways, but you can use them to destory excess yellow blocks.

You will want to have a lot of blue tiles, especially in the end of the game.  Placing them in the center will protect them from the Thief enemy.

Don't be affraid to destroy existing blocks.


## Missing Features ##
* There is no introduction to gameplay concepts
* The game is not balanced
* There are no real animations to enhance the game
* Minions are missing a graphic element to show that they are carrying blocks
