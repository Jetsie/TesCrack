import random
import time
import RakTools as tools
import threading
import socket


def ConstructPacket(id, data):
	match id:
		case '0x05':
			# data[0] is the protocol version
			return [id] + tools.MAGIC + ['0x07'] + tools.CreatePadding(1447)
		case '0x07':
			# data[0] is the MTU
			# data[1] is the client ID
			return [id] + tools.MAGIC + ['0x04'] + tools.IpToXORHexChunk(data[0][0]) + tools.IntToHexList(
				data[0][1]) + tools.IntToHexList(
				data[1]) + data[2]
		case '0x09':
			# data[0] is the client ID
			# data[1] is the time since start
			# data[2] is the RakNet password
			return [id] + data[0] + tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[1]), 8)) + ['0x00'] + data[
				2]
		case '0xa0':
			# data[0] is the nack id
			# data[1] is the min
			# data[2] is the max
			if data[2] is None:
				max = []
				flag = '0x01'
			else:
				flag = '0x00'
				max = tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[2]), 3))[::-1]
			min = tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[1]), 3))[::-1]
			return [id] + tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[0]), 2)) + [flag] + min + max
		case '0xc0':
			# data[0] is the ack id
			# data[1] is the min
			# data[2] is the max
			if data[2] is None:
				max = []
				flag = '0x01'
			else:
				flag = '0x00'
				max = tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[2]), 3))[::-1]
			min = tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[1]), 3))[::-1]
			return [id] + tools.HexToHexList(tools.ExpandHexToByteLength(hex(data[0]), 2)) + [flag] + min + max
		case _:
			raise NotImplementedError(f'Unrecognized packet: {id}')


def GenerateMessage(msgType, ids, payload):
	match msgType:
		case '0x84':
			return [msgType] + tools.GeneratePacketSequenceNumber(ids[0]) + ['0x40'] + tools.GetPayloadSize(
				payload) + tools.GeneratePacketSequenceNumber(ids[1]) + payload
		case _:
			raise NotImplementedError(f'Unrecognized packet: {id}')


def DestructPacket(hexList):
	id = hexList[0]
	match id:
		case '0x06':
			return id, tools.MAGIC, tools.GetHexListChunk(hexList, 17, 8), False if hexList[
																						25] == '0x00' else True, tools.HexListToInt(
				tools.GetHexListChunk(hexList, 26, 2))
		case '0x08':
			return id, tools.MAGIC, tools.GetHexListChunk(hexList, 17, 8), tools.XORHexChunkToIp(
				tools.GetHexListChunk(hexList, 26, 4)), tools.HexListToInt(
				tools.GetHexListChunk(hexList, 30, 2)), tools.HexListToInt(
				tools.GetHexListChunk(hexList, 32, 2)), False if hexList[33] == '0x00' else True
		case '0x10':
			getAddr = lambda offset: [int(hexList[offset], 0),
									  tools.XORHexChunkToIp(tools.GetHexListChunk(hexList, offset + 1, 4)),
									  tools.HexListToInt(tools.GetHexListChunk(hexList, offset + 5, 2))]
			clientAddr = getAddr(1)
			sysIndex = tools.HexListToInt(tools.GetHexListChunk(hexList, 8, 2))

			rakInternalAddrs = [getAddr(10), getAddr(17), getAddr(24), getAddr(31), getAddr(38), getAddr(45),
								getAddr(52), getAddr(59), getAddr(66), getAddr(73)]
			timeSinceConn = tools.HexListToInt(tools.GetHexListChunk(hexList, 80, 8))
			timeServerUp = tools.HexListToInt(tools.GetHexListChunk(hexList, 88, 8))
			return [clientAddr, sysIndex, rakInternalAddrs, timeSinceConn, timeServerUp]
		case _:
			raise NotImplementedError(f'Unrecognized packet: {id}')


class NetworkEngine:
	def __init__(self, serverAddr, serverPass):
		self.serverAddr = serverAddr
		self.serverPass = tools.HexToHexList('0x' + serverPass.encode().hex())
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		self.startTime = time.time()
		self.clientID = [tools.HexToRakNetHex(hex(random.getrandbits(8))) for _ in range(8)]
		self.MTU = 1497
		self.sequenceID = 0
		self.ourAddr = [None, None]
		self.sock.sendto(b'', self.serverAddr)
		self.queue = self.NetworkQueue(self)
		self.queueThread, self.ACKThread = self.queue.ActivateQueue()

		self.SecureHandshakeConnect()

	def run(self):
		while True:
			data = self.queue.WaitForQueue()
			if data:
				data = tools.BytesToHexList(data)
				packet = self.Packet(self, data)
				packet.UsePacket()

	def SecureHandshakeConnect(self):
		self.SendHexList(ConstructPacket('0x05', None))
		_, _, serverId, _, self.MTU = DestructPacket(tools.BytesToHexList(self.queue.WaitForQueue()))

		self.SendHexList(ConstructPacket('0x07', [self.serverAddr, self.MTU, self.clientID]))
		_, _, serverId, self.ourAddr[0], self.ourAddr[1], self.MTU, _ = DestructPacket(
			tools.BytesToHexList(self.queue.WaitForQueue()))

		payload = ConstructPacket('0x09', [self.clientID, self.GetTimeSinceStart(), self.serverPass])
		message = GenerateMessage('0x84', [0, 0], payload)
		self.SendHexList(message)
		self.queue.Sent(0, message)
		print(f'Connecting to {self.serverAddr[0]}:{self.serverAddr[1]}...')

	def GetTimeSinceStart(self):
		return int((time.time() - self.startTime) * 1000)

	def SendHexList(self, hexList):
		return self.sock.sendto(tools.HexListToBytes(hexList), self.serverAddr)

	class NetworkQueue():
		def __init__(self, parentSelf):
			self.parent = parentSelf
			self.all = []
			self.sent = []
			self.NACKcnt = 0

		def Add(self, byteStr: bytearray) -> list:
			hexList = tools.BytesToHexList(byteStr)
			if hexList[0] == '0xc0':
				match hexList[3]:
					case '0x00':
						ackForMin = tools.HexListToInt(
							tools.RemoveTrailingPadding(tools.GetHexListChunk(hexList, 4, 3)))
						ackForMax = tools.HexListToInt(
							tools.RemoveTrailingPadding(tools.GetHexListChunk(hexList, 7, 3)))
						acks = list(range(ackForMin, ackForMax))
						for x in acks:
							if x in self.sent:
								i = self.sent.index(x)
								self.sent.pop(i)
								self.sentFull.pop(i)
					case '0x01':
						ackFor = tools.HexListToInt(tools.RemoveTrailingPadding(tools.GetHexListChunk(hexList, 4, 3)))
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
				data, server = self.parent.sock.recvfrom(self.parent.MTU)
				if data and server == self.parent.serverAddr:
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
						packet = ConstructPacket('0xa0', [self.NACKcnt, x[0], None])
						self.NACKcnt += 1
					else:
						packet = ConstructPacket('0xa0', [self.NACKcnt, x[0], x[-1]])
						self.NACKcnt += 1
					self.parent.SendHexList(packet)

		def ActivateQueue(self):
			ql = threading.Thread(target=self.QueueLoop, daemon=True)
			ql.start()
			nl = threading.Thread(target=self.NACKLoop, daemon=True)
			nl.start()
			return ql, nl

	class Packet():
		def __init__(self, parent, data):
			self.parent = parent
			self.data = data
			self.messageId = ''
			self.id = ''
			self.header = []
			self.payload = []
			self.messageFlags = ''
			self.SeparateHeader()

			self.destructedPayload = DestructPacket(self.payload)

		def UsePacket(self):
			match self.id:
				case '0x10':
					print('Connection Accepted!')
					self.parent.SendHexList(ConstructPacket('0xc0', [1, self.header[2], None]))
				case _:
					raise NotImplementedError(f'Unrecognized packet: {self.id}')

		def SeparateHeader(self):
			self.messageId = self.data[0]
			match self.messageId:
				case '0x84':
					self.messageFlags = self.data[4]
					payloadLength = tools.HexListToInt(tools.GetHexListChunk(self.data, 5, 2))
					self.header = [self.messageId, self.messageFlags, tools.HexListToInt(
						tools.RemoveTrailingPadding(tools.GetHexListChunk(self.data, 1, 3))), payloadLength]
					match self.messageFlags:
						case '0x60':
							self.header.append(
								tools.HexListToInt(tools.RemoveTrailingPadding(tools.GetHexListChunk(self.data, 7, 3))))
							self.header.append(
								tools.HexListToInt(
									tools.RemoveTrailingPadding(tools.GetHexListChunk(self.data, 10, 3))))
							self.header.append(tools.OrderingChannelIdToName(int(self.data[13], 0)))
							self.payload = tools.GetHexListChunk(self.data, 14, len(self.data) - 14)
							self.id = self.payload[0]
						case '0x40':
							pass
						case '0x00':
							pass
				case _:
					raise NotImplementedError(f'Unrecognized packet: {id}')
