from .poly_interface import Node, LOGGER
import re

class ZoneNode(Node):

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
        super(ZoneNode, self).__init__(controller, primary, address, name)

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

        res = response.decode()
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
