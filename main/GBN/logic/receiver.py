import socket
import struct
import time
from collections import OrderedDict


FORMAT = "utf-8"
HOST = socket.gethostbyname(socket.gethostname())
PORT = 8085
ADDRESS = (HOST, PORT)


def receiver_program():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(ADDRESS)
    server_socket.listen()
    runningTimes = OrderedDict()
    for i in range(80):
        print(f"[LISTENING] Server is listening on {HOST}")
        conn, addr = server_socket.accept()
        print('[CONNECTING] Connected by', addr)
        start = time.time()
        data = conn.recv(1024)
        dataSize = struct.unpack("=I", data[:4])[0]
        print(dataSize)
        fieldLength = struct.unpack("=H", data[4:6])[0]
        print("\n", fieldLength, "\n")
        PacketManager(conn, addr, fieldLength, dataSize).start()
        end = time.time()
        print(f"Elapsed time : {(end - start) * 1000} ms")
        if fieldLength not in runningTimes.keys():
            runningTimes[fieldLength] = []
        runningTimes[fieldLength].append((end - start) * 1000)
        print(runningTimes)


class PacketManager:
    def __init__(self, conn, addr, fieldLength, dataSize=60):
        self.conn = conn
        self.result = ""
        self.addr = addr
        self.expectedFrame = 0
        self.received = 0
        self.maxWindowSize = 2 ** (fieldLength - 1)
        self.fieldLength = fieldLength
        self.dataSize = dataSize

    def start(self):
        while self.received < self.dataSize:
            print(len(self.result), self.dataSize)
            print(self.result)
            data = self.conn.recv(1024)
            if not data:
                break
            seqNum = struct.unpack("=I", data[:4])[0]
            print(seqNum)
            er = data[4]
            if er:
                self.sendAck(askedSeqNum=seqNum)
            else:
                self.received += self.fieldLength
                # print(f"[{self.addr}] Sequence number : {seqNum}, data :{data.decode(FORMAT)[5:-2]}")
                print(f"Sequence number : {seqNum}, data :{data.decode(FORMAT)[5:-2]}")
                self.sendAck(data)
        print(self.result)
        self.conn.close()

    def sendAck(self, data=None, askedSeqNum=None):

        if data is None:
            print("asked : ", askedSeqNum)
            if 0 < askedSeqNum < self.expectedFrame or askedSeqNum < (self.expectedFrame - self.maxWindowSize) % 2 ** self.fieldLength and askedSeqNum < self.expectedFrame:
                self.conn.sendall(struct.pack("=?", True) + struct.pack("=I", askedSeqNum+1))
                print(f"Sent ack for {askedSeqNum + 1}")
            else:
                self.conn.sendall(struct.pack("=?", False) + struct.pack("=I", askedSeqNum))
        else:
            seqNum = struct.unpack("=I", data[:4])[0]
            if seqNum == self.expectedFrame:
                self.conn.sendall(struct.pack("=?", True) + struct.pack("=I", (seqNum + 1) % (2 ** self.fieldLength)))
                print(f"Send ack {seqNum}")
                self.result += data.decode(FORMAT)[5:-2]
                self.expectedFrame += 1
            else:
                self.conn.sendall(struct.pack("=?", False) + struct.pack("=I", self.expectedFrame))
            self.expectedFrame %= 2 ** self.fieldLength




if __name__ == '__main__':
    print(f"[STARTING] Server is starting ...")
    receiver_program()
