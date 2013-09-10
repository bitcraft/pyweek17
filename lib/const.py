import pygame


volume = .4

TILESIZE = 48
TIMESTEP = 30.0
COLORSTEP = 8

REGOLITH = 0
BARREN = 1
STOCKPILE = 2
FARM = 3
ENERGY = 4
KITCHEN = 5
BARRACKS = 6
FOOD = 7

transport_map = {
    FARM: KITCHEN,
    REGOLITH: STOCKPILE,
}

primary_colors = [
    '#75987c', #lunar green
    '#403d32', #wet dirt
    '#a2000d', #red
    '#1b5a2c', #algae
    '#3f9089', #tiffany blue
    '#f7a50d', #sunset orange
    '#ef899b', #warm pink
    '#75202d', #maroon
    '#09303a', #dark navy blue
    '#bc9e60', #khaki
    '#403e30', #dark rust
    '#191e18', #black
    '#e0e2e0', #light grey
    '#f9f9f0', #white
]


colors = []
for i, c in enumerate(primary_colors[:-2]):
    color = pygame.Color(c)
    r, g, b = color.r, color.g, color.b
    for x in range(16):
        if r >= 7:
            r -= 7
        if g >= 7:
            g -= 7
        if b >= 7:
            b -= 7
        colors.append(pygame.Color(r, g, b))

tblocks = [
    ((0,0,0), (1,0,0), (1,-1,0), (0,-1,0)),
    ((0,0,0), (1,0,0), (-1,0,0), (0,1,0)),
    ((-2,0,0), (-1,0,0), (0,0,0), (1,0,0), (2,0,0)),
    ((-1,-1,0), (0,-1,0), (0,0,0), (1,0,0)),
    ((-1,0,0), (0,0,0), (0,-1,0), (1,-1,0)),
    ((-1,0,0), (0,0,0), (0,-1,0), (0,-2,0)),
    ((1,0,0), (0,0,0), (0,-1,0), (0,-2,0))
]


status_msg = {
    'idle': 'your minions are idle. drop some tiles around them so they can work',
    'regolith1': 'place tiles and create a 5x5 square of any color to extract materials',
    'regolith2': 'materials can be traded for bonuses',
    'prepare': 'prepare for the next wave by placing blue energy tiles',
    'lowenergy': 'your energy is too low.  place blue tiles to increase energy for your turrets',
    'levelup': 'minions grow stronger as they complete tasks. try to keep them busy',
    'clone1': 'minions will clone a new minion by mining green tiles and filling yellow tiles',
    'clone2': 'clones start weak.  be sure to keep the clones busy.'
}
