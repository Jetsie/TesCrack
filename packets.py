import socket
import RakTools as Tools
import random
import RakTypes as Types

class Packet():
    def __init__(self, data, packetManager):
        self.packetManager = packetManager
        self.data = data
        self.messageId = ''
        self.id = ''
        self.header = []
        self.payloadLength = 0
        self.payload = []
        self.timeSinceStart = 0
        self.channel = ''
        self.orderingIndex = 0
        self.reliableID = 0
        self.sequenceID = 0
        self.messageFlags = ''
        self.SeparateHeader()

        self.destructedPayload = self.packetManager.DestructPacket(self.payload)

    def UsePacket(self):
        match self.id:
            case '0x10':
                print('Connection Accepted!')
                self.parent.localAddr = (socket.gethostbyname(socket.gethostname()), self.destructedPayload[0][2])
                self.timeSinceStart = self.destructedPayload[4]
                self.parent.timeServerUp = self.timeSinceStart

                message = self.GenerateMessage('0x60', [0], self.ConstructPacket('0x13'))
                message += self.GenerateMessage('0x00', None, self.ConstructPacket('0x00'),
                                                        useSeqNum=False)
                self.parent.SendHexList(message)
                self.parent.queue.Sent(self.parent.sequenceID, message)

                self.parent.SendHexList(self.parent.ConstructPacket('0xc0', [1, self.sequenceID, None]))
            case _:
                raise NotImplementedError(f'Unrecognized packet: {id}')

    def SeparateHeader(self):
        self.messageId = self.data[0]
        match self.messageId:
            case '0x84':
                self.messageFlags = self.data[4]
                self.payloadLength = Tools.HexListToInt(Tools.GetHexListChunk(self.data, 5, 2))
                self.sequenceID = Tools.HexListToInt(
                    Tools.RemoveTrailingPadding(Tools.GetHexListChunk(self.data, 1, 3)))
                self.header = [self.messageId, self.messageFlags, self.sequenceID, self.payloadLength]
                match self.messageFlags:
                    case '0x60':
                        self.reliableID = Tools.HexListToInt(
                            Tools.RemoveTrailingPadding(Tools.GetHexListChunk(self.data, 7, 3)))
                        self.header.append(self.reliableID)

                        self.orderingIndex = Tools.HexListToInt(
                            Tools.RemoveTrailingPadding(Tools.GetHexListChunk(self.data, 10, 3)))
                        self.header.append(self.orderingIndex)

                        self.channel = Tools.OrderingChannelIdToName(int(self.data[13], 0))
                        self.header.append(self.channel)

                        self.payload = Tools.GetHexListChunk(self.data, 14, len(self.data) - 14)
                        self.id = self.payload[0]
                    case '0x40':
                        pass
                    case '0x00':
                        pass

            case _:
                raise NotImplementedError(f'Unrecognized packet: {id}')

class PacketManager():
    def __init__(self, serverAddr, MTU) -> None:
        self.serverAddr = serverAddr
        self.clientID = [Tools.HexToRakNetHex(hex(random.getrandbits(8))) for _ in range(8)]
        self.MTU = MTU
    
    def GenerateMessage(self, reliability, extra, payload, useSeqNum=True):
            match reliability:
                case '0x40':
                    return [id] + (Tools.GeneratePacketSequenceNumber(self.sequenceID) if useSeqNum else []) + [
                        reliability] + Tools.GetPayloadSize(
                        payload) + Tools.GeneratePacketSequenceNumber(self.reliableID) + payload
                case '0x60':
                    return [id] + (Tools.GeneratePacketSequenceNumber(self.sequenceID) if useSeqNum else []) + [
                        reliability] + Tools.GetPayloadSize(
                        payload) + Tools.GeneratePacketSequenceNumber(self.reliableID) + Tools.GeneratePacketSequenceNumber(
                        self.orderingIndexes[Tools.OrderingChannelIdToName(extra[0])]) + Tools.HexToHexList(
                        Tools.HexToRakNetHex(
                            hex(extra[0]))) + payload
                case '0x00':
                    return [id] + (Tools.GeneratePacketSequenceNumber(self.sequenceID) if useSeqNum else []) + [
                        reliability] + Tools.GetPayloadSize(
                        payload) + payload

                case _:
                    raise NotImplementedError(f'Unrecognized packet: {id}')

    def ConstructPacket(self, id, data=None):
        match id:
            case '0x00':
                return [id] + Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(self.GetTimeSinceStart()), 8))

            case '0x05':
                return [id] + Tools.MAGIC + ['0x07'] + Tools.CreatePadding(1447)

            case '0x07':
                return [id] + Tools.MAGIC + Tools.AddrToHexList(self.serverAddr) + Tools.IntToHexList(self.MTU) + self.clientID

            case '0x09':
                return [id] + self.clientID + Tools.HexToHexList(
                    Tools.ExpandHexToByteLength(hex(self.GetTimeSinceStart()), 8)) + ['0x00'] + self.serverPass

            case '0x13':
                blank = Tools.AddrToHexList(('0.0.0.0', 0))
                return [id] + Tools.AddrToHexList(self.serverAddr) + Tools.AddrToHexList(
                    self.localAddr) + (blank * 9) + Tools.HexToHexList(
                    Tools.ExpandHexToByteLength(hex(self.timeServerUp), 8)) + Tools.HexToHexList(
                    Tools.ExpandHexToByteLength(hex(self.GetTimeSinceStart()), 8))

            case '0xa0':
                # data[0] is the nack id
                # data[1] is the min
                # data[2] is the max
                if data[2] is None:
                    max = []
                    flag = '0x01'
                else:
                    flag = '0x00'
                    max = Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[2]), 3))[::-1]
                min = Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[1]), 3))[::-1]
                return [id] + Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[0]), 2)) + [flag] + min + max

            case '0xc0':
                # data[0] is the ack id
                # data[1] is the min
                # data[2] is the max
                if data[2] is None:
                    max = []
                    flag = '0x01'
                else:
                    flag = '0x00'
                    max = Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[2]), 3))[::-1]
                min = Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[1]), 3))[::-1]
                return [id] + Tools.HexToHexList(Tools.ExpandHexToByteLength(hex(data[0]), 2)) + [flag] + min + max

            case _:
                raise NotImplementedError(f'Unrecognized packet: {id}')

    def DestructPacket(self, hexList):
        id = hexList[0]
        match id:
            case '0x06':
                return id, Tools.MAGIC, Tools.GetHexListChunk(hexList, 17, 8), False if hexList[
                                                                                            25] == '0x00' else True, Tools.HexListToInt(
                    Tools.GetHexListChunk(hexList, 26, 2))
            case '0x08':
                return id, Tools.MAGIC, Tools.GetHexListChunk(hexList, 17, 8), Tools.XORHexChunkToIp(
                    Tools.GetHexListChunk(hexList, 26, 4)), Tools.HexListToInt(
                    Tools.GetHexListChunk(hexList, 30, 2)), Tools.HexListToInt(
                    Tools.GetHexListChunk(hexList, 32, 2)), False if hexList[33] == '0x00' else True
            case '0x10':
                clientAddr = Tools.HexListToAddrs(1, hexList)
                sysIndex = Tools.HexListToInt(Tools.GetHexListChunk(hexList, 8, 2))

                rakInternalAddrs = [Tools.HexListToAddrs(10, hexList),
                                    Tools.HexListToAddrs(17, hexList),
                                    Tools.HexListToAddrs(24, hexList),
                                    Tools.HexListToAddrs(31, hexList),
                                    Tools.HexListToAddrs(38, hexList),
                                    Tools.HexListToAddrs(45, hexList),
                                    Tools.HexListToAddrs(52, hexList),
                                    Tools.HexListToAddrs(59, hexList),
                                    Tools.HexListToAddrs(66, hexList),
                                    Tools.HexListToAddrs(73, hexList)]
                timeSinceConn = Tools.HexListToInt(Tools.GetHexListChunk(hexList, 80, 8))
                timeServerUp = Tools.HexListToInt(Tools.GetHexListChunk(hexList, 88, 8))
                return [clientAddr, sysIndex, rakInternalAddrs, timeSinceConn, timeServerUp]
            case _:
                raise NotImplementedError(f'Unrecognized packet: {id}')
