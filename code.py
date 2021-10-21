import time
import board
from busio import I2C
from adafruit_bitmap_font import bitmap_font
import adafruit_is31fl3741
from adafruit_is31fl3741.adafruit_ledglasses import LED_Glasses
import IS31Framebuffer

#font_file = "tom_thumb.bdf" # 3x5 font
font_file = "tfont.bdf"
font = bitmap_font.load_font(font_file)

message = "CIRCUITPYTHON!"

# Manually declare I2C (not board.I2C() directly) to access 1 MHz speed...
i2c = I2C(board.SCL, board.SDA, frequency=1000000)

# Initialize the IS31 LED driver, buffered for smoother animation
glasses = LED_Glasses(i2c, allocate=adafruit_is31fl3741.MUST_BUFFER)
glasses.show()
glasses.global_current = 20

fb = IS31Framebuffer.IS31Framebuffer(glasses, 18*3, 5*3, glasses_width=18, glasses_height=5, scale=True)
#fb = IS31Framebuffer.IS31Framebuffer(glasses, 18, 5)

fb._font = IS31Framebuffer.BDFFont(font)

width = fb._font.width(message)
x=54
t = time.monotonic()
length = len(fb.buf)
while True:
    # rather then framebuffer.fill this seemed slightly faster
    for i in range(length):
        fb.buf[i] = 0x00
    fb.text(message, x, 0, 0xA000A0)
    fb.display()

    print(1/(time.monotonic()-t))
    t = time.monotonic()

    x = x - 1
    if x < -width:
        x = 54

while True:
    pass