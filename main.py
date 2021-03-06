'''
Author: MASTREX
'''

from time import sleep
from os import system
import logging
import sqlite3
import datetime

import requests
from requests.exceptions import (ConnectionError, ReadTimeout)
from bs4 import BeautifulSoup

class FlipkartTracker():
	'''
	self.products: Is a list type containing all details of all products

	self.total_product_count: An int and stores count of all product starting from 0
	'''

	def __init__(self):
		self.logger = logging.getLogger(__name__)
		self.is_active = False
		self.products = []
		self.total_product_count = -1
		self.conn = sqlite3.connect('data.db')
		self.req_headers = {'DNT': '1',
							'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
		# self.set_proxies()
		self.read_data()

	# def _set_proxies(self):
	# 	'''
	# 	Set for burp proxy
	# 	'''
	# 	self.session.proxies = {
	# 		'http': 'http://127.0.0.1:8080',
	# 		'https': 'https://127.0.0.1:8080'
	# 	}
	# 	self.session.verify = 'PortSwiggerCA.crt'

	def read_data(self):
		'''
		read stored data from data.db
		'''
		c = self.conn.cursor()
		c2 = self.conn.cursor()
		try:
			c.execute('SELECT id, name, url, demand_price, curr_id, date_added FROM products')
		except sqlite3.OperationalError as e:
			if str(e).find('no such table') >= 0:
				self.logger.warning('Previous Data file not found!')
				self.execute_db('CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, url TEXT, demand_price REAL, curr_id INTEGER, date_added TEXT)')
			else:
				raise
		except:
			raise
		else:
			for i, n, u, dp, curr_id, dta in c.fetchall():
				self.products.append({
					'name' : n,
					'url' : u,
					'demand_price' : dp,
					'curr_id' : curr_id,
					'date_added': datetime.datetime.strptime(dta, '%Y-%m-%d T%H:%M:%S')
				})

				# reading last entries
				if curr_id != -1:
					try:
						c2.execute(f'SELECT * FROM product_{i} WHERE id = {curr_id}')
					except:
						raise
					else:
						for id, dt, in_stock, price in c2.fetchall():
							self.products[i]['last_entry'] = {
								'datetime' : datetime.datetime.strptime(dt, '%Y-%m-%d T%H:%M:%S'),
								'in_stock' : in_stock == 1,	# True or False
								'price' : price
							}
			self.total_product_count = len(self.products) - 1
			self.logger.info('Data file exist and read successfully')
			self.logger.debug(self.products)

	def show_all_products(self):
		print()
		print(f'{"id":<5} {"Product Name":<20}')
		for i in range(self.total_product_count + 1):
			print(f'{i:<5} {self.products[i]["name"]:<20}')

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
		self.execute_db(f'CREATE TABLE product_{self.total_product_count} (id INTEGER PRIMARY KEY, datetime TEXT, in_stock INTEGER, price REAL)')

		dt_str = dt.strftime('%Y-%m-%d T%H:%M:%S')
		self.execute_db(f'INSERT INTO products (id, name, url, demand_price, curr_id, date_added) VALUES ({self.total_product_count}, "{name}", "{url}", {demand_price}, -1, "{dt_str}")')
		self.commit_to_db()
		logger.info('Product added')

	def db_update(self, product_id):
		product = self.products[product_id]
		self.execute_db(f'UPDATE products SET curr_id = "{product["curr_id"]}" WHERE id = "{product_id}"')

		dt_str = product['last_entry']['datetime'].strftime('%Y-%m-%d T%H:%M:%S')
		if product['last_entry']['in_stock']:
			self.execute_db(f'INSERT INTO product_{product_id} (id, datetime, in_stock, price) VALUES ({product["curr_id"]}, "{dt_str}", 1, {product["last_entry"]["price"]})')
		else:
			self.execute_db(f'INSERT INTO product_{product_id} (id, datetime, in_stock, price) VALUES ({product["curr_id"]}, "{dt_str}", 0, {product["last_entry"]["price"]})')
		self.commit_to_db()
		self.logger.info('database has been updated')

	def db_delete(self):
		pass

	def notifier(self, msg, id=-1):
		system('termux-notification -c \'' + msg + '\' --group flipkart -i ' + str(id) + ' --title \'Flipkart Tracker\'')
		self.logger.debug('In app notificaton sent')

	def run(self):
		if self.total_product_count == -1:
			self.logger.error('No Product!')
			self.end()
			return
		sleep_time = (int)((60*60) / len(self.products))	# sleep_time = (int)((interval-time-in-sec) / len(products_dict))
															# Do not abuse flipkart server by setting very small interval-time
		loop_c = 0
		while True:
			try:
				system('clear')
				loop_c += 1
				print(f'Loop Count: {loop_c}\n')
				for product_id in range(self.total_product_count + 1):
					try:
						self.fetch(product_id)
					except (ConnectionError, ReadTimeout):
						logger.error('No Internet!')
						self.notifier('No Internet!', -1)
						logger.warning('Going to sleep for 10 mins')
						sleep(10*60)
					else:
						logger.warning('sleeping for {}'.format(sleep_time))
						sleep(sleep_time)
			except KeyboardInterrupt:
				logger.error('Terminated by user')
				break
			except Exception as e:
				logger.exception(e)
				self.notifier('Error!', -1)
				raise e
		self.end()

	def fetch(self, product_id):
		self.logger.debug('Making request...')
		response = requests.get(self.products[product_id]['url'], headers=self.req_headers)
		self.logger.debug('Got Response')
		soup = BeautifulSoup(response.content, 'html.parser')
		try:
			price = soup.find('div', attrs={'class': '_30jeq3 _16Jk6d'}).text
		except AttributeError:
			self.logger.error('No price tag found!')
			return
		curr_price = (int)(price[1:].replace(',', ''))

		# <div class="_16FRp0">Sold Out</div>
		if (soup.find('div', attrs={'class': '_16FRp0'}) == None):
			self.update_handler(product_id, curr_price, True)
		else:
			self.update_handler(product_id, curr_price, False)

	def update_handler(self, product_id, new_price, new_stock_status):
		product = self.products[product_id]
		dt = datetime.datetime.now()
		if product['curr_id'] != -1:
			last_in_stock = product['last_entry']['in_stock']
			last_price = product['last_entry']['price']
		else:
			last_in_stock = False
			last_price = 0.0
			product['last_entry'] = {}
		status_str = product['name'] + ': '
		if(new_stock_status):
			if(new_price <= product['demand_price']):
				status_str += 'Available and in range at Rs' + str(new_price)
			else:
				status_str += 'Available but not in range at Rs' + str(new_price)
		else:
			if(new_price <= product['demand_price']):
				status_str += 'Not available but in range at Rs' + str(new_price)
			else:
				status_str += 'Not available and not in range at Rs' + str(new_price)
		logger.info(status_str)
		if (int)(last_price) != (int)(new_price) or last_in_stock != new_stock_status:
			product['curr_id'] += 1
			product['last_entry']['datetime'] = dt
			product['last_entry']['in_stock'] = new_stock_status
			product['last_entry']['price'] = new_price
			self.db_update(product_id)
			# App Notification when status changed
			self.notifier(status_str, product_id)

	def update_url(self, id, new_url):
		self.products[id]['url'] = new_url
		self.execute_db(f'UPDATE products SET url = "{new_url}" WHERE id = {id}')
		self.commit_to_db()
		self.logger.info('URL Updated')

	def execute_db(self, command):
		'''
		only use for simple executing commands which do not provide any output or object
		like do not use for SELECT commands
		'''
		c = self.conn.cursor()
		try:
			c.execute(command)
		except:
			raise

	def commit_to_db(self):
		try:
			self.conn.commit()
		except:
			raise

	def end(self):
		self.conn.close()
		logger.info('Tracker Stopped')

if __name__ == '__main__':
	logger = logging.getLogger(__name__)
	logger.setLevel(logging.DEBUG)
	c_handler = logging.StreamHandler()
	c_handler.setFormatter(logging.Formatter('%(asctime)s : %(name)s - %(levelname)s : %(message)s'))
	c_handler.setLevel(logging.INFO)
	# c_handler.setLevel(logging.DEBUG)
	logger.addHandler(c_handler)

	tracker = FlipkartTracker()
	choosed = 1
	while(choosed == 1):
		print()
		print('Enter the option:')
		print('1. Add Product')
		print('2. Run tracker')
		print('3. Remove Product')
		print('4. Update or change configuration')
		print('0. EXIT')
		try:
			choosed = (int)(input())
			if(choosed < 0 or choosed > 4):
				raise ValueError
		except ValueError:
			print('Invalid Option!')
		else:
			if choosed == 0:
				# exit
				exit()
			elif choosed == 1:
				# add
				print()
				url=input('Enter the product URL (must be obtained from web browser): ')
				name=input('Enter a short name: ')
				dp=(float)(input('Enter the limit price: '))
				tracker.add_product(name, url, dp)
			elif choosed == 2:
				# run
				tracker.run()
			elif choosed == 3:
				# remove
				print('This feature is in development!')
			elif choosed == 4:
				# Update config
				print()
				print('Enter the option:')
				print('1. Update URL')
				try:
					choosed = (int)(input())
					if(choosed < 1 or choosed > 1):
						raise ValueError
				except ValueError:
					print('Invalid Option!')
				else:
					if choosed == 1:
						# edit URL
						tracker.show_all_products()
						try:
							id = int(input('\nEnter id of the product: '))
							if(id < 0 or id > tracker.total_product_count):
								raise ValueError
						except ValueError:
							print('Id out of range!')
						else:
							print(f'\nCurrent URL: {tracker.products[id]["url"]}')
							new_url = input('Enter New URL: ')
							tracker.update_url(id, new_url)
							print('Done')
