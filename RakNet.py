import time
import RakTools as Tools
import RakQueue
import packets

class NetworkEngine:
	def __init__(self, serverAddr, serverPass):
		self.startTime = time.time() # Used for time calculations.
		self.serverAddr = serverAddr
		self.serverPass = Tools.HexToHexList('0x' + serverPass.encode().hex())

		self.MTU = 1497
		self.sequenceID = 0
		self.reliableID = 0
		self.timeServerUp = 0
		self.localAddr = [None, None]
		self.publicAddr = [None, None]

		self.orderingIndexes = {'CHANNEL_SYSTEM': 0, 'CHANNEL_ACTOR': 0, 'CHANNEL_PLAYER': 0,
										'CHANNEL_OBJECT': 0, 'CHANNEL_MASTER': 0, 'CHANNEL_WORLDSTATE': 0}

		self.packetManager = packets.PacketManager(self.serverAddr, self.MTU)

		self.queue = RakQueue.NetworkQueue(self.MTU, self.serverAddr)
		self.queueThread, self.ACKThread = self.queue.ActivateQueue()

		self.SecureHandshake()

	def run(self):
		while True:
			data = self.queue.WaitForQueue()
			if data:
				data = Tools.BytesToHexList(data)
				packet = packets.Packet(data, self.packetManager)
				packet.UsePacket()

	# Follows RakNet handshake protocol.
	def SecureHandshake(self):
		print(f'Commiting handshake to {self.serverAddr[0]}:{self.serverAddr[1]}...')
		try:
			self.SendHexList(self.packetManager.ConstructPacket('0x05'))
			_, _, serverId, _, self.MTU = self.packetManager.DestructPacket(Tools.BytesToHexList(self.queue.WaitForQueue()))
			
			self.SendHexList(self.packetManager.ConstructPacket('0x07'))
			_, _, serverId, self.publicAddr[0], self.publicAddr[1], self.MTU, _ = self.packetManager.DestructPacket(Tools.BytesToHexList(self.queue.WaitForQueue()))

			print(f'Handshake with {self.serverAddr[0]}:{self.serverAddr[1]} successful...')
		except BaseException as e:
			print(f'Handshake with {self.serverAddr[0]}:{self.serverAddr[1]} failed. Reason {e}. Aborting...')
			quit(-1)

		# payload = self.ConstructPacket('0x09')
		# message = self.GenerateMessage('0x40', [], payload)
		# self.sequenceID += 1
		# self.reliableID += 1

		# self.SendHexList(message)
		# self.queue.Sent(0, message)

	def GetTimeSinceStart(self):
		return int((time.time() - self.startTime) * 1000)

	def SendHexList(self, hexList):
		return self.queue.sock.sendto(Tools.HexListToBytes(hexList), self.serverAddr)