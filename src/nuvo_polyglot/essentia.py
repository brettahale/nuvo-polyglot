from nuvo_factory import nuvo_factory
import polyinterface
from global_cache import GlobalCache
import re

LOGGER = polyinterface.LOGGER


class EssentiaController(polyinterface.Controller):
    """
    The Controller Class is the primary node from an ISY perspective. It is a Superclass
    of polyinterface.Node so all methods from polyinterface.Node are available to this
    class as well.

    Class Variables:
    self.nodes: Dictionary of nodes. Includes the Controller node. Keys are the node addresses
    self.name: String name of the node
    self.address: String Address of Node, must be less than 14 characters (ISY limitation)
    self.polyConfig: Full JSON config dictionary received from Polyglot for the controller Node
    self.added: Boolean Confirmed added to ISY as primary node
    self.config: Dictionary, this node's Config

    Class Methods (not including the Node methods):
    start(): Once the NodeServer config is received from Polyglot this method is automatically called.
    addNode(polyinterface.Node, update = False): Adds Node to self.nodes and polyglot/ISY. This is called
        for you on the controller itself. Update = True overwrites the existing Node data.
    updateNode(polyinterface.Node): Overwrites the existing node data here and on Polyglot.
    delNode(address): Deletes a Node from the self.nodes/polyglot and ISY. Address is the Node's Address
    longPoll(): Runs every longPoll seconds (set initially in the server.json or default 10 seconds)
    shortPoll(): Runs every shortPoll seconds (set initially in the server.json or default 30 seconds)
    query(): Queries and reports ALL drivers for ALL nodes to the ISY.
    getDriver('ST'): gets the current value from Polyglot for driver 'ST' returns a STRING, cast as needed
    runForever(): Easy way to run forever without maxing your CPU or doing some silly 'time.sleep' nonsense
                  this joins the underlying queue query thread and just waits for it to terminate
                  which never happens.
    """
    def __init__(self, polyglot):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.
        """
        super(EssentiaController, self).__init__(polyglot)
        self.name = 'Nuvo Essentia Controller'
        self.poly.onConfig(self.process_config)

    def start(self):
        """
        Optional.
        Polyglot v2 Interface startup done. Here is where you start your integration.
        This will run, once the NodeServer connects to Polyglot and gets it's config.
        In this example I am calling a discovery method. While this is optional,
        this is where you should start. No need to Super this method, the parent
        version does nothing.
        """
        LOGGER.info('Started Nuvo Essentia Controller NodeServer')
        if False is self.check_params():
            return False
        self.discover()
        # self.poly.add_custom_config_docs("<b>And this is some custom config data</b>")

    def shortPoll(self):
        """
        Optional.
        This runs every 10 seconds. You would probably update your nodes either here
        or longPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def longPoll(self):
        """
        Optional.
        This runs every 30 seconds. You would probably update your nodes either here
        or shortPoll. No need to Super this method the parent version does nothing.
        The timer can be overriden in the server.json.
        """
        pass

    def query(self):
        """
        Optional.
        By default a query to the control node reports the FULL driver set for ALL
        nodes back to ISY. If you override this method you will need to Super or
        issue a reportDrivers() to each node manually.
        """
        self.check_params()
        for node in self.nodes:
            self.nodes[node].reportDrivers()

    def discover(self, *args, **kwargs):
        """
        Add 6 zones
        """
        for x in range(1,7):
            name = "Zone {}".format(str(x))
            address = "z0{0}".format(str(x))
            LOGGER.info("Adding {} {} and client".format(name,address))
            gc = GlobalCache(self.host, self.port, 10)
            self.addNode(EssentiaNode(self, self.address, address, name, gc))

    def delete(self):
        """
        Example
        This is sent by Polyglot upon deletion of the NodeServer. If the process is
        co-resident and controlled by Polyglot, it will be terminiated within 5 seconds
        of receiving this message.
        """
        LOGGER.info('Oh God I\'m being deleted. Nooooooooooooooooooooooooooooooooooooooooo.')

    def stop(self):
        LOGGER.debug('NodeServer stopped.')

    def process_config(self, config):
        # this seems to get called twice for every change, why?
        # What does config represent?
        # LOGGER.info("process_config: Enter config={}".format(config))
        # LOGGER.info("process_config: Exit")
        pass

    def _all_on(self, *args):
        for node in self.nodes:
            if node != self.address:
                self.nodes[node]._on(args)

    def _all_off(self, *args):
        for node in self.nodes:
            if node != self.address:
                self.nodes[node]._off(args)

    def check_params(self):
        """
        todo: get zone assignments from here
        """
        LOGGER.info(self.polyConfig)
        if 'host' in self.polyConfig['customParams']:
            self.host = self.polyConfig['customParams']['host']
        else:
            self.host = '192.168.3.70' # default globalcache

        if 'port' in self.polyConfig['customParams']:
            self.port = self.polyConfig['customParams']['port']
        else:
            LOGGER.error('check_params: port not defined in customParams, please add it.  Using {}')
            st = False
            return st

        self.addCustomParam({'host': self.host, 'port': self.port})

    """
    Optional.
    Since the controller is the parent node in ISY, it will actual show up as a node.
    So it needs to know the drivers and what id it will use. The drivers are
    the defaults in the parent Class, so you don't need them unless you want to add to
    them. The ST and GV1 variables are for reporting status through Polyglot to ISY,
    DO NOT remove them. UOM 2 is boolean.
    The id must match the nodeDef id="controller"
    In the nodedefs.xml
    """
    id = 'nuvoe6dms'
    commands = {
        'ALLON':_all_on,
        'ALLOFF': _all_off
    }
    drivers = [{'driver': 'ST', 'value': 1, 'uom': 2}]


class EssentiaNode(polyinterface.Node):

    def __init__(self, controller, primary, address, name, client):
        """
        Optional.
        Super runs all the parent class necessities. You do NOT have
        to override the __init__ method, but if you do, you MUST call super.

        :param controller: Reference to the Controller class
        :param primary: Controller address
        :param address: This nodes address
        :param name: This nodes name
        """
        self.address = address
        self.name = name
        self.client = client
        super(EssentiaNode, self).__init__(controller, primary, address, name)

    def start(self):
        self.query()

    # percent to int
    def denormalize_volume(self, val, max=0):
        new_volume = 79 - int(round(float(val)/100*79,2))
        return max if max>0 and new_volume>max else "{:0>2}".format(new_volume)

    # int to percent
    def normalize_volume(self, val, max=0):
        new_volume = int(round((1 - float(val)/80) * 100,0))
        return max if max>0 and new_volume>max else "{:0>2}".format(new_volume)

    def parse_status(self, response):
        try:
            res = response
            if res == "#?":
                return False

            # Examples: `#Z01PWRON,SRC2,GRP0,VOL-62,POFF | #Z01PWROFF`
            # Match Groups: 0-All, 1- PWR ON/OFF, 2- SRC [1-6],GRP [0-6],VOL int, P ON/OFF
            pat = re.compile("^#Z0[0-9]PWR(ON|OFF)(?:,SRC([0-9]),GRP([0-9]),VOL[-]?([0-9MT]+),P(ON|OFF))?")
            m = re.match(pat,res)

            status = {}
            status['ST'] = 0 if m.group(1) == 'OFF' else 1

            if status['ST'] == 1:
                status['GV1'] = int(m.group(3)) #group
                status['GV2'] = 1 if m.group(4) and m.group(4) == "MT" else 0 #mute
                status['GV3'] = int(m.group(2)) #source

            if status['ST'] == 1 and status['GV2'] == 0:
                status['GV4'] = self.normalize_volume(int(m.group(4))) #volume

            return status
        except Exception as e:
            LOGGER.debug('Error parse response on Node {0} : {1}'.format(self.address,response))
            LOGGER.error(e)
            return False

    def _volume(self, *args):
        val = int(args[0]['value'])
        LOGGER.error('Attempting to set volume {0} : {1}'.format(self.address,val))
        if val:
            vol = self.denormalize_volume(val, max=80)
            return self._send_cmd("*{0}VOL{1}".format(self.address, vol))
        else:
            return False

    def _on(self, *args):
        LOGGER.info(args)
        success = self._send_cmd("*{0}ON".format(self.address))
        LOGGER.info("_on for {} is success? {}".format(self.address, success))
        return success

    def _off(self, *args):
        LOGGER.info('Recieved DOF command')
        return self._send_cmd("*{0}OFF".format(self.address))

    def _group(self, *args):
        group = args[0]['value']
        if group:
            return self._send_cmd("*{0}GRP{1}".format(self.address, str(group)))
        else:
            return False

    def _source(self, *args):
        source = args[0]['value']
        if source and int(source) in range(1,7):
            return self._send_cmd("*{0}SRC{1}".format(self.address, source))
        else:
            return False

    def _mute(self, *args):
        mute_on = self.status['GV2']
        if int(mute_on) == 1:
            return self._send_cmd("*{0}MT{1}".format(self.address, "ON"))
        elif int(mute_on) == 0:
            return self._send_cmd("*{0}MT{1}".format(self.address, "OFF"))
        else:
            return False

    def _send_cmd(self, cmd):
        response = self.client.msg(cmd.upper())
        if response:
            return self._update_status(response)
        return False

    def _update_status(self, response):
        LOGGER.info("parsing response")
        LOGGER.info(response)
        self.status = self.parse_status(response)
        if self.status:
            for driver,val in self.status.items():
                LOGGER.info("Set Driver {} : {}".format(driver, val))
                self.setDriver(driver, val, False)
            return self.reportDrivers()
        else:
            return False

    def query(self, **kwargs):
        self._send_cmd("*{0}CONSR".format(self.address))

    drivers = [
        {'driver': 'ST' , 'value': 0, 'uom': 2}, # st
        {'driver': 'GV1', 'value': 0, 'uom': 25}, # group
        {'driver': 'GV2', 'value': 0, 'uom': 2}, # mute
        {'driver': 'GV3', 'value': 0, 'uom': 25}, # src
        {'driver': 'GV4', 'value': 0, 'uom': 51} #volume
    ]
    """
    Optional.
    This is an array of dictionary items containing the variable names(drivers)
    values and uoms(units of measure) from ISY. This is how ISY knows what kind
    of variable to display. Check the UOM's in the WSDK for a complete list.
    UOM 2 is boolean so the ISY will display 'True/False'
    """
    id = 'nuvozone'
    """
    id of the node from the nodedefs.xml that is in the profile.zip. This tells
    the ISY what fields and commands this node has.
    """
    commands = {
        'SET_VOL': _volume,
        'SET_GRP': _group,
        'SET_SRC': _source,
        'SET_MT': _mute,
        'DON': _on,
        'DOF': _off
    }

    """
    This is a dictionary of commands. If ISY sends a command to the NodeServer,
    this tells it which method to call. DON calls setOn, etc.
    """

nuvo_factory.register_nodes('ESSENTIA', EssentiaController, EssentiaNode)
