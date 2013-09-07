import pygame



TILESIZE = 48
TIMESTEP = 30.0
COLORSTEP = 8

REGOLITH = 0
STOCKPILE = 1
FARM = 2
WATER = 3
ORIGIN = 4
FOOD = 5
BARREN = 6
KITCHEN = 7


primary_colors = [
    '#75987c', #lunar green
    '#f7a50d', #sunset orange
    '#1b5a2c', #algae
    '#a2000d', #red
    '#403d32', #wet dirt
    '#ef899b', #warm pink
    '#3f9089', #tiffany blue
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

