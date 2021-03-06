from ConfigHandler import cfgget
from gc import mem_free
from time import localtime

__OLED = None
__INVERT = False

def __init():
    global __OLED
    if __OLED is None:
        from machine import Pin, I2C
        from ssd1306 import SSD1306_I2C
        from LogicalPins import get_pin_on_platform_by_key
        i2c = I2C(-1, Pin(get_pin_on_platform_by_key('i2c_scl')), Pin(get_pin_on_platform_by_key('i2c_sda')))
        __OLED = SSD1306_I2C(128, 64, i2c)
    return __OLED

def simple_page():
    try:
        # Clean screen
        __init().fill(0)
        # Draw time
        __OLED.text("{}:{}:{}".format(localtime()[-5], localtime()[-4], localtime()[-3]), 30, 10)
        __OLED.show()
    except Exception as e:
        return str(e)
    return True


def show_debug_page():
    try:
        # Clean screen
        __init().fill(0)
        __OLED.show()
        # Print info
        ltime = localtime()
        __OLED.text("{}:{}:{}".format(ltime[-5], ltime[-4], ltime[-3]), 30, 0)
        __OLED.text("NW_MODE: {}".format(cfgget("nwmd")), 0, 10)
        __OLED.text("IP: {}".format(cfgget("devip")), 0, 20)
        __OLED.text("FreeMem: {}".format(mem_free()), 0, 30)
        __OLED.text("PORT: {}".format(cfgget("socport")), 0, 40)
        __OLED.text("NAME: {}".format(cfgget("devfid")), 0, 50)
        # Show page buffer - send to display
        __OLED.show()
    except Exception as e:
        return str(e)
    return True

def toggle_invert():
    global __INVERT
    __INVERT = not __INVERT
    __init().invert(__INVERT)
    return 'INVERT:{}'.format(__INVERT)


def help():
    return 'simple_page', 'show_debug_page', 'toggle_invert'

