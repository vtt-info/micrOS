#!/usr/bin/env python3

import sys
import socket
import os
myfolder = os.path.dirname(os.path.abspath(__file__))
sys.path.append(myfolder)
import select
import time
import nwscan
import json

class ConnectionData():
    HOST = 'localhost'
    PORT = 9008                 # TODO: Get from MicrOS config ../MicroOS/node_config.json
    MICROS_DEV_IP_DICT = {}
    DEVICE_CACHE_PATH = os.path.join(myfolder, "device_conn_cache.json")

    @staticmethod
    def filter_MicrOS_devices():
        for device in nwscan.map_wlan_devices():
            socket = None
            if '.' in device[0]:
                try:
                    print("Device Query on {} ...".format(device[0]))
                    socket = SocketDictClient(host=device[0], port=ConnectionData.PORT)
                    reply = socket.non_interactive('hello')
                    if "hello" in reply:
                        print("[MicrOS] Device: {} reply: {}".format(device[0], reply))
                        fuid = reply.split(':')[1]
                        uid = reply.split(':')[2]
                        ConnectionData.MICROS_DEV_IP_DICT[uid] = [device[0], device[1], fuid]
                    else:
                        print("[Non MicrOS] Device: {} reply: {}".format(device[0], reply))
                except Exception as e:
                    print("{} scan warning: {}".format(device, e))
                finally:
                    if socket is not None and socket.conn is not None:
                        socket.conn.close()
                    del socket
        ConnectionData.write_MicrOS_device_cache(ConnectionData.MICROS_DEV_IP_DICT)
        print("AVAILABLE MICROS DEVICES: {}".format(ConnectionData.MICROS_DEV_IP_DICT))

    @staticmethod
    def write_MicrOS_device_cache(device_dict):
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        print("Write MicrOS device cache: {}".format(cache_path))
        with open(cache_path, 'w') as f:
            json.dump(device_dict, f, indent=4)

    @staticmethod
    def read_MicrOS_device_cache():
        cache_path = ConnectionData.DEVICE_CACHE_PATH
        if os.path.isfile(cache_path):
            print("Load MicrOS device cache: {}".format(cache_path))
            with open(cache_path, 'r') as f:
                ConnectionData.MICROS_DEV_IP_DICT = json.load(f)
        else:
            print("Load MicrOS device cache not found: {}".format(cache_path))

    @staticmethod
    def select_device():
        device_choose_list = []
        print("Activate MicrOS device connection address")
        if len(list(ConnectionData.MICROS_DEV_IP_DICT.keys())) == 1:
            key = list(ConnectionData.MICROS_DEV_IP_DICT.keys())[0]
            ConnectionData.HOST = ConnectionData.MICROS_DEV_IP_DICT[key][0]
        else:
            print("[i]         FUID        IP               UID")
            for index, device in enumerate(ConnectionData.MICROS_DEV_IP_DICT.keys()):
                uid = device
                devip = ConnectionData.MICROS_DEV_IP_DICT[device][0]
                fuid = ConnectionData.MICROS_DEV_IP_DICT[device][2]
                print("[{}] Device: {} - {} - {}".format(index, fuid, devip, uid))
                device_choose_list.append(devip)
            index = int(input("Choose a device index: "))
            ConnectionData.HOST = device_choose_list[index]
            print("Device IP was set: {}".format(ConnectionData.HOST))

    @staticmethod
    def auto_execute(search=False):
        if not os.path.isfile(ConnectionData.DEVICE_CACHE_PATH):
            search = True
        if search:
            ConnectionData.filter_MicrOS_devices()
        else:
            ConnectionData.read_MicrOS_device_cache()
        ConnectionData.select_device()
        ConnectionData.read_port_from_nodeconf()
        return ConnectionData.HOST, ConnectionData.PORT

    @staticmethod
    def read_port_from_nodeconf():
        base_path = myfolder + os.sep + ".." + os.sep + "MicrOS" + os.sep
        config_path = base_path + "node_config.json"
        confighandler_path = base_path + "ConfigHandler.py"
        port_data = ""
        if os.path.isfile(config_path):
            with open(config_path) as json_file:
                port_data = json.load(json_file)['socport']
            try:
                ConnectionData.PORT = int(port_data)
            except:
                print("PORT: {} from {} invalid, must be integer".format(port_data, config_path))
        else:
            print("PORT INFORMATION COMES FROM: {}, but not exists!\n\t[HINT] Run {} script to generate default MicrOS config.".format(config_path, confighandler_path))

class SocketDictClient():

    def __init__(self, host='localhost', port=9008, bufsize=4096):
        self.is_interactive = False
        self.bufsize = bufsize
        self.host = host
        self.port = port
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.connect((host, port))

    def run_command(self, cmd, info=False):
        cmd = str.encode(cmd)
        self.conn.send(cmd)
        data = self.receive_data()
        if info:
            msglen = len(data)
            self.console("got: {}".format(data))
            self.console("received: {}".format(msglen))
        if data == '\0':
            self.console('exiting...')
            self.close_connection()
            sys.exit(0)
        return data

    def receive_data(self):
        data = ""
        data_list = []
        if select.select([self.conn], [], [], 2)[0]:
            if self.is_interactive:
                time.sleep(1)
                data = self.conn.recv(self.bufsize).decode('utf-8')
                data_list = data.split('\n')
            else:
                while data == "" or data == "slim01 $  ":
                    time.sleep(1)
                    data += self.conn.recv(self.bufsize).decode('utf-8')
                    #print("====> |{}|".format(data))
                data_list = data.split('\n')
        return data, data_list

    def interactive(self):
        self.is_interactive = True
        self.console(self.receive_data(), end='')
        while True:
            cmd = input()
            if cmd != "":
                self.console(self.run_command(cmd), end='')
                if cmd.rstrip() == "exit":
                    self.close_connection()
                    sys.exit(0)

    def non_interactive(self, cmd_list):
        self.is_interactive = False
        if isinstance(cmd_list, list):
            cmd_args = " ".join(cmd_list).strip()
        elif isinstance(cmd_list, str):
            cmd_args = cmd_list
        else:
            Exception("non_interactive function input must be list ot str!")
        ret_msg = self.console(self.run_command(cmd_args))
        self.close_connection()
        return ret_msg

    def close_connection(self):
        self.run_command("exit")
        self.conn.close()

    def console(self, msg, end='\n', server_pronpt_sep=' $'):
        if isinstance(msg, list) or isinstance(msg, tuple):
            str_msg = str(msg[0])
            list_msg = msg[1]
            if not self.is_interactive:
                input_list_buff = [k.split(server_pronpt_sep) for k in list_msg]
                filtered_msg = ""
                for line in input_list_buff:
                    if len(line) > 1:
                        for word in line[1:]:
                            filtered_msg += word + "\n"
                    else:
                        filtered_msg += ''.join(line) + "\n"
                str_msg = filtered_msg.strip()
        else:
            str_msg = msg
        print(str_msg, end=end)
        return str_msg

def main():
    try:
        socketdictclient = SocketDictClient(host=ConnectionData.HOST, port=ConnectionData.PORT)
        if len(sys.argv[1:]) == 0:
            socketdictclient.interactive()
        else:
            socketdictclient.non_interactive(sys.argv[1:])
    except KeyboardInterrupt:
        pass
    except Exception as e:
        if "Connection reset by peer" not in str(e):
            print("FAILED TO START: " + str(e))

if __name__ == "__main__":
    ConnectionData.auto_execute()
    main()
