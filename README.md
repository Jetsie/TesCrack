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
<br/>Tes3mp Discord server: https://discord.gg/gESPzHuc


## A short dive into the basics.

**What's a packet?**
<br/>&emsp;A packet is a group of bytes that you recieve. Most raw packets would look something like this when you first recieve them:
```py
rawData = b'\x84\x01\x00\x00\x00\x00H\x00\x00\x00\x00\x00\x00\xf3\xfd]\x00\x00\x88\x03\x00\x00\x00\x00\x00\x00\x01\xb1\x00\x00\x00\x00\x00\xf3\xfd]'
```
> *Note: This is actually a rather small packet, for demonstrational purposes.*

&emsp;Pretty ugly stuff, I know. How can we clean this up? Well first we can cconvert it to a list of hex strings. Here's a snippet of python of what it looks like in practice:
```py
def BytesToHexList(rawData):
    listedData = []  
    h = lambda i: hex(int(i))  
    for i in rawData:
        listedData.append(h(i)[:2] + '0' + h(i)[2:] if len(h(i)) == 3 else h(i))
    return listedData
```
&emsp;As you can see by the above after we convert the raw data we store our processed packet payload in a list called `listedData`. Now lets take a look at the contents of that list.
```py
listedData = ['0x84', '0x01', '0x00', '0x00', '0x00', '0x00', '0x48', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0xf3', '0xfd', '0x5d', '0x00', '0x00', '0x88', '0x03', '0x00', '0x00', '0x00', '0x00', '0x00', '0x00', '0x01', '0xb1', '0x00', '0x00', '0x00', '0x00', '0x00', '0xf3', '0xfd', '0x5d']
```
&emsp;Wow, much better. We can actually read the individual hex bytes now. Now, onto the hard part. What in the world do these hex codes *actually* mean?
___
**No need for more code!**
<br/>&emsp;With TesCrack you don't need to interact with the low level hex as out RakNet library already handles it for you.
___
**Fast but not certain?**
<br/>&emsp;&emsp;CrabNet Protocol is UDP based, meaning that packets are not guaranteed to arrive, but have a substantial packet size reduction. This can be problematic for implementations such as games where missing packets could lead to rubber banding and/or jittery movement of other players, not to mention the nightmare of unresponsive UI. To overcome this obstacle, CrabNet has a few types of packets in its protocol to assure with a high chance of certainty that the packet arrives.
