import os
import pickle
import queue
import select
import socket
import logging
import threading

# Configure logging
log_file = "ui.log"

# setup config of the logs
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

LOAD_BALANCER_IP = "20.8.176.72"
PORT=5090
class processImage(threading.Thread):
    def __init__(self,operation,img,resQ) -> None:
        super(processImage, self).__init__()
        self.port=PORT
        self.sock = None
        self.operation=operation
        self.image=img
        self.resQ=resQ
    def run(self):
        self.process(self.operation,self.image)
        operation,im=self.receive()
        self.resQ.put([operation,im])
    def process(self,op,image):
        try:
            logger.info(f"[Host]: LBIP: {LOAD_BALANCER_IP}")
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((LOAD_BALANCER_IP, self.port))
            logger.info("[Host]: Socket connected")
            logger.info("[Host]: Start sending")
            self.send_data([op, image])
            
        except Exception as e:
            logger.error(f"Error in Thread processImage(): {e}")
    def receive(self):
        try:
            operation, result = self.receive_data()
            # print("opp:"+operation,"resss:",result)
            if operation is None or result is None:
                raise Exception("processImage Thread received None!")
            return [operation,result]
        except Exception as e:
            logger.error(f"Error in Thread processImage(): {e}")
        finally:
            if self.sock:
                self.sock.close()
    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        self.sock.sendall(serialized_data)
    def receive_data(self):
        timeout = 5
        data = b""
        ready_to_read, _, _ = select.select([self.sock], [], [])
        if ready_to_read:
            logger.info("[Host]: Start receiving data")
            self.sock.settimeout(timeout)
            while True:
                try:
                    chunk = self.sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
        array = pickle.loads(data)
        logger.info("[Host]: Returning received array")
        return array

class guiAPI:
    def __init__(self):
        self.port = PORT
        self.sock = None
        self.processThreads=[]
        self.resultQueue=queue.Queue()
        
    # def gray(self, img):
    #     try:
    #         # logger.info(f"[Host]: LBIP: {LOAD_BALANCER_IP}")
    #         # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         # self.sock.connect((LOAD_BALANCER_IP, self.port))
    #         # logger.info("[Host]: Socket connected")
    #         # self.start_process("Gray", img)
    #         # op, result = self.receive_data()
    #         pImage=processImage()
    #         op,result=pImage.process("Gray", img)
    #         return result
    #     except Exception as e:
    #         logger.error(f"Error in gray(): {e}")
    #         return None
    #     finally:
    #         if self.sock:
    #             self.sock.close()

    # def threshold(self, img):
    #     try:
    #         # logger.info(f"[Host]: LBIP: {LOAD_BALANCER_IP}")
    #         # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         # self.sock.connect((LOAD_BALANCER_IP, self.port))
    #         # logger.info("[Host]: Socket connected")
    #         # self.start_process("Threshold", img)
    #         # op, result = self.receive_data()
    #         pImage=processImage()
    #         op,result=pImage.process("Threshold", img)
    #         return result
    #     except Exception as e:
    #         logger.error(f"Error in threshold(): {e}")
    #         return None
    #     finally:
    #         if self.sock:
    #             self.sock.close()

    # def bright(self, img):
    #     try:
    #         # logger.info(f"[Host]: LBIP: {LOAD_BALANCER_IP}")
    #         # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         # self.sock.connect((LOAD_BALANCER_IP, self.port))
    #         # logger.info("[Host]: Socket connected")
    #         # self.start_process("Brighten", img)
    #         # op, result = self.receive_data()
    #         pImage=processImage()
    #         op,result=pImage.process("Brighten", img)
    #         return result
    #     except Exception as e:
    #         logger.error(f"Error in bright(): {e}")
    #         return None
    #     finally:
    #         if self.sock:
    #             self.sock.close()

    # def dark(self, img):
    #     try:
    #         # logger.info(f"[Host]: LBIP: {LOAD_BALANCER_IP}")
    #         # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         # self.sock.connect((LOAD_BALANCER_IP, self.port))
    #         # logger.info("[Host]: Socket connected")
    #         # self.start_process("Darken", img)
    #         # op, result = self.receive_data()
    #         pImage=processImage()
    #         op,result=pImage.process("Darken", img)
    #         return result
    #     except Exception as e:
    #         logger.error(f"Error in dark(): {e}")
    #         return None
    #     finally:
    #         if self.sock:
    #             self.sock.close()

    def processImage(self, inputImage, op):
        if op == "Gray":
            pImage=processImage("Gray", inputImage,self.resultQueue)
            pImage.start()
            # self.processThreads.append(pImage)
            # return self.gray(inputImage)
        elif op == "Brighten":
            pImage=processImage("Brighten", inputImage,self.resultQueue)
            pImage.start()
            # pImage=processImage()
            # op,result=pImage.process("Brighten", inputImage)
            # return result
            # return self.bright(inputImage)
        elif op == "Darken":
            pImage=processImage("Darken", inputImage,self.resultQueue)
            pImage.start()
            # pImage=processImage()
            # op,result=pImage.process("Darken", inputImage)
            # return result
            # return self.dark(inputImage)
        elif op == "Threshold":
            pImage=processImage("Threshold", inputImage,self.resultQueue)
            pImage.start()
            # pImage=processImage()
            # op,result=pImage.process("Threshold", inputImage)
            # return result
            # return self.threshold(inputImage)
        # self.processThreads.append(pImage)
            
    def receiveProcessed(self):
        # while self.resultQueue.empty():
        #     pass
        op,result=self.resultQueue.get(block=True,timeout=60)
        return result
    # def start_process(self, op, image):
    #     try:
    #         logger.info("[Host]: Start sending")
    #         self.send_data([op, image])
    #     except Exception as e:
    #         logger.error(f"Error in start_process(): {e}")


    
