from polyglot.nodeserver_api import SimpleNodeServer, PolyglotConnector
from nuvo_nodes import NuvoMain

VERSION = "0.0.1"


class NuvoNodeServer(SimpleNodeServer):
    """ Nuvo Node Server """
    zones = []


    def setup(self):
        super(SimpleNodeServer, self).setup()
        manifest = self.config.get('manifest',{})
        self.controller = NuvoMain(self, 'nuvocontroller', 'Nuvo NS', manifest, self.poly.nodeserver_config)
        self.controller.add_zones()
        self.poly.logger.info("FROM Poly ISYVER: " + self.poly.isyver)
        self.update_config()

    def poll(self):

        pass

    def long_poll(self):
        # Future stuff
        pass


def main():
    # Setup connection, node server, and nodes
    poly = PolyglotConnector()
    # Override shortpoll and longpoll timers to 5/30, once per second in unnessesary 
    nserver = NuvoNodeServer(poly, shortpoll=30, longpoll=300)
    poly.connect()
    poly.wait_for_config()
    poly.logger.info("Nuvo Interface version " + VERSION + " created. Initiating setup.")
    nserver.setup()
    poly.logger.info("Setup completed. Running Server.")
    nserver.run()

if __name__ == "__main__":
    main()
