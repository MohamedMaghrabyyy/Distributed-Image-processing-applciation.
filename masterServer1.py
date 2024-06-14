import os
import pickle
import select
import socket
import threading
from CL_For_Image import CL_Image_Preprocessing
import logging
import subprocess

masterip = socket.gethostbyname(socket.gethostname())
masterport = 5090

class MainServer(threading.Thread):
    def __init__(self, ip, port, masterSocket) -> None:
        super(MainServer, self).__init__()
        self.ip = ip
        self.port = port
        self.masterSocket = masterSocket
        self.CL = CL_Image_Preprocessing()

    def run(self):
        # while True:
            try:
                receivedData = self.receive_data()
                while len(receivedData) == 0:
                    continue
                operation = receivedData[0]
                image = receivedData[1]
                print(f"[Master 1]: Received image with operation:{operation} ")
                logging.info(f"[Master 1]: Received image with operation:{operation} ")
                processed = None
                if operation == "Gray":
                    processed = self.CL.To_gray_pyopencl(image)
                elif operation == "Brighten":
                    processed = self.CL.Intensity_pyopencl(image, 1)
                elif operation == "Darken":
                    processed = self.CL.Intensity_pyopencl(image, 0)
                elif operation == "Threshold":
                    processed = self.CL.Threshhold(image)
                if processed is not None:
                    self.send_data([operation, processed])
                else:
                    raise Exception("master processed image is None")
            except OSError as oErr:
                print("OSError: {0}".format(oErr))
                logging.error("[Master 1]: OSError")
                self.upload_logs_to_azure()
            except Exception as e:
                print("Exception: {0}".format(e))
                logging.error("[Master 1]: Exception: %s")
                self.upload_logs_to_azure()
                # break
            finally:
                if self.masterSocket:
                    self.masterSocket.close()

    # run script that uplaod app.log from the master vm to the azure storage account
    def upload_logs_to_azure(self):
        try:
            subprocess.run(["./upload_log.sh"], check=True)
            print("Log file uploaded successfully to Azure Storage.")
        except subprocess.CalledProcessError as e:
            print(f"Error uploading log file to Azure Storage: {e}")

    def receive_data(self):
        timeout = 5
        data = b""
        ready_to_read, _, _ = select.select([self.masterSocket], [], [])
        if ready_to_read:
            print(f"start receiving data")
            logging.info(f"[Master 1]: start receiving data")
            self.masterSocket.settimeout(timeout)
            while True:
                try:
                    chunk = self.masterSocket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                except socket.timeout:
                    break
            self.upload_logs_to_azure()
        array = pickle.loads(data)
        print("returning received array")
        logging.info("[Master 1]: returning received array")
        return array

    def send_data(self, data):
        serialized_data = pickle.dumps(data)
        print("sending serialized")
        logging.info("[Master 1]: sending serialized")
        self.masterSocket.sendall(serialized_data)


def listenServer():
    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.bind((masterip, masterport))
    
    #config log
    logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Clear log
    with open('app.log', 'w') as log_file:
            pass
    
    print(f"Start listening on ip:{masterip}, port:{masterport}")

    logging.info(f"[Master 1]: Start listening on ip:{masterip}, port:{masterport}")

    tcpSocket.listen(20)
    while tcpSocket:
        if not tcpSocket:
            continue
        readable, _, _ = select.select([tcpSocket], [], [])
        serverSocket, serverAddress = tcpSocket.accept()
        if serverAddress[0] == "168.63.129.16":
            serverSocket.send(("done").encode())
            print(f"Health Probe")
            logging.info(f"[Master 1]: Health Probe")
            serverSocket.close()
            continue


        newThread = MainServer(serverAddress[0], serverAddress[1], serverSocket)
        
        print(f"Starting Thread with:{serverAddress[0]} : {serverAddress[1]} ")
        logging.info(f"[Master 1]: Starting Thread with:{serverAddress[0]} : {serverAddress[1]} ")
        newThread.start()

if __name__ == "__main__":
    threading.Thread(target=listenServer).start()
