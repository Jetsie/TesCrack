import RakNet
from config import serverAddr, serverPassword

networkEngine = RakNet.NetworkEngine(serverAddr, serverPassword)

networkEngine.run()
