from polyglot.nodeserver_api import Node
from gc_client import GlobalCache
import re

def myint(myval):
    return str(int(round(float(myval))))

def parse_status(response):

    if response == "#?":
        return False

    #         #Z01PWRON,SRC2,GRP0,VOL-62,POFF | #Z01PWROFF
    pat = re.compile("^#Z0[0-9]PWR(ON|OFF)(,SRC([0-9]),GRP([0-9]),VOL[-]?([0-9MT]+),P(ON|OFF))?")
    m = pat.match(response)
    status = {}
    if m.group(5) and m.group(5) == "MT":
        status['GV2'] = 1
    elif m.group(5):
        status['GV4'] = normalize_volume(m.group(5))
        status['GV2'] = 0

    if m.group(1) == 'ON':
        status['ST'] = 1
        status['GV1'] = m.group(4)
        status['GV3'] = m.group(3)
    else:
        status['ST'] = 0

    return status


# percent to int
def denormalize_volume(val, max=0):
    new_volume = 79 - int(round(float(val)/100*79,2))
    return max if max>0 and new_volume>max else "{:0>2}".format(new_volume)


# int to percent
def normalize_volume(val, max=0):
    new_volume = int(round((1 - float(val)/80) * 100,0))
    return max if max>0 and new_volume>max else "{:0>2}".format(new_volume)


class NuvoMain(Node):

    node_def_id = 'NVCTRL'

    def __init__(self, parent, address, name, manifest=None, config_data=None):
        self.parent = parent
        self.address = address
        self.name = name
        self.logger = parent.logger
        self.config_data = config_data
        self.logger.info(" ************ CONFIG *************")
        self.logger.info(config_data)
        super(NuvoMain, self).__init__(parent, address, name, True, manifest=None)
        self.client = GlobalCache(self.config_data['nuvo']['host'], self.config_data['nuvo']['port'], self.logger)
        status = self.client.msg("*VER")
        self.logger.info("current status: {0}".format(status))

    def add_zones(self, **kwargs):
        config_data = self.config_data
        manifest = self.parent.config.get('manifest', {})
        self.logger.info("Received Discover command from ISY.")
        for x in range(1, 7):
            if (x in config_data['zones']) and ('name' in config_data['zones'][x]):
                zname = config_data['zones'][x]['name']
            else:
                zname = 'Zone {0}'.format(str(x))

            zprefix = "Z0{0}".format(str(x))
            address = "nuvozone{0}".format(str(x))
            lnode = self.parent.get_node(address)
            if not lnode:
                self.logger.info("Adding zone: {0} {1} {2}".format(zname, zprefix, address))
                current_node = NuvoZone(self.parent, self.parent.get_node(self.address), address, zname, zprefix, self.client, manifest)
                self.parent.zones.append(current_node)
                current_node.query()
            self.logger.info("Updating config: {0} {1} {2}")


            self.parent.update_config()

        return True

    def _all_off(self):
        return self.client.msg("*ALLOFF")


    def query(self, **kwargs):
        pass

    _drivers = {}
    _commands = {'ALLOFF': _all_off}




class NuvoZone(Node):

    node_def_id = 'NVZONE'
    status = {}

    def __init__(self, parent, primary, address, zone_name, zone_prefix, client, manifest=None):
        self.parent = parent
        self.client = client
        self.zone_name = zone_name
        self.zone_prefix = zone_prefix
        self.volume = 0
        self.address = address
        super(NuvoZone, self).__init__(parent, address, zone_name, primary, manifest)


    def _update_status(self, response):
        self.logger.info("parsing response")
        self.logger.info(response)
        self.status = parse_status(response)
        if self.status:
            for driver, val in self.status.iteritems():
                self.set_driver(driver, val, False)
            return self.report_driver()
        else:
            return False

    def query(self, **kwargs):
        return self._send_cmd("*{0}CONSR".format(self.zone_prefix))

    def _send_cmd(self, cmd):
        response = self.client.msg(cmd)
        if response:
            return self._update_status(response)
        return False

    def _volume(self, **kwargs):
        val = kwargs.get('value')
        self.logger.error('Attempting to set volume {0} : {1}'.format(self.zone_prefix,str(val)))
        if val:
            vol = denormalize_volume(val, 80)
            return self._send_cmd("*{0}VOL{1}".format(self.zone_prefix, vol))
        else:
            return False

    def _on(self, **kwargs):
        return self._send_cmd("*{0}ON".format(self.zone_prefix))

    def _off(self, **kwargs):
        return self._send_cmd("*{0}OFF".format(self.zone_prefix))

    def _group(self, **kwargs):
        group = kwargs.get('value')
        if group:
            return self._send_cmd("*{0}GRP{1}".format(self.zone_prefix, str(group)))
        else:
            return False

    def _source(self, **kwargs):
        source = kwargs.get('value')
        if source:
            return self._send_cmd("*{0}SRC{1}".format(self.zone_prefix, myint(source)))
        else:
            return False

    def _mute(self, **kwargs):
        mute_on = self.status['GV2']
        if int(mute_on) == 1:
            return self._send_cmd("*{0}MT{1}".format(self.zone_prefix, "ON"))
        elif int(mute_on) == 0:
            return self._send_cmd("*{0}MT{1}".format(self.zone_prefix, "OFF"))
        else:
            return False

    _drivers = {
        'ST': [0, 25, str], # st
        'GV1': [0, 25, int], # group
        'GV2': [0, 25, str], # mute
        'GV3': [0, 25, myint], # src
        'GV4': [0, 51, int] #volume
                }
    _commands = {
        'SET_VOL': _volume,
        'SET_GRP': _group,
        'SET_SRC': _source,
        'SET_MT': _mute,
        'DON': _on,
        'DOF': _off
    }

