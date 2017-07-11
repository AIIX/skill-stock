# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

import time
import xml.etree.ElementTree as ET

import requests
from adapt.intent import IntentBuilder
from os.path import dirname

from mycroft.skills.core import MycroftSkill
from mycroft.util.log import getLogger
from mycroft.messagebus.message import Message

__author__ = 'eward'
logger = getLogger(__name__)


class StockSkill(MycroftSkill):
    def __init__(self):
        super(StockSkill, self).__init__(name="StockSkill")
        self.html_index = dirname(__file__) + '/html/'
        self.js_index = dirname(__file__) + '/html/chartscript.js'

    def initialize(self):
        stock_price_intent = IntentBuilder("StockPriceIntent") \
            .require("StockPriceKeyword").require("Company").build()
        self.register_intent(stock_price_intent,
                             self.handle_stock_price_intent)

    def handle_stock_price_intent(self, message):
        company = message.data.get("Company")
        try:
            response = self.find_and_query(company)
            self.emitter.once("recognizer_loop:audio_output_start",
                              self.enclosure.mouth_text(
                                  response['symbol'] + ": " + response[
                                      'price']))                                  
            self.enclosure.deactivate_mouth_events()
            self.speak_dialog("stock.price", data=response)
            websymb = response['symbol']
            self.__genwebview(websymb)
            self.enclosure.ws.emit(Message("data", {'desktop': {'url': self.html_index + 'stockresult.html'}}))
            time.sleep(12)
            self.enclosure.activate_mouth_events()
            self.enclosure.mouth_reset()

        except:
            self.speak_dialog("not.found", data={'company': company})

    def _query(self, url, param_name, query):
        payload = {param_name: query}
        response = requests.get(url, params=payload)
        return ET.fromstring(response.content)

    def find_and_query(self, query):
        root = self._query(
            "http://dev.markitondemand.com/MODApis/Api/v2/Lookup?",
            'input', query)
        root = self._query(
            "http://dev.markitondemand.com/Api/v2/Quote?", 'symbol',
            root.iter('Symbol').next().text)
        return {'symbol': root.iter('Symbol').next().text,
                'company': root.iter('Name').next().text,
                'price': root.iter('LastPrice').next().text}
    
    def __genwebview(self, symbol):
        smbl = symbol
        sjs = self.js_index
        fname = self.html_index + 'stockresult.html'
        f = open(fname,'w')
        wrapper = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>Untitled Document</title>
<link rel="stylesheet" href="https://code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css">
<script src="https://code.jquery.com/jquery-1.10.2.js"></script>
<script src="https://code.jquery.com/ui/1.11.4/jquery-ui.js"></script>  
<script src="https://code.highcharts.com/stock/highstock.js"></script>
<script src="https://code.highcharts.com/stock/modules/exporting.js"></script>
<script src="{0}"></script>
<script>
new Markit.TimeseriesService("{1}", 365);
</script>
</head>
<body>
<div id="chartDemoContainer" style="min-width: 300px; height: 250px; margin: 0 auto"></div>
</body>
</html>""".format(sjs, smbl)
        f.write(wrapper)
        f.close()
    
    def stop(self):
        pass


def create_skill():
    return StockSkill()
