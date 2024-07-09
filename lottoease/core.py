from curl_cffi import requests
import re


ENTER_INDIVIDUAL_LOTTERY_URL = 'https://lottery.broadwaydirect.com/enter-lottery/'

SHOW_NAMES_TO_API_URLS = {
    "six": "https://lottery.broadwaydirect.com/show/six-ny/",
}


class LotteryApplier(object):

    def __init__(self, email):
        self.email = email
    
    def apply_broadway_lotteries(self):
        print('hey')
        showtime_ids = self.get_showtime_lotteries()
        for showtime_id in showtime_ids:
            self.enter_showtime_lottery(showtime_id)

    
    def get_showtime_lotteries(self):
        # fetch specific show lotteries
        response = requests.get(
            'https://lottery.broadwaydirect.com/show/six-ny/',
            headers=self._get_headers(),
            impersonate="chrome"
        )

        # from response, parse '825610' from the following sample syntax:
        # <a href="https://lottery.broadwaydirect.com/enter-lottery/?lottery=825610&window=popup" class="btn btn-primary enter-button enter-lottery-link">
        # ideally add functionality later to only pull ids from showtimes we want (i.e. not matinees)

        showtime_ids_set = set()
        showtime_ids = re.findall("lottery=(.*?)\&", response.text)
        showtime_ids_set.update(showtime_ids)

        return showtime_ids_set
        
        
    def enter_showtime_lottery(self, showtime_id): 
        # enter lottery
        
        params = {
            'lottery': f'{showtime_id}',
            'window': 'popup',
        }
        
        # dummy data for now 
        data = {
            'dlslot_name_first': 'tim',
            'dlslot_name_last': 'hrea',
            'dlslot_ticket_qty': '1',
            'dlslot_email': f'{self.email}',
            'dlslot_dob_month': '03',
            'dlslot_dob_day': '03',
            'dlslot_dob_year': '1992',
            'dlslot_zip': '10005',
            'dlslot_country': '2',
            'dlslot_agree': 'true',
            'dlslot_website': '',
            'dlslot_performance_id': f'{showtime_id}',
            'dlslot_nonce': '42d232200c',
            '_wp_http_referer': f'/enter-lottery/?lottery={showtime_id}&window=popup',
        }

        requests.post(
            ENTER_INDIVIDUAL_LOTTERY_URL,
            impersonate="chrome",
            params=params,
            headers=self._get_headers(content_type='application/x-www-form-urlencoded'),
            data=data,
        )

        # try:
        #     res = r.json()
        # except Exception as e:
        #     print(f'An error occurred trying to enter lottery: {e}')
        #     print(f'return from api call: {r}')
        #     raise e
        
        print('hey')

    def _get_request_headers(self, content_type=None):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            # 'sec-fetch-dest': 'iframe',    from entering lottery
            # 'sec-fetch-dest': 'document',    from fetching showtimes
            'sec-fetch-mode': 'navigate',   
            # 'sec-fetch-site': 'none',     from entering lottery
            # 'sec-fetch-site': 'same-origin',     from fetching showtimes
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }

        if content_type:
            headers['content-type'] = content_type

        return headers

