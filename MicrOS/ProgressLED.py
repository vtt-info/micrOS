# VERSION 1.0
import machine
import time

#################################################################
#          _____ _                _____ _____                   #
#         / ____| |        /\    / ____/ ____|                  #
#        | |    | |       /  \  | (___| (___                    #
#        | |    | |      / /\ \  \___ \\___ \                   #
#        | |____| |____ / ____ \ ____) |___) |                  #
#         \_____|______/_/    \_\_____/_____/                   #
#################################################################
class Pled(object):
    __instance = None
    def __new__(cls, name="progress_led", led_pin=16):
        if cls.__instance is None:
            cls.led = machine.Pin(led_pin, machine.Pin.OUT)
            cls.__instance = object.__new__(cls)
            cls.__instance.name = name
        return cls.__instance

    def toggle(cls):
        if cls.led.value() == 0:
            cls.led.value(1)
        elif cls.led.value() == 1:
            cls.led.value(0)
        else:
            print("UNKNOWN STATUS")

    def ON(cls):
        cls.led.value(0)

    def OFF(cls):
        cls.led.value(1)

#################################################################################################################
#  _____ _   _  _____ _______       _   _ _______ _____       _______ ______                                    #
# |_   _| \ | |/ ____|__   __|/\   | \ | |__   __|_   _|   /\|__   __|  ____|                                   #
#   | | |  \| | (___    | |  /  \  |  \| |  | |    | |    /  \  | |  | |__                                      #
#   | | | . ` |\___ \   | | / /\ \ | . ` |  | |    | |   / /\ \ | |  |  __|                                     #
#  _| |_| |\  |____) |  | |/ ____ \| |\  |  | |   _| |_ / ____ \| |  | |____                                    #
# |_____|_| \_|_____/   |_/_/    \_\_| \_|  |_|  |_____/_/    \_\_|  |______| a singleton, return instance      #
#################################################################################################################
if "ProgressLED" in __name__:
    pled = Pled()

#################################################################
#         _____  ______ __  __  ____                            #
#        |  __ \|  ____|  \/  |/ __ \                           #
#        | |  | | |__  | \  / | |  | |                          #
#        | |  | |  __| | |\/| | |  | |                          #
#        | |__| | |____| |  | | |__| |                          #
#        |_____/|______|_|  |_|\____/ and TEST                  #
#################################################################
def pled_demo():
    pled = Pled()
    while True:
        pled.toggle()
        time.sleep(0.1)

if __name__ == "__main__":
    pled_demo()