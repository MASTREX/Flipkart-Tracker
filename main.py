import requests
from requests.exceptions import ConnectionError
from bs4 import BeautifulSoup
from time import sleep

class FlipkartTracker():
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    def __init__(self, url, limit = 0):
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
        response = self.session.get(self.url)
        soup = BeautifulSoup(response.content, 'lxml')
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
                return 'Nnt available and not in range at Rs' + str(self.price)
        
    def end(self):
        self.session.close()

if(__name__ == '__main__'):
    products_dict = {
        #'Name': tracker
        'Samsung Monitor': FlipkartTracker(url='https://www.flipkart.com/samsung-23-8-inch-curved-full-hd-led-backlit-va-panel-monitor-lc24f390fhwxxl/p/itmezu53yhwg2ayg?pid=MONEZU4Z8BYBV2GZ', limit=9000),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
        #'': FlipkartTracker(url='', limit=),
    }
    sleep_time = (int)((10) / len(products_dict))
    while(True):
        try:
            for name, tracker in products_dict.items():
                tracker.fetch()
                print(name + ': ' + tracker.status())
                sleep(sleep_time)
        except ConnectionError:
            print('No Internet!')
            break
        except KeyboardInterrupt:
            print('Terminated by user')
            break
        except Exception as e:
            raise e
    for tracker in products_dict.values():            
        tracker.end()