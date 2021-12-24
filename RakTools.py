import RakTypes

MAGIC = ['0x00', '0xff', '0xff', '0x00', '0xfe', '0xfe', '0xfe', '0xfe', '0xfd', '0xfd', '0xfd', '0xfd', '0x12', '0x34',
		 '0x56', '0x78']

# Simple class to hold an IPv4 address
class Address:
	def __init__(self, address: tuple) -> None:
		self.address = address
		try:
			self.ip = address[0]
			self.port = address[1]
		except IndexError:
			raise Exception("Invalid address")

	def __str__(self) -> str:
		return str(self.ip) + ":" + str(self.port)

	def __tuple__(self) -> tuple:
		return self.address

def CreatePadding(size: int) -> list:
	return ['0x00'] * size


def HexToRakNetHex(hexed: str) -> str:
	if (len(hexed) % 2) == 0:
		return hexed
	else:
		return hexed[:2] + '0' + hexed[2:]


def XORHexChunkToIp(xhc: list) -> str:
	ip = ''
	for i in xhc:
		i = HexToRakNetHex(hex(int(i, 16) ^ 0xff))
		ip += str(int(i, 0)) + '.'
	return ip[:-1]


def IpToXORHexChunk(ip: str) -> list:
	splip = ip.split('.')
	e = []
	for i in splip:
		e.append(HexToRakNetHex(hex(int(hex(int(i)), 16) ^ 0xff)))
	return e


def HexListToBytes(hexList):
	return bytes([int(x, 0) for x in hexList])


def BytesToHexList(byteArr):
	return [HexToRakNetHex(hex(i)) for i in list(byteArr)]


def OrderingChannelIdToName(id):
	names = ['CHANNEL_SYSTEM', 'CHANNEL_ACTOR', 'CHANNEL_PLAYER', 'CHANNEL_OBJECT', 'CHANNEL_MASTER',
			 'CHANNEL_WORLDSTATE']
	return names[id]


def HexListToInt(hexList):
	return int(f'0x{"".join(x[2:] for x in hexList)}', 0)


def IntToHexList(num: int, tLen=None) -> list:
	hexed = Hexer(num)[2:]
	end = ['0x' + hexed[i:i + 2] for i in range(0, len(hexed), 2)]
	if tLen:
		end = ExpandHexToByteLength(end, tLen)
	return end


def Hexer(num: int) -> str:
	hexed = hex(num).replace('0x', '')
	hexed = f'0x{hexed}' if (len(hexed) % 2) == 0 else f'0x0{hexed}'
	return hexed


def HexToHexList(value):
	value = value[2:]
	if not (len(value) % 2) == 0:
		value = f'0{value}'
	return ['0x' + value[i:i + 2] for i in range(0, len(value), 2)]


def GetHexListChunk(hexList, min, length):
	chunk = []
	for i in range(min, min + length):
		chunk.append(hexList[i])
	return chunk


def RemoveTrailingPadding(hexList):
	if hexList.count('0x00') == len(hexList):
		return ['0x00']
	final = hexList
	for i in reversed(hexList):
		if i == '0x00':
			final.pop()
		else:
			return final


def GetNameOfPacketType(packetType):
	return RakTypes.types[int(packetType, 0)]


def ExpandHexToByteLength(hexed, byteCount):
	hexed = hexed[2:]
	if len(hexed) == byteCount * 2:
		return '0x' + hexed
	elif len(hexed) < byteCount * 2:
		return '0x' + ('0' * (byteCount * 2 - len(hexed))) + hexed
	else:
		raise IndexError('Value is too large to fit into the provided byte count.')


def GenerateReliabilityFlag():
	pass


def GeneratePacketSequenceNumber(num):
	return list(reversed(HexToHexList(ExpandHexToByteLength(HexToRakNetHex(hex(num)), 3))))


def GetPayloadSize(payload):
	return HexToHexList(ExpandHexToByteLength(HexToRakNetHex(hex(len(payload) * 8)), 2))


def HexListToAddrs(offset, hexList):
	return [int(hexList[offset], 0), XORHexChunkToIp(GetHexListChunk(hexList, offset + 1, 4)),
			HexListToInt(GetHexListChunk(hexList, offset + 5, 2))]


def AddrToHexList(addr):
	return ['0x04'] + IpToXORHexChunk(addr[0]) + HexToHexList(ExpandHexToByteLength(HexToRakNetHex(hex(addr[1])), 2))
