"""
Module is responsible for shell like environment
dedicated to micrOS framework.
Built-in-function:
- Shell wrapper for safe InterpreterCore interface
- Configuration handling interface - state machine handling
- Help (runtime) message generation

Designed by Marcell Ban aka BxNxM
"""
#################################################################
#                           IMPORTS                             #
#################################################################
from os import listdir
from ConfigHandler import cfgget, cfgput, read_cfg_file
from InterpreterCore import execute_LM_function_Core

try:
    from gc import collect, mem_free
except:
    from simgc import collect, mem_free  # simulator mode


#################################################################
#                  SHELL Interpreter FUNCTIONS                  #
#################################################################

def shell(msg, SocketServerObj):
    try:
        return __shell(msg, SocketServerObj)
    except Exception as e:
        SocketServerObj.reply_message("[SHELL] Runtime error: {}".format(e))
        return False


def __shell(msg, SocketServerObj):
    """
    Socket server - interpreter shell
    INPUT:
        msg - str
    RETURN STATE:
        True: OK/HEALTHY
        False: ERROR/FAULTY
    """

    # PARSE RAW STR MSG
    if msg is None or len(msg.strip()) == 0:
        # No msg to work with
        return True
    msg_list = msg.strip().split()

    # CONFIGURE MODE STATE: ACCESS FOR NODE_CONFIG.JSON
    if msg_list[0].startswith('conf'):
        SocketServerObj.CONFIGURE_MODE = True
        SocketServerObj.pre_prompt = "[configure] "
        return True
    elif msg_list[0].startswith('noconf'):
        SocketServerObj.CONFIGURE_MODE = False
        SocketServerObj.pre_prompt = ""
        return True

    # HELP MSG
    if msg_list[0] == 'help':
        SocketServerObj.reply_message("[MICROS]   - commands (SocketServer built-in)")
        SocketServerObj.reply_message("   hello   - default hello msg - identify device")
        SocketServerObj.reply_message("   version - shows micrOS version")
        SocketServerObj.reply_message("   exit    - exit from shell socket prompt")
        SocketServerObj.reply_message("   reboot  - system safe reboot")
        SocketServerObj.reply_message("   webrepl - start web repl for file transfers - update")
        SocketServerObj.reply_message("[CONF] Configure mode (InterpreterShell built-in):")
        SocketServerObj.reply_message("  conf       - Enter conf mode")
        SocketServerObj.reply_message("    dump       - Dump all data")
        SocketServerObj.reply_message("    key        - Get value")
        SocketServerObj.reply_message("    key value  - Set value")
        SocketServerObj.reply_message("  noconf     - Exit conf mode")
        SocketServerObj.reply_message("[EXEC] Command mode (LMs):")
        __show_LMs_functions(SocketServerObj)
        return True

    # EXECUTE:
    # @1 Configure mode
    if SocketServerObj.CONFIGURE_MODE and len(msg_list) != 0:
        return __configure(msg_list, SocketServerObj)
    # @2 Command mode
    if len(msg_list) > 1:
        """
        INPUT MSG STRUCTURE
        1. param. - LM name, i.e. LM_commands
        2. param. - function call with parameters, i.e. a()
        """
        try:
            # Execute command via InterpreterCore
            return execute_LM_function_Core(argument_list=msg_list, SocketServerObj=SocketServerObj)
        except Exception as e:
            SocketServerObj.reply_message("[ERROR] execute_LM_function_Core internal error: {}".format(e))
            return False

#################################################################
#                     CONFIGURE MODE HANDLER                    #
#################################################################


def __configure(attributes, SocketServerObj):
    # [CONFIG] Get value
    if len(attributes) == 1:
        if attributes[0] == 'dump':
            # DUMP DATA
            for key, value in read_cfg_file().items():
                spcr = (10 - len(key))
                SocketServerObj.reply_message("  {}{}:{} {}".format(key, " " * spcr, " " * 7, value))
            return True
        # GET SINGLE PARAMETER VALUE
        SocketServerObj.reply_message(cfgget(attributes[0]))
        return True
    # [CONFIG] Set value
    if len(attributes) >= 2:
        # Deserialize params
        key = attributes[0]
        value = " ".join(attributes[1:])
        # Check irq required memory
        if 'irq' in key and attributes[1].lower() == 'true':
            isOK, avmem = __irq_mem_requirement_check(key)
            if not isOK:
                SocketServerObj.reply_message("Skip ... feature requires more memory then {} byte".format(avmem))
                return True
        # Set new parameter(s)
        try:
            output = cfgput(key, value, type_check=True)
        except Exception as e:
            SocketServerObj.reply_message("node_config write error: {}".format(e))
            output = False
        # Evaluation and reply
        issue_msg = 'Invalid key' if cfgget(key) is None else 'Failed to save'
        SocketServerObj.reply_message('Saved' if output else issue_msg)
    return True


def __irq_mem_requirement_check(key):
    collect()
    memavail = mem_free()
    if 'timirq' == key and memavail < cfgget('irqmreq'):
        return False, memavail
    if 'extirq' == key and memavail < int(cfgget('irqmreq') * 0.7):
        return False, memavail
    return True, memavail


#################################################################
#                   COMMAND MODE & LMS HANDLER                  #
#################################################################


def __show_LMs_functions(SocketServerObj):
    """
    Dump LM modules with functions - in case of [py] files
    Dump LM module with help function call - in case of [mpy] files
    """
    for lm_path in (i for i in listdir() if i.startswith('LM_') and (i.endswith('py'))):
        lm_name = lm_path.replace('LM_', '').split('.')[0]
        try:
            SocketServerObj.reply_message("   {}".format(lm_name))
            if lm_path.endswith('.mpy'):
                SocketServerObj.reply_message("   {}help".format(" " * len(lm_path.replace('LM_', '').split('.')[0])))
                continue
            with open(lm_path, 'r') as f:
                line = "micrOSisTheBest"
                while line:
                    line = f.readline()
                    if "def" in line and "def __" not in line:
                        SocketServerObj.reply_message("   {}{}"
                                                      .format(" " * len(lm_name),
                                                              line.split('(')[0].split(' ')[1]))
        except Exception as e:
            SocketServerObj.reply_message("[{}] LM PARSER WARNING: {}".format(lm_path, e))
            raise Exception("__show_LMs_functions exception {}: {}".format(lm_path, e))
