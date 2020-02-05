def mem_free():
    from gc import mem_free
    from machine import freq
    from micropython import mem_info
    return "CPU[Hz]: {}\nGC MemFree[byte]: {}".format(freq(), mem_free())

def reboot():
    from machine import reset
    try:
        from LM_oled_128x64i2c import __deinit
        __deinit()
    except:
        pass
    reset()

def wifi_rssi(essid=None):
    try:
        from Network import wifi_rssi
    except Exception as e:
        return "Network.wifi_rssi import error: " + str(e)
    if essid is None:
        from ConfigHandler import cfgget
        return(wifi_rssi(cfgget('staessid')))
    else:
        return(wifi_rssi(essid))

def addnumbs(*args):
    cnt=0
    msg=""
    for k in args:
        cnt+=k
        msg+="{}+".format(k)
    msg = msg[:-1]
    return "{} = {}".format(msg, cnt)

def time():
    from time import localtime
    return localtime()
