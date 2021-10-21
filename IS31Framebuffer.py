# modified from Adafruit_CircuitPython_Pixel_Framebuf
# this is a work in progress...

from micropython import const
import adafruit_framebuf
import adafruit_is31fl3741
from adafruit_is31fl3741.adafruit_ledglasses import LED_Glasses

# build the table to convert the summed color to a single gamma corrected color
gamma_table = []
def build_gamma():
    for x in range(255*9):
        gamma_table.append(gamma(x))

def gamma(g):
    v = int((g / (255*9)) ** 2.6 * 255 + 0.5)
    return v

HORIZONTAL = const(1)
VERTICAL = const(2)

# pylint: disable=too-many-function-args
class IS31Framebuffer(adafruit_framebuf.FrameBuffer):
    def __init__(
        self,
        glasses,
        width,
        height,
        glasses_width = 18,
        glasses_height = 5,
        orientation=HORIZONTAL,
        alternating=True,
        reverse_x=False,
        reverse_y=False,
        top=0,
        bottom=0,
        rotation=0,
        scale=False,
    ):  # pylint: disable=too-many-arguments
        self._width = width
        self._height = height
        self._glasses_width = glasses_width
        self._glasses_height = glasses_height

        self._glasses = glasses
        self._scale = scale
        self._buffer = bytearray(width * height * 3)
        super().__init__(
            self._buffer, width, height, buf_format=adafruit_framebuf.RGB888
        )
        self.rotation = rotation
        build_gamma()

    def blit(self):
        """blit is not yet implemented"""
        raise NotImplementedError()

    def display(self):
        """Copy the raw buffer changes to the grid and show"""
        for _y in range(self._glasses_height):
            for _x in range(self._glasses_width):
                r = g = b = 0
                if self._scale is True:
                    index = (_y * (self.stride*3) + (_x*3)) * 3
                    for _yy in range(3):
                        for _xx in range(0, 9, 3):
                            r += self._buffer[index+_xx]
                            g += self._buffer[index+1+_xx]
                            b += self._buffer[index+2+_xx]
                        index += self.stride*3
                    r = gamma_table[r]
                    g = gamma_table[g]
                    b = gamma_table[b]
                else:
                    index = (_y * self.stride + _x) * 3
                    r = self._buffer[index]
                    g = self._buffer[index+1]
                    b = self._buffer[index+2]

                self._glasses[self._glasses.pixel_addrs(_x, _y)[self._glasses.r_offset]] = r
                self._glasses[self._glasses.pixel_addrs(_x, _y)[self._glasses.g_offset]] = g
                self._glasses[self._glasses.pixel_addrs(_x, _y)[self._glasses.b_offset]] = b
        self._glasses.show()

    # pylint: disable=too-many-arguments
    def text(self, string, x, y, color, *, font_name="font5x8.bin", size=1):
        """Place text on the screen in variables sizes. Breaks on \n to next line.
        Does not break on line going off screen.
        """
        # determine our effective width/height, taking rotation into account
        frame_width = self.width
        frame_height = self.height
        if self.rotation == 1 or self.rotation == 3:
            frame_width, frame_height = frame_height, frame_width

        for chunk in string.split("\n"):
            width = self._font.font_width
            char_width = 0
            char_x = x
            height = self._font.font_height
            for i, char in enumerate(chunk):
                char_x = char_x + char_width + 3
                char_width = self._font._bdffont.get_glyph(ord(char)).width
                if (
                    char_x + (width * size) > 0
                    and char_x < frame_width
                    and y + (height * size) > 0
                    and y < frame_height
                ):
                    self._font.draw_char(char, char_x, y, self, color, size=size)
            y += height * size


class BDFFont:
    def __init__(self, bdffont):
        self._bdffont = bdffont
        width, height, dx, dy = self._bdffont.get_bounding_box()
        self.font_width = width+dx
        self.font_height = height+dy

    def deinit(self):
        """Close the font file as cleanup."""

    def __enter__(self):
        """Initialize/open the font file"""
        self.__init__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """cleanup on exit"""
        self.deinit()

    def draw_char(
        self, char, x, y, framebuffer, color, size=1
    ):  # pylint: disable=too-many-arguments
        _, height, _, dy = self._bdffont.get_bounding_box()
        self._bdffont.load_glyphs(char)
        """Draw one character at position (x,y) to a framebuffer in a given color"""
        glyph = self._bdffont.get_glyph(ord(char))
        if not glyph:
            return
        for char_y in range(height):
            glyph_y = char_y + (glyph.height - (height + dy))
            if 0 <= glyph_y < glyph.height:
                for i in range(glyph.width):
                    value = glyph.bitmap[i, glyph_y]
                    if value > 0:
                        framebuffer.fill_rect(x + i * size, y + char_y * size, size, size, color)

    def width(self, text):
        """Return the pixel width of the specified text message."""
        return len(text) * (self.font_width + 1)