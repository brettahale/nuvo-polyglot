#!/usr/bin/env python
import os
import sys
import polyinterface
from nuvo_factory import nuvo_factory
import concerto
import essentia
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv('./.env')

    device_type = os.getenv('NUVO_DEVICE').lower()
    polyglot = polyinterface.Interface('Nuvo {} Polyglot'.format(device_type))
    Controller = nuvo_factory.get_controller(device_type.upper())

    try:
        polyglot.start()
        control = Controller(polyglot)
        control.runForever()
    except (KeyboardInterrupt, SystemExit):
        polyglot.stop()
        sys.exit(0)
