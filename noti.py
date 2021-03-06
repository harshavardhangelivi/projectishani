import os
import pyinotify
import socket
import threading

from pyinotify import WatchManager, Notifier, ThreadedNotifier, EventsCodes, ProcessEvent

method_sem = threading.Semaphore()
static_var_sem = threading.Semaphore()
ishani='/home/harsha/ishani/'
buff_src_path=""
def sock_send(fname, floc, code):
	relative_name=floc.replace(ishani,'')
	HOST =  ''   # The remote host
	PORT = 12345# The same port as used by the server
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.connect((HOST, PORT))
	sock.send(code)
	sock.close()

	HOST =  ''   # The remote host
	PORT = 12345# The same port as used by the server
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.connect((HOST, PORT))
	sock.send(relative_name)
	sock.close()
	if (code=="CREATE" or code=="MOVED_TO" ):
		HOST =  ''   # The remote host
		PORT = 12345# The same port as used by the server
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.connect((HOST, PORT))
		fd = open(floc,'rb')
		dat = fd.read(1024)
		while dat:
			sock.send(dat)
			dat=fd.read(1024)
		sock.close()
		fd.close()
	if (code=="MVDIR" or code=="MOVE"):
		HOST =  ''   # The remote host
		PORT = 12345# The same port as used by the server
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.connect((HOST, PORT))
		global buff_src_path
		src_path = buff_src_path.replace(ishani,'')
		sock.send( src_path )
		sock.close()
		
class MyProcessing(ProcessEvent):
	move_from_flag=0
	buff_dir=False
	name=""
	pathname=""
	def __init__(self):
		move_from_flag=0
		buff_dir=False
		name=""
		pathname=""

	def process_IN_CLOSE_WRITE(self, event):
		method_sem.acquire()
		print "in CLOSE WRITE ",event.pathname
		self.buff_move_from_fun()
		sock_send(event.name, event.pathname, "CREATE")
		method_sem.release()		
	def process_IN_DELETE(self, event):
		method_sem.acquire()	
		print "in DELETE ",event.pathname
		self.buff_move_from_fun()
		if(event.name!=""):
			if(event.dir):
				sock_send(event.name, event.pathname, "RMDIR")
			else:
				sock_send(event.name, event.pathname, "DELETE")
		method_sem.release()
	def process_IN_MOVED_FROM(self, event):
		method_sem.acquire()
		static_var_sem.acquire()	
		print "in MOVED_FROM of file ",event.pathname
		self.move_from_flag=1
		self.buff_dir=event.dir
		self.name=event.name
		self.pathname=event.pathname
		global buff_src_path
		buff_src_path=event.pathname
		static_var_sem.release()
		method_sem.release()		
	def buff_move_from_fun(self):
		static_var_sem.acquire()
		if self.move_from_flag==1:
			if(self.name!=""):
				if(self.buff_dir):
					sock_send(self.name, self.pathname, "RMDIR")	
				else:
					sock_send(self.name, self.pathname, "MOVED_FROM")
			self.move_from_flag=0
			self.name=""
			self.pathname=""
			self.buff_dir=False
		static_var_sem.release()	
	def process_IN_MOVED_TO(self, event):
		print "in MOVED_TO of file ",event.pathname
		method_sem.acquire()
		static_var_sem.acquire()
		if self.move_from_flag==1:
			if(event.name!="" and self.name != ""):
				if(event.dir):
					sock_send(event.name, event.pathname, "MVDIR")	
				else:
					sock_send(event.name, event.pathname, "MOVE")
			self.move_from_flag=0;	
			self.name=""
			self.pathname=""
			self.buff_dir=False
		else:
			if(event.name!=""):
				if(event.dir):
					sock_send(event.name, event.pathname, "MKDIR")	
				else:
					sock_send(event.name, event.pathname, "MOVED_TO")
		static_var_sem.release()			
		method_sem.release()	
	def process_IN_CREATE(self, event):
		method_sem.acquire()	
		print "in CREATE of file ",event.pathname
		self.buff_move_from_fun()
		if(event.name!=""):
			if(event.dir):
				sock_send(event.name, event.pathname, "MKDIR")
			else:
				sock_send(event.name, event.pathname, "CREATE")
		method_sem.release()
	def process_default(self, event):
		#print "in default ",event.pathname
		self.buff_move_from_fun()

wm = WatchManager()			#somethng which creates a manager like thing to look wat all folders are to take care of
mask = pyinotify.ALL_EVENTS	#wat all events r to be notified
wm.add_watch('/home/harsha/ishani', mask, rec=True,auto_add=True)
notifier = ThreadedNotifier(wm, MyProcessing())	# connecting d manager and methods to call
notifier.run()	# start
