#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mock import patch, MagicMock
from unittest import TestCase
import pytest
from nuvo_polyglot.nuvo_node import ZoneNode

__author__ = "brett.hale"
__copyright__ = "brett.hale"
__license__ = "mit"


class TestMethods(TestCase):

    def setUp(self):
        self.node = ZoneNode('controller', 'primary', 'address', 'name', 'client')

    def test_parse_results_on(self):
        status = self.node.parse_status(b'#Z01PWRON,SRC2,GRP0,VOL-62,POFF')
        assert status['ST'] == 1
        assert status['GV1'] == 0
        assert status['GV2'] == 0
        assert status['GV3'] ==2
        assert status['GV4'] == self.node.normalize_volume(62)

    def test_parse_results_off(self):
        status = self.node.parse_status(b'#Z01PWROFF')
        self.assertRaises(KeyError, lambda: status['GV1'])

    def test_parse_results_comm_error(self):
        assert self.node.parse_status(b'#?') is False
