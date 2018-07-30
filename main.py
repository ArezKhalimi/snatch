import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
import tablib

from config import SITES, TOKEN, SELECTED_MOUNTH


filename = 'visits_{}.xls'.format(datetime.now().isoformat(' ', 'seconds'))

links = [
        'https://api.similarweb.com/v1/website/{}/total-traffic-and-engagement/visits'.format(site)
        for site in SITES
]

payload = {
    'api_key': TOKEN,
    'start_date': SELECTED_MOUNTH,
    'end_date': SELECTED_MOUNTH,
    'main_domain_only': True,
    'granularity': 'monthly',
}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

data = tablib.Dataset()
data.headers = ['Site', 'Date', 'Visits']


def get_data(url):
    return requests.get(url, params=payload)

async def main():
    print(bcolors.HEADER + 'Start collecting data' + bcolors.ENDC)
    with ThreadPoolExecutor(max_workers=20) as executor:
        loop = asyncio.get_event_loop()
        futures = [
            loop.run_in_executor(
                executor, 
                get_data, 
                url
            )
            for url in links
        ]
        for response in await asyncio.gather(*futures):
            site = response.url.split('/')[5]

            if not response.ok:
                try:
                    error = response.json()
                else:
                    error = 'unknown'
                print(
                    bcolors.FAIL + site,
                    ': Fail to collect ' + bcolors.ENDC,
                    error
                )
            else:
                print(bcolors.OKBLUE + site, ' collected' + bcolors.ENDC)
                visits = response.json()['visits'][0]
                data.append([site, visits['date'], visits['visits']])

    print(bcolors.HEADER + 'Creating a file...' + bcolors.ENDC)
    book = tablib.Databook((data,))
    with open(filename, 'wb') as f:
        f.write(book.xls)
    print(bcolors.OKGREEN + 'Collecting complited' + bcolors.ENDC)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
