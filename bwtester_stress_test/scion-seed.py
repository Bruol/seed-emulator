

from seedemu.compiler import Docker, Graphviz
from seedemu.core import Emulator, Binding, Filter
from seedemu.layers import ScionBase, ScionRouting, ScionIsd, Scion, Ospf
from seedemu.layers.Scion import LinkType as ScLinkType
from seedemu.services import ScionBwtestService
import os

BASE_LOG_DIR = "/home/ubuntu/bt/bwtester_stress_test/logs"


# Initialize
emu = Emulator()
base = ScionBase()
routing = ScionRouting()
scion_isd = ScionIsd()
scion = Scion()
bwtest = ScionBwtestService()
ospf = Ospf()


def createBWServer(asn):
    _as = base.getAutonomousSystem(asn)
    # Create a host running the bandwidth test server
    _as.createHost('bwtest').joinNetwork('net0', address=f'10.{asn}.0.30')
    bwtest.install('bwtest'+str(asn)).setPort(40002) # Setting the port is optional (40002 is the default)
    emu.addBinding(Binding('bwtest'+str(asn), filter=Filter(nodeName='bwtest', asn=asn)))



def createLogFolders():
    ases = base.getAsns()
    # save ASNs
    with open("./asns","w") as f:
        f.write(",".join(str(x) for x in ases))
        f.close()
    # create log folders
    os.mkdir(BASE_LOG_DIR)
    for asn in ases:
        os.mkdir(BASE_LOG_DIR + "/" + str(asn))
        node = base.getNodeByAsnAndName(asn=asn,name="bwtest")
        node.addSharedFolder("/var/log",BASE_LOG_DIR + "/" + str(asn))





# Create ISDs
base.createIsolationDomain(2)
base.createIsolationDomain(1)


# Ases 

# AS-110
as110 = base.createAutonomousSystem(110)
scion_isd.addIsdAs(1,110,is_core=True)
as110.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as110.createControlService('cs_1').joinNetwork('net0')
as_110_br1 = as110.createRouter('br1').joinNetwork('net0')

as_110_br1.crossConnect(120,'br1','10.3.0.2/29',latency=0,bandwidth=0,packetDrop=0)

as_110_br2 = as110.createRouter('br2').joinNetwork('net0')

as_110_br2.crossConnect(130,'br1','10.3.0.10/29',latency=0,bandwidth=0,packetDrop=0)

as_110_br3 = as110.createRouter('br3').joinNetwork('net0')

as_110_br3.crossConnect(210,'br1','10.3.0.18/29',latency=0,bandwidth=0,packetDrop=0)

createBWServer(110)



# AS-120
as120 = base.createAutonomousSystem(120)
scion_isd.addIsdAs(1,120,is_core=True)
as120.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as120.createControlService('cs_1').joinNetwork('net0')
as_120_br1 = as120.createRouter('br1').joinNetwork('net0')

as_120_br1.crossConnect(110,'br1','10.3.0.3/29',latency=0,bandwidth=0,packetDrop=0)


as_120_br1.crossConnect(130,'br2','10.3.0.26/29',latency=0,bandwidth=0,packetDrop=0)

as_120_br2 = as120.createRouter('br2').joinNetwork('net0')

as_120_br2.crossConnect(220,'br1','10.3.0.34/29',latency=0,bandwidth=0,packetDrop=0,MTU=1350)


as_120_br2.crossConnect(220,'br2','10.3.0.42/29',latency=0,bandwidth=0,packetDrop=0,MTU=1400)


as_120_br2.crossConnect(121,'br1','10.3.0.50/29',latency=0,bandwidth=0,packetDrop=0)

as_120_br3 = as120.createRouter('br3').joinNetwork('net0')

as_120_br3.crossConnect(111,'br1','10.3.0.58/29',latency=0,bandwidth=0,packetDrop=0)

createBWServer(120)



# AS-130
as130 = base.createAutonomousSystem(130)
scion_isd.addIsdAs(1,130,is_core=True)
as130.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as130.createControlService('cs_1').joinNetwork('net0')
as_130_br1 = as130.createRouter('br1').joinNetwork('net0')

as_130_br1.crossConnect(110,'br2','10.3.0.11/29',latency=0,bandwidth=0,packetDrop=0)


as_130_br1.crossConnect(131,'br1','10.3.0.66/29',latency=0,bandwidth=0,packetDrop=0)


as_130_br1.crossConnect(112,'br1','10.3.0.82/29',latency=0,bandwidth=0,packetDrop=0)

as_130_br2 = as130.createRouter('br2').joinNetwork('net0')

as_130_br2.crossConnect(120,'br1','10.3.0.27/29',latency=0,bandwidth=0,packetDrop=0)


as_130_br2.crossConnect(111,'br2','10.3.0.74/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(130)



# AS-111
as111 = base.createAutonomousSystem(111)
scion_isd.addIsdAs(1,111,is_core=False)
scion_isd.setCertIssuer((1,111),issuer=110)
as111.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as111.createControlService('cs_1').joinNetwork('net0')
as_111_br1 = as111.createRouter('br1').joinNetwork('net0')

as_111_br1.crossConnect(120,'br3','10.3.0.59/29',latency=0,bandwidth=0,packetDrop=0)


as_111_br1.crossConnect(211,'br1','10.3.0.98/29',latency=0,bandwidth=0,packetDrop=0)

as_111_br2 = as111.createRouter('br2').joinNetwork('net0')

as_111_br2.crossConnect(130,'br2','10.3.0.75/29',latency=0,bandwidth=0,packetDrop=0)


as_111_br2.crossConnect(112,'br2','10.3.0.114/29',latency=0,bandwidth=0,packetDrop=0)

as_111_br3 = as111.createRouter('br3').joinNetwork('net0')

as_111_br3.crossConnect(121,'br2','10.3.0.90/29',latency=0,bandwidth=0,packetDrop=0)


as_111_br3.crossConnect(211,'br1','10.3.0.106/29',latency=0,bandwidth=0,packetDrop=0)

createBWServer(111)


# AS-112
as112 = base.createAutonomousSystem(112)
scion_isd.addIsdAs(1,112,is_core=False)
scion_isd.setCertIssuer((1,112),issuer=110)
as112.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0).setMtu(1450)
as112.createControlService('cs_1').joinNetwork('net0')
as_112_br1 = as112.createRouter('br1').joinNetwork('net0')

as_112_br1.crossConnect(130,'br1','10.3.0.83/29',latency=0,bandwidth=0,packetDrop=0)

as_112_br2 = as112.createRouter('br2').joinNetwork('net0')

as_112_br2.crossConnect(111,'br2','10.3.0.115/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(112)



# AS-121
as121 = base.createAutonomousSystem(121)
scion_isd.addIsdAs(1,121,is_core=False)
scion_isd.setCertIssuer((1,121),issuer=120)
as121.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as121.createControlService('cs_1').joinNetwork('net0')
as_121_br1 = as121.createRouter('br1').joinNetwork('net0')

as_121_br1.crossConnect(120,'br2','10.3.0.51/29',latency=0,bandwidth=0,packetDrop=0)

as_121_br2 = as121.createRouter('br2').joinNetwork('net0')

as_121_br2.crossConnect(111,'br3','10.3.0.91/29',latency=0,bandwidth=0,packetDrop=0)

as_121_br3 = as121.createRouter('br3').joinNetwork('net0')

as_121_br3.crossConnect(131,'br2','10.3.0.122/29',latency=0,bandwidth=0,packetDrop=0)

as_121_br4 = as121.createRouter('br4').joinNetwork('net0')

as_121_br4.crossConnect(122,'br1','10.3.0.130/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(121)



# AS-122
as122 = base.createAutonomousSystem(122)
scion_isd.addIsdAs(1,122,is_core=False)
scion_isd.setCertIssuer((1,122),issuer=120)
as122.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as122.createControlService('cs_1').joinNetwork('net0')
as_122_br1 = as122.createRouter('br1').joinNetwork('net0')

as_122_br1.crossConnect(121,'br4','10.3.0.131/29',latency=0,bandwidth=0,packetDrop=0)

as_122_br2 = as122.createRouter('br2').joinNetwork('net0')

as_122_br2.crossConnect(133,'br1','10.3.0.138/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(122)



# AS-131
as131 = base.createAutonomousSystem(131)
scion_isd.addIsdAs(1,131,is_core=False)
scion_isd.setCertIssuer((1,131),issuer=130)
as131.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as131.createControlService('cs_1').joinNetwork('net0')
as_131_br1 = as131.createRouter('br1').joinNetwork('net0')

as_131_br1.crossConnect(130,'br1','10.3.0.67/29',latency=0,bandwidth=0,packetDrop=0)

as_131_br2 = as131.createRouter('br2').joinNetwork('net0')

as_131_br2.crossConnect(121,'br3','10.3.0.123/29',latency=0,bandwidth=0,packetDrop=0)

as_131_br3 = as131.createRouter('br3').joinNetwork('net0')

as_131_br3.crossConnect(132,'br1','10.3.0.146/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(131)



# AS-132
as132 = base.createAutonomousSystem(132)
scion_isd.addIsdAs(1,132,is_core=False)
scion_isd.setCertIssuer((1,132),issuer=130)
as132.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as132.createControlService('cs_1').joinNetwork('net0')
as_132_br1 = as132.createRouter('br1').joinNetwork('net0')

as_132_br1.crossConnect(131,'br3','10.3.0.147/29',latency=0,bandwidth=0,packetDrop=0)

as_132_br2 = as132.createRouter('br2').joinNetwork('net0')

as_132_br2.crossConnect(133,'br2','10.3.0.154/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(132)



# AS-133
as133 = base.createAutonomousSystem(133)
scion_isd.addIsdAs(1,133,is_core=False)
scion_isd.setCertIssuer((1,133),issuer=130)
as133.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as133.createControlService('cs_1').joinNetwork('net0')
as_133_br1 = as133.createRouter('br1').joinNetwork('net0')

as_133_br1.crossConnect(122,'br2','10.3.0.139/29',latency=0,bandwidth=0,packetDrop=0)

as_133_br2 = as133.createRouter('br2').joinNetwork('net0')

as_133_br2.crossConnect(132,'br2','10.3.0.155/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(133)



# AS-210
as210 = base.createAutonomousSystem(210)
scion_isd.addIsdAs(2,210,is_core=True)
as210.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0).setMtu(1280)
as210.createControlService('cs_1').joinNetwork('net0')
as_210_br1 = as210.createRouter('br1').joinNetwork('net0')

as_210_br1.crossConnect(110,'br3','10.3.0.19/29',latency=0,bandwidth=0,packetDrop=0)

as_210_br2 = as210.createRouter('br2').joinNetwork('net0')

as_210_br2.crossConnect(220,'br3','10.3.0.162/29',latency=0,bandwidth=0,packetDrop=0)

as_210_br3 = as210.createRouter('br3').joinNetwork('net0')

as_210_br3.crossConnect(211,'br1','10.3.0.170/29',latency=0,bandwidth=0,packetDrop=0)

as_210_br4 = as210.createRouter('br4').joinNetwork('net0')

as_210_br4.crossConnect(211,'br1','10.3.0.178/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(210)



# AS-220
as220 = base.createAutonomousSystem(220)
scion_isd.addIsdAs(2,220,is_core=True)
as220.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as220.createControlService('cs_1').joinNetwork('net0')
as_220_br1 = as220.createRouter('br1').joinNetwork('net0')

as_220_br1.crossConnect(120,'br2','10.3.0.35/29',latency=0,bandwidth=0,packetDrop=0,MTU=1350)

as_220_br2 = as220.createRouter('br2').joinNetwork('net0')

as_220_br2.crossConnect(120,'br2','10.3.0.43/29',latency=0,bandwidth=0,packetDrop=0,MTU=1400)

as_220_br3 = as220.createRouter('br3').joinNetwork('net0')

as_220_br3.crossConnect(210,'br2','10.3.0.163/29',latency=0,bandwidth=0,packetDrop=0)

as_220_br4 = as220.createRouter('br4').joinNetwork('net0')

as_220_br4.crossConnect(221,'br1','10.3.0.186/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(220)



# AS-211
as211 = base.createAutonomousSystem(211)
scion_isd.addIsdAs(2,211,is_core=False)
scion_isd.setCertIssuer((2,211),issuer=210)
as211.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as211.createControlService('cs_1').joinNetwork('net0')
as_211_br1 = as211.createRouter('br1').joinNetwork('net0')

as_211_br1.crossConnect(111,'br1','10.3.0.99/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(111,'br3','10.3.0.107/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(210,'br3','10.3.0.171/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(210,'br4','10.3.0.179/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(221,'br2','10.3.0.194/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(212,'br1','10.3.0.202/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(212,'br2','10.3.0.210/29',latency=0,bandwidth=0,packetDrop=0)


as_211_br1.crossConnect(222,'br1','10.3.0.218/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(211)



# AS-212
as212 = base.createAutonomousSystem(212)
scion_isd.addIsdAs(2,212,is_core=False)
scion_isd.setCertIssuer((2,212),issuer=210)
as212.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as212.createControlService('cs_1').joinNetwork('net0')
as_212_br1 = as212.createRouter('br1').joinNetwork('net0')

as_212_br1.crossConnect(211,'br1','10.3.0.203/29',latency=0,bandwidth=0,packetDrop=0)

as_212_br2 = as212.createRouter('br2').joinNetwork('net0')

as_212_br2.crossConnect(211,'br1','10.3.0.211/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(212)



# AS-221
as221 = base.createAutonomousSystem(221)
scion_isd.addIsdAs(2,221,is_core=False)
scion_isd.setCertIssuer((2,221),issuer=220)
as221.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as221.createControlService('cs_1').joinNetwork('net0')
as_221_br1 = as221.createRouter('br1').joinNetwork('net0')

as_221_br1.crossConnect(220,'br4','10.3.0.187/29',latency=0,bandwidth=0,packetDrop=0)

as_221_br2 = as221.createRouter('br2').joinNetwork('net0')

as_221_br2.crossConnect(211,'br1','10.3.0.195/29',latency=0,bandwidth=0,packetDrop=0)

as_221_br3 = as221.createRouter('br3').joinNetwork('net0')

as_221_br3.crossConnect(222,'br2','10.3.0.226/29',latency=0,bandwidth=0,packetDrop=0)


createBWServer(221)



# AS-222
as222 = base.createAutonomousSystem(222)
scion_isd.addIsdAs(2,222,is_core=False)
scion_isd.setCertIssuer((2,222),issuer=220)
as222.createNetwork('net0').setDefaultLinkProperties(latency=0, bandwidth=0, packetDrop=0)
as222.createControlService('cs_1').joinNetwork('net0')
as_222_br1 = as222.createRouter('br1').joinNetwork('net0')

as_222_br1.crossConnect(211,'br1','10.3.0.219/29',latency=0,bandwidth=0,packetDrop=0)

as_222_br2 = as222.createRouter('br2').joinNetwork('net0')

as_222_br2.crossConnect(221,'br3','10.3.0.227/29',latency=0,bandwidth=0,packetDrop=0)

createBWServer(222)





# Inter-AS routing

scion.addXcLink((1,110),(1,120),ScLinkType.Core,a_router='br1',b_router='br1')


scion.addXcLink((1,110),(1,130),ScLinkType.Core,a_router='br2',b_router='br1')


scion.addXcLink((1,110),(2,210),ScLinkType.Core,a_router='br3',b_router='br1')


scion.addXcLink((1,120),(1,130),ScLinkType.Core,a_router='br1',b_router='br2')


scion.addXcLink((1,120),(2,220),ScLinkType.Core,a_router='br2',b_router='br1')


scion.addXcLink((1,120),(2,220),ScLinkType.Core,a_router='br2',b_router='br2')


scion.addXcLink((1,120),(1,121),ScLinkType.Transit,a_router='br2',b_router='br1')


scion.addXcLink((1,120),(1,111),ScLinkType.Transit,a_router='br3',b_router='br1')


scion.addXcLink((1,130),(1,131),ScLinkType.Transit,a_router='br1',b_router='br1')


scion.addXcLink((1,130),(1,111),ScLinkType.Transit,a_router='br2',b_router='br2')


scion.addXcLink((1,130),(1,112),ScLinkType.Transit,a_router='br1',b_router='br1')


scion.addXcLink((1,111),(1,121),ScLinkType.Peer,a_router='br3',b_router='br2')


scion.addXcLink((1,111),(2,211),ScLinkType.Peer,a_router='br1',b_router='br1')


scion.addXcLink((1,111),(2,211),ScLinkType.Peer,a_router='br3',b_router='br1')


scion.addXcLink((1,111),(1,112),ScLinkType.Transit,a_router='br2',b_router='br2')


scion.addXcLink((1,121),(1,131),ScLinkType.Peer,a_router='br3',b_router='br2')


scion.addXcLink((1,121),(1,122),ScLinkType.Transit,a_router='br4',b_router='br1')


scion.addXcLink((1,122),(1,133),ScLinkType.Peer,a_router='br2',b_router='br1')


scion.addXcLink((1,131),(1,132),ScLinkType.Transit,a_router='br3',b_router='br1')


scion.addXcLink((1,132),(1,133),ScLinkType.Transit,a_router='br2',b_router='br2')


scion.addXcLink((2,210),(2,220),ScLinkType.Core,a_router='br2',b_router='br3')


scion.addXcLink((2,210),(2,211),ScLinkType.Transit,a_router='br3',b_router='br1')


scion.addXcLink((2,210),(2,211),ScLinkType.Transit,a_router='br4',b_router='br1')


scion.addXcLink((2,220),(2,221),ScLinkType.Transit,a_router='br4',b_router='br1')


scion.addXcLink((2,211),(2,221),ScLinkType.Peer,a_router='br1',b_router='br2')


scion.addXcLink((2,211),(2,212),ScLinkType.Transit,a_router='br1',b_router='br1')


scion.addXcLink((2,211),(2,212),ScLinkType.Transit,a_router='br1',b_router='br2')


scion.addXcLink((2,211),(2,222),ScLinkType.Transit,a_router='br1',b_router='br1')


scion.addXcLink((2,221),(2,222),ScLinkType.Transit,a_router='br3',b_router='br2')


# Rendering
emu.addLayer(base)
emu.addLayer(routing)
emu.addLayer(scion_isd)
emu.addLayer(scion)
emu.addLayer(bwtest)
emu.addLayer(ospf)

createLogFolders()

emu.render()

# Compilation
emu.compile(Docker(internetMapEnabled=True), './seed-compiled', override=True)
emu.compile(Graphviz(), './viz', override=True)
