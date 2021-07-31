'''
Author: MASTREX
'''

from time import sleep
from os import system
import logging
import sqlite3
import datetime

import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

class FlipkartTracker():
	'''
	url: product url

	limit: limit price
	'''

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.is_active = False
		self.products = []
		self.total_product_count = -1
		self.conn = sqlite3.connect('data.db')
		self.session = requests.Session()
		self.session.headers = {'DNT': '1',
								'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
		#self.set_proxies()
		self.read_data()

	def _set_proxies(self):
		'''
		Set for burp proxy
		'''
		self.session.proxies = {
			'http': 'http://127.0.0.1:8080',
			'https': 'https://127.0.0.1:8080'
		}
		self.session.verify = 'PortSwiggerCA.crt'

	def read_data(self):
		c = self.conn.cursor()
		try:
			c.execute('SELECT id, name, url, demand_price, current_id, date_added FROM products')
		except sqlite3.OperationalError as e:
			if str(e).find('no such table') >= 0:
				self.logger.warning('Previous Data file not found!')
				c.execute('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, url TEXT, demand_price REAL, current_id INTEGER, date_added TEXT)')
			else:
				raise
		except:
			raise
		else:
			for i, n, u, dp, currid, dta in c.fetchall():
				self.products.append({
					'name' : n,
					'url' : u,
					'demand_price' : dp,
					'curr_id' : currid,
					'date_added': datetime.datetime.strptime(dta, '%Y-%m-%d T%H:%M:%S')
				})
				self.total_product_count = i
			self.logger.info('Data file exist and read successfully')
			print(self.products)
	
	def add_product(self, name, url, demand_price):
		dt = datetime.datetime.now()
		self.products.append({
			'name' : name,
			'url' : url,
			'demand_price' : demand_price,
			'curr_id' : -1,
			'date_added': dt
		})
		self.total_product_count += 1
		c = self.conn.cursor()
		try:
			c.execute(f'CREATE TABLE product_{self.total_product_count} (id INTEGER PRIMARY KEY, datetime TEXT, in_stock INTEGER, Price REAL)')
		except:
			raise
		try:
			dt_str = dt.strftime('%Y-%m-%d T%H:%M:%S')
			c.execute(f'INSERT INTO products (id, name, url, demand_price, current_id, date_added) VALUES ({self.total_product_count}, \'{name}\', \'{url}\', {demand_price}, -1, \'{dt_str}\')')
		except:
			raise
		self.commit_to_db()
		logger.info('Product added')

	def db_update(self):
		pass

	def db_delete(self):
		pass

	def notifier(self):
		pass

	def run(self):
		pass

	def fetch(self):
		self.logger.debug('Making request...')
		response = self.session.get(self.url)
		self.logger.debug('Got Response')
		soup = BeautifulSoup(response.content, 'html.parser')
		price = soup.find('div', attrs={'class': '_30jeq3 _16Jk6d'}).text
		self.price = (int)(price[1:].replace(',', ''))

		#<div class="_16FRp0">Sold Out</div>
		if (soup.find('div', attrs={'class': '_16FRp0'}) == None): self.in_stock = True

	def status(self) -> str:
		if(self.in_stock):
			if(self.price <= self.limit):
				return 'Available and in range at Rs' + str(self.price)
			else:
				return 'Available but not in range at Rs' + str(self.price)
		else:
			if(self.price <= self.limit):
				return 'Not available but in range at Rs' + str(self.price)
			else:
				return 'Not available and not in range at Rs' + str(self.price)

	def commit_to_db(self):
		try:
			self.conn.commit()
		except:
			raise

	def end(self):
		self.session.close()

if __name__ == '__main__':
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	c_handler = logging.StreamHandler()
	c_handler.setFormatter(logging.Formatter('%(asctime)s : %(name)s - %(levelname)s : %(message)s'))
	c_handler.setLevel(logging.INFO)
	logger.addHandler(c_handler)

	# products_dict = {
	# 	# ' <NAME> ': FlipkartTracker(url=' <URL> ', limit= <LIMIT> )
	# 	'SAMSUNG Galaxy A50': FlipkartTracker(url='https://www.flipkart.com/samsung-galaxy-a50-blue-64-gb/p/itmfe4cssxfzcph3?pid=MOBFE4CSRHGF4ETQ&lid=LSTMOBFE4CSRHGF4ETQGJSQUK', limit=20000),
	# 	'Sandisk 32GB': FlipkartTracker(url='https://www.flipkart.com/sandisk-ultra-32-gb-microsdhc-class-10-120-mbps-memory-card/p/itm8a003f95095a5?pid=ACCFXNGYT6YJZVHZ&lid=LSTACCFXNGYT6YJZVHZKDEKXR', limit=450),
	# 	# '': FlipkartTracker(url='', limit=),
	# 	# '': FlipkartTracker(url='', limit=),
	# 	# '': FlipkartTracker(url='', limit=),
	# }
	# sleep_time = (int)((1*60) / len(products_dict))   #sleep_time = (int)((interval-time-in-sec) / len(products_dict))
	# # Do not abuse flipkart server by setting very small interval-time

	# while(True):
	# 	try:
	# 		system('clear')
	# 		for name, tracker in products_dict.items():
	# 			temp_in_stock = tracker.in_stock
	# 			temp_price = tracker.price
	# 			tracker.fetch()
	# 			status_str = name + ': ' + tracker.status()
	# 			logger.info(status_str)
	# 			# App Notification when status changed
	# 			if(tracker.in_stock != temp_in_stock or tracker.price != temp_price):
	# 				system('termux-notification -c \'' + status_str + '\' --group flipkart -i 0 --title \'Flipkart Tracker\'')
	# 				logger.debug('In app notificaton sent')
	# 			logger.warning('sleeping for {}'.format(sleep_time))
	# 			sleep(sleep_time)
	# 	except ConnectionError:
	# 		logger.error('No Internet!')
	# 		logger.warning('Going to sleep for 10 mins')
	# 		sleep(10*60)
	# 	except KeyboardInterrupt:
	# 		logger.error('Terminated by user')
	# 		break
	# 	except Exception as e:
	# 		logger.exception(e)
	# 		raise e
	# for tracker in products_dict.values():
	# 	tracker.end()
	# 	logger.debug('all session closed successfully')

	tracker = FlipkartTracker()
	choosed = 1
	while(choosed == 1):
		print()
		print('Enter the option:')
		print('1. Add Product')
		print('2. Run tracker')
		print('9. Remove Product')
		print('0. EXIT')
		try:
			choosed = (int)(input())
			if(choosed < 0 or choosed > 2):
				raise ValueError
		except ValueError:
			print('Invalid Option!')
		else:
			if choosed == 0:
				# end
				pass
			elif choosed == 1:
				# add
				print()
				url=input('Enter the product URL (must be obtained from web browser): ')
				name=input('Enter a short name: ')
				dp=(float)(input('Enter the limit price: '))
				tracker.add_product(name, url, dp)
			elif choosed == 2:
				# run
				pass
			elif choosed == 9:
				# remove
				pass
