## DA for DATA ANALYSIS
import json, os, itertools
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
mpl.style.use('ggplot')

# SET OF FUNCTIONS TO BETTER LOAD AND VISUALIZE DATASETS

def load(market,tick_interval):
	filename = '{}({})'.format(market,tick_interval)
	directory = os.path.join(str(Path.home()),'bittrex','ticks')
	filepath = os.path.join(directory,filename)
	with open(filepath) as f:
		dataset = json.load(f)
	add_volume_indicator(dataset)
	df = pd.DataFrame(dataset)
	df.index = df['UT']
	df.drop(['T','V','UT'],axis=1,inplace=True)
	return df

def add_volume_indicator(tick_history, n=1, threshold = 10):
	for i in range(len(tick_history)):
		tick = tick_history[i]
		if i >= n:
			previous_tick = tick_history[i-n]
			if tick['BV'] < 1:
				tick['BV'] = 1
			if previous_tick['BV'] < 1:
				previous_tick['BV'] = 1
			vi = tick['BV']/previous_tick['BV']
			if vi < threshold:
				vi = 0
			tick['VI'] = vi
		else:
			tick['VI'] = 0
			
def plot(markets, tick_intervals):
	if type(markets) is str: markets = (markets,)
	for market in markets:
		market_dfs = []
		for tick_interval in tick_intervals:
			market_dfs.append(tick_interval)
			
def plot1(markets, tick_intervals):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	for market in markets:
		for tick_interval in tick_intervals:
			market_df = load(market,tick_interval)
			fig = plt.figure()
			ax = fig.gca()
			ax.plot(market_df.index, market_df['C'], color='cyan', label='C')
			plt.ylabel('Closing price (BTC)')
			plt.legend(loc='upper left')
			ax2 = ax.twinx()
			ax2.plot(market_df.index, market_df['VI'], color='magenta', label='VI')
			plt.ylabel('Volume indicator')
			plt.legend(loc='upper right')
			plt.title('{}, {}'.format(market, tick_interval))
	plt.show()

def plot2(markets, tick_intervals):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	for market in markets:
		for tick_interval in tick_intervals:
			market_df = load(market,tick_interval)
			fig = plt.figure()
			ax = fig.gca()
			plot_peaks(market_df,'C',ax)
			plt.ylabel('Closing price (BTC)')
#			plt.legend(loc='upper left')
			ax2 = ax.twinx()
			ax2.plot(market_df.index, market_df['VI'], color='magenta', label='VI')
			plt.ylabel('Volume indicator')
			plt.legend(loc='upper right')
			plt.title('{}, {}'.format(market, tick_interval))
	plt.show()

def plot3(markets, tick_intervals):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	for market in markets:
		for tick_interval in tick_intervals:
			market_df = load(market,tick_interval)
#	3 subplots sharing same x axis
			f, (ax1,ax2,ax3) = plt.subplots(3, sharex=True)
#	title of plot
			ax1.set_title('{}, {}'.format(market, tick_interval))
#	plot C peaks on first subplot
			plot_peaks(market_df,'C',ax1); plt.ylabel('Closing price (BTC)')
#	plot VI on second subplot
			ax2.plot(market_df.index, market_df['VI'], color='magenta'); plt.ylabel('Volume indicators')
#	plot BV peaks on third subplot
			plot_peaks(market_df,'BV',ax3); plt.ylabel('Base volume (BTC)')
#	adjust spacing between subplots
			f.subplots_adjust(hspace=0)
			plt.setp([a.get_xticklabels() for a in [ax1,ax2]],visible=False)
	plt.show()

def plot4(markets,tick_intervals):
	if type(markets) is str: markets = [markets]
	if type(tick_intervals) is str: tick_intervals = [tick_intervals]
	for market in markets:
		for tick_interval in tick_intervals:
			market_df = load(market,tick_interval)
#	3 subplots sharing same x axis
			f, ax = plt.subplots()
#	title of plot
			ax.set_title('{}, {}'.format(market, tick_interval))
#	plot C peaks on subplot
			plot_peaks(market_df,'C',ax); plt.ylabel('Closing price (BTC)')
#	plot and fill BV peaks on same subplot
			ax2 = ax.twinx()
			fill_peaks(market_df,'BV',ax2); plt.ylabel('Base volume (BTC)')
#	plot VI on same subplot
			ax3 = ax.twinx()
			ax3.plot(market_df.index, market_df['VI'], color='magenta'); plt.ylabel('Volume indicators')
	plt.show()

def plot0(df):
	fig = plt.figure()
	ax = fig.gca()
#	plot volume peaks
	plot_peaks(df,'BV')	
#	plot closing value
	cs = 10**int(np.log10(max(df['BV'])/max(df['C'])))
	ax.plot(df.index,cs*df['C'],label='C: scale={:.0e}'.format(cs),color='blue')
#	plot volume indicators
	ax2 = ax.twinx()
	ax2.plot(df.index,df['VI'],label='VI',color='red')
	plt.legend(loc='best')
	plt.show()


#plots the constituent peaks of a dataframe column sequentially
def plot_peaks(df, column_name, ax):
	peaks = get_peaks(list(df[column_name]))
	for peak in peaks:
		m, li, ri, area, points = peak
		ax.plot(df.index[li:ri+1], points) #label='max={}, area={}'.format(m,area))

def fill_peaks(df, column_name, ax):
	colors = mpl.rcParams['axes.prop_cycle']
	color_dict = itertools.cycle(colors)
	peaks = get_peaks(list(df[column_name]))
	for peak in peaks:
		m, li, ri, area, points = peak
		ax.fill_between(df.index[li:ri+1], 0, points, alpha=0.5, color=next(color_dict)['color']) #label='max={}, area={}'.format(m,area))


#separates any dataset in list format into constituent peaks
def get_peaks(datapoints, c=0.05):
	peaks=[]
	f=min(datapoints)		#sets floor to the absolute minimum of dataset
	while True:
		mi, m = max_index(datapoints)	#determines absolute maximum of dataset and its index
		if m < f:	#until there are no more maxima
			break
		#determines the left boundary of peak to be less than floor plus c percent of difference between max and floor
		for li, l in enumerate(datapoints[mi::-1]):
			if l < f + c*(m-f):
				break
		#determines the right boundary of peak to be less than floor plus c percent of difference between max and floor
		for ri, r in enumerate(datapoints[mi:]):
			if r < f + c*(m-f):
				break
		li= mi-li; ri= mi+ri
		if l < f: li+=1	# blocks right peak endpoint sharing
		if r < f: ri-=1	# blocks left peak endpoint sharing
		peak = datapoints[li:ri+1]	#determines the peak as the set of points on the interval [left bound, right bound]
		area = sum(peak) #approximates the peak area by summing its datapoints
		peaks.append((m, li, ri, area, peak)) #stores the peak and descriptors: maximum, li, ri, peak area
		datapoints = datapoints[:li] + [f-1]*(ri-li+1) + datapoints[ri+1:] #reduces peak to a value below floor to permit selection of next highest peak
	return peaks

def max_index(datapoints):
	mi, m  = 0, datapoints[0]
	for ni, n in enumerate(datapoints):
		if n > m:
			mi, m = ni, n
	return (mi, m)



		

			
		
