import config
import json, csv, pprint, time, xlsxwriter
import numpy as np
import pandas as pd

from datetime import datetime
from binance.client import Client
from talib import RSI, PLUS_DI, DX, CCI, ADX
from binance.websockets import BinanceSocketManager
from binance.enums import *
import bb

import talib

from bb import stream

long_positions = []

short_positions = []
	

stream(config.SUSHI)
stream(config.BTC)
