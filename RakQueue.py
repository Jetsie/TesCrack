import threading
import RakTools as Tools
import socket

class NetworkQueue():
	def __init__(self, MTU, serverAddr):
		self.serverAddr = serverAddr

		# Create Socket
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.sock.sendto(b'', self.serverAddr) # Causes us to bind to a port to solve winerror 10022

		self.MTU = MTU
		self.all = []
		self.sent = []
		self.NACKcnt = 0

	def Add(self, byteStr: bytearray) -> list:
		hexList = Tools.BytesToHexList(byteStr)
		if hexList[0] == '0xc0':
			match hexList[3]:
				case '0x00':
					ackForMin = Tools.HexListToInt(
						Tools.RemoveTrailingPadding(Tools.GetHexListChunk(hexList, 4, 3)))
					ackForMax = Tools.HexListToInt(
						Tools.RemoveTrailingPadding(Tools.GetHexListChunk(hexList, 7, 3)))
					acks = list(range(ackForMin, ackForMax))
					for x in acks:
						if x in self.sent:
							i = self.sent.index(x)
							self.sent.pop(i)
							self.sentFull.pop(i)
				case '0x01':
					ackFor = Tools.HexListToInt(Tools.RemoveTrailingPadding(Tools.GetHexListChunk(hexList, 4, 3)))
					if ackFor in self.sent:
						i = self.sent.index(ackFor)
						self.sent.pop(i)
			return self.all

		self.all.append(byteStr)
		return self.all

	def Sent(self, id, message):
		self.sent.append(id)

	def Get(self) -> bytearray:
		if self.all != []:
			return self.all.pop()
		else:
			return None

	def Clear(self) -> list:
		self.all = []
		return []

	def WaitForResponseFromServer(self):
		while True:
			data, server = self.sock.recvfrom(self.MTU)
			if data and server == self.serverAddr: # Checks that we received a packet from the server
				return data

	def QueueLoop(self):
		while True:
			self.Add(self.WaitForResponseFromServer())

	def WaitForQueue(self):
		while True:
			res = self.Get()
			if res:
				return res

	def NACKLoop(self):
		prevPass = self.sent
		while True:
			if prevPass != self.sent:
				prevPass = self.sent
				x = self.sent[:len(self.sent) // 4]
				if len(x) == 1:
					packet = self.parent.ConstructPacket('0xa0', [self.NACKcnt, x[0], None])
					self.NACKcnt += 1
				else:
					packet = self.parent.ConstructPacket('0xa0', [self.NACKcnt, x[0], x[-1]])
					self.NACKcnt += 1
				self.parent.SendHexList(packet)

	def ActivateQueue(self):
		ql = threading.Thread(target=self.QueueLoop, daemon=True)
		ql.start()
		nl = threading.Thread(target=self.NACKLoop, daemon=True)
		nl.start()
		return ql, nl
