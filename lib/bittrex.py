## Python3 Interface to Bittrex API

import requests, json
import os, time, calendar
from pathlib import Path
import numpy as np
import phone
import cutils as cu

s = requests.Session()

# Set of Functions to Retrieve, Modify, and Store Bittrex Data

def get_active_markets(base_currency ='btc', base_currencies = ('BTC','ETH','USDT')):
	base_currency = base_currency.upper()
	if base_currency not in base_currencies:
		raise Exception('Bittrex presently only supports {}, {}, and {} base currencies'.format(*base_currencies))
	bittrex_markets = s.get('https://bittrex.com/api/v1.1/public/getmarkets').json()
	if bittrex_markets['success']:
		bittrex_markets = bittrex_markets['result']
	else:
		raise Exception('Bittrex API request for traded markets not successful.')
	return [market['MarketName'].lower() for market in bittrex_markets if market['BaseCurrency']== base_currency and market['IsActive']]

def get_tick_history(market, tick_interval):
	tick_history = s.get('https://bittrex.com/Api/v2.0/pub/market/GetTicks?marketName={}&tickInterval={}'.format(market,tick_interval)).json()
	if tick_history['success']:
		tick_history = tick_history['result']
	else:
		raise Exception('Bittrex API request for {}({}) tick history not successful.'.format(market,tick_interval))
	for tick in tick_history:
		tick['UT'] = to_unix_time(tick['T'])
	return tick_history	
			
def get_tick_histories(markets, tick_intervals):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	for market in markets:
		for tick_interval in tick_intervals:
				tick_history = get_tick_history(market, tick_interval)
				filename = '{}({})'.format(market,tick_interval)
				directory = os.path.join(str(Path.home()),'bittrex','ticks')
				cu.save(tick_history,filename,directory)

def append_tick_history(market, tick_interval,save=True):
	directory = os.path.join(str(Path.home()),'bittrex','ticks')
	filename = '{}({})'.format(market,tick_interval) 
	last_tick_history = get_tick_history(market, tick_interval)
	try:
		past_tick_history = cu.load(filename,directory)
		i = past_tick_history.index(last_tick_history[0])
		appended_tick_history = past_tick_history[:i] + last_tick_history
	except FileNotFoundError:
		appended_tick_history = last_tick_history
	if save:
		cu.save(appended_tick_history,filename,directory)
	else:
		return appended_tick_history
			
		 
def append_tick_histories(markets, tick_intervals, save=True):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	tick_histories = {tick_interval:{market: append_tick_history(market,tick_interval,save) for market in markets} for tick_interval in tick_intervals}
	if not save:
		return tick_histories
		
def to_unix_time(bittrex_time):
	time_tuple = time.strptime(bittrex_time,'%Y-%m-%dT%H:%M:%S')
	unix_time =  float(calendar.timegm(time_tuple))
	return unix_time

def to_bittrex_time(unix_time):
	time_tuple = time.gmtime(unix_time)
	bittrex_time = time.strftime('%Y-%m-%dT%H:%M:%S', time_tuple)
	return bittrex_time
	

# Set of Functions to Retrieve, Modify, Generate, and Store Bittrex Data

def get_market_history(market):
	retrieval_time = time.time()
	market_history = s.get('https://bittrex.com/api/v1.1/public/getmarkethistory?market={}'.format(market)).json()
	if market_history['success']:
		market_history = market_history['result'][::-1]
	else:
		raise Exception('Bittrex API request for {} market history not successful.'.format(market))
	for order in market_history:
		ut = to_unix_time(order['TimeStamp'][:19]) + float('0'+order['TimeStamp'][19:])
		order['UT'] = ut
	return (retrieval_time, market_history)
	
def generate_ticks(market_history, seconds):
	ticks = []
	collated_orders = collate_orders(market_history, seconds)
	for unix_time, orders in collated_orders:
		tick = {}
#		tick['T'] = to_bittrex_time(unix_time)
		tick['UT'] = unix_time
		if orders:
#			tick['O'] = orders[0]['Price']
			tick['C'] = orders[-1]['Price']
#			tick['H'] = max([order['Price'] for order in orders])
#			tick['L'] = min([order['Price'] for order in orders])
#			tick['BV'] = sum([order['Total'] for order in orders])
#			tick['V'] = sum([order['Quantity'] for order in orders])
			tick['BV'] = sum([order['Total'] for order in orders if order['OrderType'] == 'BUY'])
#			tick['SV'] = sum([order['Total'] for order in orders if order['OrderType'] == 'SELL'])
		else:
#			tick['O'] = ticks[-1]['C']
			tick['C'] = ticks[-1]['C']
#			tick['H'] = ticks[-1]['C']
#			tick['L'] = ticks[-1]['C']
#			tick['BV'] = 0
#			tick['V'] = 0
			tick['BV'] = 0
#			tick['SV'] = 0
		ticks.append(tick)
	return ticks
			  
def collate_orders(market_history, s):
	retrieval_time, market_history = market_history
	btime = lambda ut, s: ut - ut %s
	bin_time_first = btime(market_history[0]['UT'], s)
	bin_time_last = btime(retrieval_time, s) - s
	bin_times = np.arange(bin_time_first, bin_time_last + s, s)
	collated_orders = [(bin_time,[order for order in market_history if btime(order['UT'], s) == bin_time]) for bin_time in bin_times]
	return collated_orders
	
def report_volume_anomalies(th, notify, i=-1, threshold={1:10,2:10,3:10,5:10,15:10,30:20}, pthreshold=1.2, show=True, beep=True, call=False, text=False, flag=True):
	anomaly = False
	for market in th.keys():
		timestamp, delta = detect_volume_anomaly(th[market],i,threshold,pthreshold)
		va = [(n,v,p) for n,v,p in delta if v and p]
		if va:
			anomaly = True
			ts = time.strftime('%H:%M:%S',timestamp)
			if show:
				if not flag:
					print('')
					flag = True		
			for n,v,p in va:
				if show:
					print(ts.ljust(13),market.ljust(10),str(n).ljust(9),'{:.2g}'.format(v).ljust(9),'{:.3g}'.format(p).ljust(9))
				if notify[market][n]:
					notify[market][n]=False
					if beep:
						d = 0.25; f = 440
						os.system('play --no-show-progress --null --channels 1 synth {} sine {}'.format(d,f))
					if call:
						phone.call('me')
					if text:
						n = len(va)
						txt_msg = 'TIME:{}, MARKET:{}, PERIOD:{}, BUY:{:.2f}, PRICE:{:.2g}, VD:{}'.format(ts,market,n,buy,price,int(vd))
						phone.text('me',txt_msg)
	return anomaly
	

def detect_volume_anomaly(tick_history,i=-1,threshold={1:10,2:10,3:10,5:10,15:10,30:20}, pthreshold=1.2):
	timestamp = time.localtime(tick_history[i]['UT'])
	c1 = lambda x: x if x > 1 else 1
	c2 = lambda x,n: 0 if x < threshold[n] else x
	c3 = lambda x: 0 if x < pthreshold else x
	bv2 = lambda n: sum([tick['BV'] for tick in tick_history[i:i-n:-1]])
	bv1 = lambda n: sum([tick['BV'] for tick in tick_history[i-n:i-2*n:-1]])
	pd = lambda n: tick_history[i]['C'] / tick_history[i-n]['C']
	N = sorted(threshold.keys())
	Nticks = len(tick_history)
	delta = [(n, c2(c1(bv2(n))/c1(bv1(n)), n), c3(pd(n))) for n in N if Nticks >= 2*n]
	delta = (timestamp, delta)
	return delta



############functions to be reviewed for their utility

def get_market_histories(markets,save=True):
	if type(markets) is str: markets = [markets]
	if save:
		for market in markets:
			market_history = get_market_history(market)
			filename = market
			directory = os.path.join(str(Path.home()),'bittrex','trades')
			cu.save(tick_history,filename,directory)
	else:
		return {market: get_market_history(market) for market in markets}
	
def update_market_history(market):
	directory = os.path.join(str(Path.home()),'bittrex','trades')
	filename = market
	retrieval_time, market_history = cu.load(filename,directory)
	retrieval_time_update, market_history_update = get_market_history(market)
	try:
		index = market_history.index(market_history_update[0])
	except ValueError:
		index = len(market_history)
	updated_market_history = market_history[:index] + market_history_update
	updated_market_history = (retrieval_time_update, updated_market_history)
	cu.save(updated_market_history,filename,directory)

def update_market_histories(market_histories):
	update = lambda i,m,u: m[:i] + u
	market_history_update = {market: get_market_history(market) for market in market_history.keys()}
	try:
		index = market_history.index(market_history_update[0])
	except ValueError:
		index = len(market_history)
	updated_market_history = market_history[:index] + market_history_update
	cu.save(updated_market_history,filename,directory)
	
#arcane	
def get_latest_tick(market, tick_interval):
	latest_tick = s.get('https://bittrex.com/Api/v2.0/pub/market/GetLatestTick?marketName={}&tickInterval={}'.format(market,tick_interval)).json()
	if latest_tick['success']:
		latest_tick = latest_tick['result'][0]
	else:
		raise Exception('Bittrex API request for latest {}({}) tick not successful.'.format(market,tick_interval))
	latest_tick['UT'] = to_unix_time(latest_tick['T'])
	return latest_tick
