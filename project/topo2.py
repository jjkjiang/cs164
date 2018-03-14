from mininet.topo import Topo
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

class MyFirstTopo( Topo ):
	"Topology example"
	def __init__( self ):
		"Create custom topo"
		Topo.__init__( self )
		h1 = self.addHost( 'h1' )
		h2 = self.addHost( 'h2' )
		h3 = self.addHost( 'h3' )
		h4 = self.addHost( 'h4' )
		leftSwitch = self.addSwitch( 's1' )
		#rightSwitch = self.addSwitch( 's2' )
		self.addLink( h1, leftSwitch )
		self.addLink( h2, leftSwitch )
		#self.addLink( leftSwitch, rightSwitch )
		self.addLink( leftSwitch, h3 )
		self.addLink( leftSwitch, h4 )

topos = { 'myfirsttopo': (lambda: MyFirstTopo() ) }
