import pickle
import select
import socket
import threading
import helper1 as gp1
import pyopencl as cl


ip="10.0.0.5" # M1-1
# ip="10.1.0.5" # M2-1
port=5051
#data received from masterVM
#   ["op","channel","image","value","height","width"]
#data sent to masterVM
#   ["op","channel","processedimage"]
class VMThread(threading.Thread):
    def __init__(self,ip,port,vmSocket) -> None:
        super(VMThread, self).__init__()
        self.ip=ip
        self.port=port
        self.vmSocket = vmSocket
        self.vmSocket.setblocking(0)
        self.ctx = cl.create_some_context()
        self.queue = cl.CommandQueue(self.ctx)
        self.kernels = {
            'bright': """
                __kernel void bright(__global float* V) {
                    int i = get_global_id(0);
                    if (V[i] + 60.0f <= 255.0f)
                        V[i] = V[i] + 60.0f;
                    else
                        V[i] = 255.0f;
                }
            """,
            'dark': """
                __kernel void dark(__global float* V) {
                    int i = get_global_id(0);
                    if (V[i] - 60.0f >= 0.0f)
                        V[i] = V[i] - 60.0f;
                    else
                        V[i] = 0.0f;
                }
            """,
            'threshold': """
                __kernel void Thresh(__global float* V) { 
                    int i = get_global_id(0);
                    if (V[i] >= 127.0f) 
                        V[i] = 255.0f;
                    else
                        V[i] = 0.0f;
                }
            """,
            'grey': """
                __kernel void grayscale(__global float* channel, __global float* result) {
                    int i = get_global_id(0);
                    result[i] = channel[i];
                }
            """
        }
        
    def run(self)->None:
        # while True:
            try:
                receivedData=self.receive_data()
                while len(receivedData)==0:
                    continue
                print(f"received: {receivedData[0]} : {receivedData[1]} : {receivedData[3]} : ")
                operation = receivedData[0]
                channel=receivedData[1]
                imageChannel=receivedData[2]
                value=receivedData[3]
                height=receivedData[4]
                width=receivedData[5]
                processed = self.process_image(self.ctx,self.queue,operation,imageChannel,value,height,width)
                print(f"Sending response {operation} ")
                self.send_data([operation,channel,processed])
            except OSError as oErr:
                print("OSError: {0}".format(oErr))
            except Exception as e:
                print("Exception: {0}".format(e))
                # break
                
    def receive_data(self):
        timeout=5
        
        # Receive the data from the client
        data = b""
        ready_to_read, _, _ = select.select([self.vmSocket], [], [])
        if ready_to_read:
            print(f"start receiving data")
            self.vmSocket.settimeout(timeout)
            while True:
                try:
                    chunk = self.vmSocket.recv(4096)
                    if not chunk:
                        break  # No more data being received
                    data += chunk
                except socket.timeout:
                # Timeout occurred, no more data being received
                    break
        # Deserialize the received data
        array = pickle.loads(data)
        print("returning received array")
        return array

    def send_data(self, data):
        # Serialize the array
        serialized_data = pickle.dumps(data)
        print("sending serialized")
        # Send the serialized array to the server
        self.vmSocket.sendall(serialized_data)
    
    def process_image(self,ctx,queue, op, img, value, height = 0, width = 0):
        print(f"Starting processing {op}")
        if op == 'intensity':
            processedChannel = gp1.apply_intensity_kernel_R(ctx,queue, img, value, self.kernels['bright'], self.kernels['dark'])
            return processedChannel
        elif op == "to_grey":
            processedChannel = gp1.process_grey_R(ctx,queue, img, height, width, self.kernels['grey'])
            return processedChannel
        elif op == "threshold":
            processedChannel = gp1.Threshold_helper(ctx,queue, img, self.kernels['threshold'], height, width)
            return processedChannel



tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcpSocket.bind((ip, port))
print(f"Start listening on ip:{ip} , port:{port}")
tcpSocket.listen(20)

while tcpSocket:
    if not tcpSocket:
        continue
    readable,_,_ = select.select([tcpSocket],[],[])
    serverSocket,serverAddress = tcpSocket.accept()
    newThread = VMThread(serverAddress[0],serverAddress[1],serverSocket)
    print(f"Starting Thread with:{serverAddress[0]} : {serverAddress[1]} ")
    newThread.start()