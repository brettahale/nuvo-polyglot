#!/usr/bin/env python
import sys
from .poly_interface import LOGGER, PolyInterface, Interface
from .nuvo_controller import Controller

if __name__ == "__main__":

    polyinterface = PolyInterface()
    polyglot = Interface('Nuvo Essentia Polyglot')

    try:
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
