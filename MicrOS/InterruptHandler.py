"""
Module is responsible for hardware interrupt
handling dedicated to micrOS framework.
- Setting up interrupt memory buffer from config
- Configure time based and external interrupts

- Time based IRQ:
    - Simple with fix period callback
    - Advanced - time stump ! LM function;
    -            0-6:0-24:0-59:0-59!system heartbeat; etc.

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                            IMPORTS                            #
#################################################################
from ConfigHandler import cfgget, console_write
from InterpreterCore import execute_LM_function_Core
from LogicalPins import get_pin_on_platform_by_key
from Scheduler import scheduler


# TIMER IRQ AND CRON VALUES PERSISTENT CACHE
# timirqcbf (simple), crontasks, timirqseq
CFG_TIMER_IRQ = ['n/a', 3]

# EVENT IRQ VALUE PERSISTENT CACHE
CFG_EVIRQCBF = 'n/a'

#################################################################
#            CONFIGURE INTERRUPT MEMORY BUFFER                  #
#################################################################


def set_emergency_buffer():
    emergency_buff_kb = cfgget('irqmembuf')
    if cfgget('extirq') or cfgget("timirq"):
        from micropython import alloc_emergency_exception_buf
        console_write("[IRQ] Interrupts was enabled, alloc_emergency_exception_buf={}".format(emergency_buff_kb))
        alloc_emergency_exception_buf(emergency_buff_kb)
    else:
        console_write("[IRQ] Interrupts disabled, skip alloc_emergency_exception_buf configuration.")

#################################################################
#                       TIMER INTERRUPT(S)                      #
#################################################################

#############################################
#     [TIMER] TIMIRQ CBFs - LM executor     #
#############################################


def secureInterruptHandlerSimple(timer=None):
    try:
        # Execute CBF from cached config
        state = execute_LM_function_Core(CFG_TIMER_IRQ[0].split(' '))
        if not state:
            console_write("[IRQ] TIMIRQ execute_LM_function_Core error: {}".format(CFG_TIMER_IRQ[0]))
    except Exception as e:
        console_write("[IRQ] TIMIRQ callback: {} error: {}".format(CFG_TIMER_IRQ[0], e))


def secureInterruptHandlerScheduler(timer=None):
    try:
        # Execute CBF LIST from local cached config with timirqseq in sec
        scheduler(CFG_TIMER_IRQ[0], CFG_TIMER_IRQ[1])
    except Exception as e:
        console_write("[IRQ] TIMIRQ (cron) callback: {} error: {}".format(CFG_TIMER_IRQ[0], e))


#############################################
#         [TIMER] INIT TIMIRQ SET CBF       #
#############################################


def enableInterrupt():
    """
    TIMER INTERRUPT CALLBACK FUNCTION CONFIG. WRAPPER
    - FIRST PRIORITY: SCHEDULER
    - SECOND PRIORITY: SIMPLE PERIODIC CALLBACK
    """
    console_write("[IRQ] TIMIRQ SETUP - TIMIRQ: {} SEQ: {}".format(cfgget("timirq"), cfgget("timirqseq")))
    console_write("|- [IRQ] CRON:{} CBF:{}".format(cfgget('cron'), cfgget('crontasks')))
    console_write("|- [IRQ] SIMPLE CBF:{}".format(cfgget('timirqcbf')))
    if cfgget("timirq"):
        # Configure advanced scheduler OR simple repeater
        if cfgget('cron') and cfgget('crontasks').lower() != 'n/a':
            console_write("|-- TIMER IRQ MODE: SCHEDULER")
            # ENABLE ADVANCED SCHEDULER (BASED ON SIMPLE TIMIRQ)
            __enableInterruptScheduler()
            return
        # ENABLE SIMPLE PERIODIC INTERRUPT
        console_write("|-- TIMER IRQ MODE: SIMPLE")
        __enableInterruptSimple()


def __enableInterruptScheduler():
    """
    SMART TIMER INTERRUPT CONFIGURATION
    # MUST BE CHECK BEFORE CALL: cfgget("timirq") and cfgget('cron') and cfgget('crontasks')
    """
    # CACHE TASKS FOR CBF
    CFG_TIMER_IRQ[0] = cfgget('crontasks')
    CFG_TIMER_IRQ[1] = int(cfgget("timirqseq") / 1000)
    from machine import Timer
    # INIT TIMER IRQ with callback function wrapper
    timer = Timer(0)
    timer.init(period=int(cfgget("timirqseq")), mode=Timer.PERIODIC, callback=secureInterruptHandlerScheduler)


def __enableInterruptSimple():
    """
    SIMPLE TIMER INTERRUPT CONFIGURATION
    """
    # LOAD DATA FOR TIMER IRQ: cfgget("timirq")
    # CACHE TASK FOR CBF
    CFG_TIMER_IRQ[0] = cfgget('timirqcbf')
    if CFG_TIMER_IRQ[0].lower() != 'n/a':
        from machine import Timer
        # INIT TIMER IRQ with callback function wrapper
        timer = Timer(0)
        timer.init(period=int(cfgget("timirqseq")), mode=Timer.PERIODIC, callback=secureInterruptHandlerSimple)
    else:
        console_write("[IRQ] TIMIRQ: isenable: {} callback: {}".format(cfgget("timirq"), cfgget('timirqcbf')))


#################################################################
#                  EVENT/EXTERNAL INTERRUPT(S)                  #
#################################################################
# trigger=Pin.IRQ_FALLING   signal HIGH to LOW
# trigger=Pin.IRQ_RISING    signal LOW to HIGH
# trigger=3                 both
#################################################################


def secureEventInterruptHandler(pin=None):
    """
    EVENT INTERRUPT CALLBACK FUNCTION WRAPPER
    """
    try:
        state = execute_LM_function_Core(CFG_EVIRQCBF.split(' '))
        if not state:
            console_write("[IRQ] EXTIRQ execute_LM_function_Core error: {}".format(CFG_EVIRQCBF))
    except Exception as e:
        console_write("[IRQ] EVENTIRQ callback: {} error: {}".format(CFG_EVIRQCBF, e))


def init_eventPIN():
    """
    EVENT INTERRUPT CONFIGURATION
    """
    global CFG_EVIRQCBF
    if cfgget('extirq') and cfgget('extirqcbf').lower() != 'n/a':
        CFG_EVIRQCBF = cfgget('extirqcbf')
        pin = get_pin_on_platform_by_key('pwm_4')
        console_write("[IRQ] EVENTIRQ ENABLED PIN: {} CBF: {}".format(pin, CFG_EVIRQCBF))
        # Init event irq with callback function wrapper
        from machine import Pin
        pin_obj = Pin(pin, Pin.IN, Pin.PULL_UP)
        pin_obj.irq(trigger=Pin.IRQ_RISING, handler=secureEventInterruptHandler)
    else:
        console_write("[IRQ] EVENTIRQ: isenable: {} callback: {}".format(cfgget('extirq'), CFG_EVIRQCBF))

#################################################################
#                         INIT MODULE                           #
#################################################################


set_emergency_buffer()
