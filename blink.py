import time
import sys
import os
from random import randrange
sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/..'))
from rgbmatrix import RGBMatrix, RGBMatrixOptions

from PIL import Image, ImageFile
from PIL import PngImagePlugin

ROWS = 32
COLS = 64


ImageFile.LOAD_TRUNCATED_IMAGES = True
options = RGBMatrixOptions()

options.hardware_mapping = 'adafruit-hat'
options.rows = ROWS
options.cols = COLS
options.parallel = 1

matrix = RGBMatrix(options = options)

def show_image(image_file: str):
    print(Image.registered_extensions())
    image = Image.open(image_file)
    print(image.getpixel((1, 1)))
          #image.thumbnail((matrix.width, matrix.height), Image.LANCZOS)
    image = image.convert("RGB")
    print(dir(image))
    print(image.getpixel((1,1)))
    matrix.SetImage(image)


def fill(r, g, b):
    for x in range(COLS):
        for y in range(ROWS):
            matrix.SetPixel(x, y, r, g, b)
            time.sleep(0.005)

def rainbow_fill():

    # rd, gd, bd 0 is down 1 is up
    r = 255
    rd = 1
    g = 0
    gd = 1
    b = 0
    bd = 0
    #matrix.Clear()

    for y in range(ROWS):
        for x in range(COLS):
            if r == 255 and g == 0 and b == 0: # max red
                gd = 1

            if g == 255 and r == 255:  # Yellow
                rd = 0

            if g == 255 and r == 0 and b == 0:  # max green
                bd = 1

            if g == 255 and b == 255: # cyan
                gd = 0

            if b == 255 and r == 0 and g == 0: # max blue
                rd = 1
            
            if b == 255 and r == 255:  # Purple
                bd = 0 


            if rd:
                r += 1
            else:
                r -= 1
            if gd:
                g += 1
            else:
                g -= 1
            if bd:
                b += 1
            else:
                b -= 1

            if r >= 255:
                r = 255
            if r <= 0:
                r = 0
            if g >= 255:
                g = 255
            if g <= 0:
                g = 0
            if b >= 255:
                b = 255
            if b <= 0:
                b = 0
            matrix.SetPixel(x, y, r, g, b)
            time.sleep(0.005)
    time.sleep(5)

def rand_fill():
    #matrix.Clear()
    for _ in range(1000):
        r = randrange(256)
        g = randrange(256)
        b = randrange(256)
        x = randrange(64)
        y = randrange(32)
    
        matrix.SetPixel(x, y, r, g, b)

        time.sleep(0.01)

def drop_fill():
    for x in range(COLS):
        pr, pg, pb = 0, 0, 0
        for y in range(ROWS):
            r = randrange(100, 256)
            g = randrange(100, 256)
            b = randrange(100, 256)
            matrix.SetPixel(x, y, r, g, b)
            if y != 0:
                matrix.SetPixel(x, y - 1, pr - 50, pg - 50, pb - 50)
            pr, pg, pb = r, g, b
            time.sleep(0.01)

 


while True:
    rand_fill()
    #fill(255, 5, 150)
    drop_fill()
    rainbow_fill()
    #show_image('image/kc.png')
