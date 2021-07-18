from time import sleep
from os import system
import logging

import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup

class FlipkartTracker():
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def __init__(self, url, limit = 0):
        self.logger = logging.getLogger()
        self.url = url
        self.is_active = False
        self.limit = limit
        self.price = 0
        self.in_stock = True
        self.session = requests.Session()
        self.session.headers = {'DNT': '1',
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        #self.set_proxies()

    def set_proxies(self):
        '''
        Set for burp proxy
        '''
        self.session.proxies = {
            'http': 'http://127.0.0.1:8080',
            'https': 'https://127.0.0.1:8080'
        }
        self.session.verify = 'PortSwiggerCA.crt'

    def fetch(self):
        self.logger.debug('Making request...')
        response = self.session.get(self.url)
        self.logger.debug('Got Response')
        soup = BeautifulSoup(response.content, 'html.parser')
        price = soup.find('div', attrs={'class': '_30jeq3 _16Jk6d'}).text
        self.price = (int)(price[1:].replace(',', ''))

        #<div class="_16FRp0">Sold Out</div>
        if (soup.find('div', attrs={'class': '_16FRp0'}) != None): self.in_stock = False

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

    def end(self):
        self.session.close()

if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(logging.Formatter('%(asctime)s : %(name)s - %(levelname)s : %(message)s'))
    c_handler.setLevel(logging.INFO)
    logger.addHandler(c_handler)

    products_dict = {
        #'Name': tracker
        'Samsung Monitor': FlipkartTracker(url='https://www.flipkart.com/samsung-23-8-inch-curved-full-hd-led-backlit-va-panel-monitor-lc24f390fhwxxl/p/itmezu53yhwg2ayg?pid=MONEZU4Z8BYBV2GZ', limit=9000),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
    }
    sleep_time = (int)((10) / len(products_dict))   #sleep_time = (int)((interval-time-in-sec) / len(products_dict))
    while(True):
        try:
            for name, tracker in products_dict.items():
                tracker.fetch()
                status_str = name + ': ' + tracker.status()
                logger.info(status_str)
                #system('termux-notification -c \'' + status_str + '\' --group flipkart -i 0 --title \'Flipkart Tracker\'')
                logger.warning('sleeping for {}'.format(sleep_time))
                sleep(sleep_time)
        except ConnectionError:
            logger.error('No Internet!')
            sleep(10*60)
        except KeyboardInterrupt:
            logger.error('Terminated by user')
            break
        except Exception as e:
            logger.exception(e)
            raise e
    for tracker in products_dict.values():
        tracker.end()
        logger.debug('all session closed successfully')
