## A Quick FAQ

### Q: What is TesCrack?
>**A:** TesCrack is a python recreation of the [Tes3mp](https://github.com/TES3MP/openmw-tes3mp) client, used for multiplayer Morrowind.

### Q: What versions of Tes3mp servers does TesCrack Support?
>**A:** Currently TesCrack only supports servers using version(s) 0.7.1.

### Q: What's CrabNet?
>**A:** [CrabNet](https://github.com/TES3MP/CrabNet) is a protocol which derives its primary structure from another UDP protocol, [RakNet](https://github.com/facebookarchive/RakNet).

### Q: How can I learn more about CrabNet protocol?
>**A:** When researching the protocol structure I found these to be great resources:
<br/>https://wiki.vg/Raknet_Protocol
<br/>https://c4k3.github.io/wiki.vg/Pocket_Minecraft_Protocol.html
<br/>https://github.com/TES3MP/openmw-tes3mp/blob/0.7.1/components/openmw-mp/NetworkMessages.hpp
<br/>https://github.com/TES3MP/openmw-tes3mp/tree/0.7.1/components/openmw-mp/Packets

### Q: What platform does TesCrack support? 
>**A:** As of now, TesCrack has been tested on Windows 10, but may be available to other platforms that support Python 3.10+.

### Q: Is it "hacking"?
>**A:** Since the program only operates client side, there is nothing being "hacked" about it, although server owners may still reserve the right to disallow it due to the third party nature of it.


## Quick Links
*Links are subject to change.*

> Github: https://github.com/Jetsie/TesCrack
<br/>My Discord: https://discordapp.com/users/858952348445179925

___
**No need for more code!**
<br/>&emsp;With TesCrack you don't need to interact with the low level hex as out RakNet library already handles it for you.

___
**Fast but not certain?**
<br/>&emsp;&emsp;CrabNet Protocol is UDP based, meaning that packets are not guaranteed to arrive, but have a substantial packet size reduction. This can be problematic for implementations such as games where missing packets could lead to rubber banding and/or jittery movement of other players, not to mention the nightmare of unresponsive UI. To overcome this obstacle, CrabNet has a few types of packets in its protocol to assure with a high chance of certainty that the packet arrives.
