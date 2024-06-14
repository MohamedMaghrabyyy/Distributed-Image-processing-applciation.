import pickle
import queue
import select
import socket
import threading
import time
import logging
import cv2

# Set up logging
logging.basicConfig(filename='app.log', filemode='w', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# data sent by masterVM
# ["op","channel","image","value","height","width"]
# data received from vms
# ["op","channel","processedimage"]
VMS_IP_Port = {
    "vm1": ["10.0.0.5", 5051],
    "vm2": ["10.0.0.6", 5052],
    "vm3": ["10.0.0.7", 5053]
}
# VMS_IP_Port = {
#     "vm1": ["10.1.0.5", 5051],
#     "vm2": ["10.1.0.6", 5052],
#     "vm3": ["10.1.0.7", 5053]
# }
class masterT(threading.Thread):
    def __init__(self,name, r, g, b, value,resQ, height=0, width=0) -> None:
        super(masterT, self).__init__()
        self.name=name
        self.r=r
        self.g=g
        self.b=b
        self.value=value
        self.height=height
        self.width=width
        self.vm1 = None
        self.vm2 = None
        self.vm3 = None
        self.resQ=resQ
    
    def run(self):
        pr=self.MasterTask(self.name, self.r, self.g, self.b, self.value, self.height, self.width)
        self.resQ.put(pr)
    def MasterTask(self,name, r, g, b, value, height=0, width=0):
        result_queue = queue.Queue(3)
        
        if name == "intensity-grey":
            self.vm2 = VM(VMS_IP_Port["vm2"][0], VMS_IP_Port["vm2"][1],result_queue,name,"ig",r,value,height,width)
            self.vm2.start()
            while result_queue.empty():
                continue
            item = result_queue.get()
            return item[2]
            # processed = self.vm2.process(name, "ig", r, value, height, width)
            # return processed
        if name == "threshold":
            self.vm1 = VM(VMS_IP_Port["vm1"][0], VMS_IP_Port["vm1"][1],result_queue,name,"th",r,value,height,width)
            self.vm1.start()
            while result_queue.empty():
                continue
            item = result_queue.get()
            return item[2]
            # processed = self.vm1.process(name, "th", r, value, height, width)
            # return processed
        else:
            self.vm1 = VM(VMS_IP_Port["vm1"][0], VMS_IP_Port["vm1"][1],result_queue,name,"r",r,value,height,width)
            self.vm1.start()
            self.vm2 = VM(VMS_IP_Port["vm2"][0], VMS_IP_Port["vm2"][1],result_queue,name,"g",g,value,height,width)
            self.vm2.start()
            self.vm3 = VM(VMS_IP_Port["vm3"][0], VMS_IP_Port["vm3"][1],result_queue,name,"b",b,value,height,width)
            self.vm3.start()
            # self.vm1.start_process(name, "r", r, value, height, width)
            # self.vm2.start_process(name, "b", b, value, height, width)
            # self.vm3.start_process(name, "g", g, value, height, width)
            # time.sleep(0.01)
            # vm1_receive_thread = threading.Thread(target=self.vm1.receive_process, args=(result_queue,))
            # vm1_receive_thread.start()
            # vm2_receive_thread = threading.Thread(target=self.vm2.receive_process, args=(result_queue,))
            # vm2_receive_thread.start()
            # vm3_receive_thread = threading.Thread(target=self.vm3.receive_process, args=(result_queue,))
            # vm3_receive_thread.start()
            while not result_queue.full():
                continue
            adjusted_R = adjusted_G = adjusted_B = None
            for i in range(3):
                item = result_queue.get()
                if item[1] == "r":
                    adjusted_R = item[2]
                elif item[1] == "b":
                    adjusted_B = item[2]
                elif item[1] == "g":
                    adjusted_G = item[2]
            processed = cv2.merge((adjusted_R, adjusted_G, adjusted_B))
        return processed


class VM(threading.Thread):
    def __init__(self, ip, port,resQ,op, channel, image, value, height, width):
        super(VM, self).__init__()
        self.ip = ip
        self.port = port
        self.vmSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.vmSocket.connect((self.ip, self.port))
        self.resQ=resQ
        self.op=op
        self.channel=channel
        self.image=image
        self.value=value
        self.height=height
        self.width=width

    def run(self):
        try:
            self.start_process(self.op, self.channel, self.image, self.value, self.height, self.width)
            self.receive_process(self.resQ)
        finally:
            if self.vmSocket:
                self.vmSocket.close()
    def process(self, op, channel, image, value, height, width):
        try:
            logging.info("[ServerMaster]: Start sending")
            self.send_data([op, channel, image, value, height, width])
            logging.info("[ServerMaster]: Start receive process")
            received_data = self.receive_data()
            operation = received_data[0]
            ch = received_data[1]
            processed_image_channel = received_data[2]
            return processed_image_channel

        except OSError as oErr:
            logging.error(f"[ServerMaster]: OSError: {oErr}")
        except Exception as e:
            logging.error(f"[ServerMaster]: Exception: {e}")

    def start_process(self, op, channel, image, value, height, width):
        try:
            logging.info("[ServerMaster]: Start sending")
            self.send_data([op, channel, image, value, height, width])

        except OSError as oErr:
            logging.error(f"[ServerMaster]: OSError: {oErr}")
        except Exception as e:
            logging.error(f"[ServerMaster]: Exception: {e}")

    def receive_process(self, result_queue):
        try:
            logging.info("[ServerMaster]: Start receive process")
            received_data = self.receive_data()
            operation = received_data[0]
            ch = received_data[1]
            processed_image_channel = received_data[2]

            result_queue.put([operation, ch, processed_image_channel])

        except OSError as oErr:
            logging.error(f"[ServerMaster]: OSError: {oErr}")
        except Exception as e:
            logging.error(f"[ServerMaster]: Exception: {e}")

    def close_vm(self):
        self.send_data(["EXIT"])
        received_data = self.receive_data()
        self.vmSocket.close()

    def receive_data(self):
        timeout = 5
        data = b""
        ready_to_read, _, _ = select.select([self.vmSocket], [], [])
        if ready_to_read:
            logging.info("[ServerMaster]: Start receiving data")
            self.vmSocket.settimeout(timeout)
            while True:
                try:
                    chunk = self.vmSocket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
        array = pickle.loads(data)
        logging.info("[ServerMaster]: Returning received array")
        return array

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        self.vmSocket.sendall(serialized_data)


# vm1 = VM(VMS_IP_Port["vm1"][0], VMS_IP_Port["vm1"][1])
# vm2 = VM(VMS_IP_Port["vm2"][0], VMS_IP_Port["vm2"][1])
# vm3 = VM(VMS_IP_Port["vm3"][0], VMS_IP_Port["vm3"][1])
