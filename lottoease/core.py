import os
import re

from curl_cffi import requests
from dotenv import load_dotenv
from twocaptcha import TwoCaptcha


load_dotenv()


FETCH_SHOWS_URL = 'https://lottery.broadwaydirect.com/'
ENTER_INDIVIDUAL_LOTTERY_URL = 'https://lottery.broadwaydirect.com/enter-lottery/'
API_KEY_TWOCAPTCHA = os.getenv('API_KEY_TWOCAPTCHA')
RECAPTCHA_SITE_KEY_BROADWAY_DIRECT = '6LeIhQ4TAAAAACUkR1rzWeVk63ko-sACUlB7i932'


class LotteryApplier(object):

    def __init__(self, email):
        self.email = email
    
    def apply_broadway_lotteries(self):
        """
        Performs the following steps:
            1. Fetches all current broadway shows that have ongoing lotteries
            2. For each show, fetch the individual showtimes that are available to apply for
            3. For each showtime, generate a nonce token (which is required to enter lottery)
            4. Enter broadway lottery for the specific showtime with the nonce token 
        """
        show_names = self.fetch_shows()

        num_shows_applied = 0
        num_showtimes_applied = 0
        
        for show_name in show_names:
            showtime_ids = self.get_showtime_lotteries(show_name)
            for showtime_id in showtime_ids:
                nonce_token, recaptcha_token = self.generate_nonce_and_recaptcha_tokens(showtime_id)
                self.enter_showtime_lottery(showtime_id, nonce_token, recaptcha_token)
                num_showtimes_applied += 1
            
            if showtime_ids:
                num_shows_applied += 1
            
            print(f'Finished applying for show {show_name}')
        
        print(f'Successfully entered lotteries for {num_showtimes_applied} showtimes across {num_shows_applied} shows.')

    
    def fetch_shows(self):
        print(f'Fetching all broadway shows with ongoing lotteries...')
        response = requests.get(
            FETCH_SHOWS_URL,
            headers=self._get_request_headers(),
            impersonate="chrome",
        )

        show_regex = '\/show\/(.*?)\/'

        unique_show_names = set()
        show_names = re.findall(show_regex, response.text)
        unique_show_names.update(show_names)

        print(f'Found the following shows with ongoing lotteries: {unique_show_names}')

        return unique_show_names
        

    def generate_nonce_and_recaptcha_tokens(self, showtime_id):
        params = {
            'lottery': f'{showtime_id}',
            'window': 'popup',
        }
        
        response = requests.get(
            ENTER_INDIVIDUAL_LOTTERY_URL,
            impersonate="chrome",
            params=params,
            headers=self._get_request_headers(),
        )

        # parse nonce value from sample response snippet below
        # <input type="hidden" id="dlslot_nonce" name="dlslot_nonce" value="194b24b759"/>
        nonce_regex = 'name="dlslot_nonce" value="(.*?)"'
        nonce_value = re.findall(nonce_regex, response.text)

        recaptcha_regex = 'class="g-recaptcha'
        recaptcha_token = None
        showtime_url = ENTER_INDIVIDUAL_LOTTERY_URL + f'?lottery={showtime_id}&window=popup'
        if re.search(recaptcha_regex, response.text):
            recaptcha_token = self.generate_recaptcha_token(showtime_url)

        return nonce_value[0], recaptcha_token
    
    def generate_recaptcha_token(self, showtime_url):
        print(f'Recaptcha required. Fetching recaptcha response token...')
        solver = TwoCaptcha(API_KEY_TWOCAPTCHA)
        try:
            result = solver.recaptcha(
                sitekey=RECAPTCHA_SITE_KEY_BROADWAY_DIRECT,
                url=showtime_url)

        except Exception as e:
            print(e)
        
        return result.get('code')

    
    def get_showtime_lotteries(self, show_name):
        print(f'Fetching active showtimes for {show_name}...')
        show_url = self._generate_show_url_from_show_name(show_name)

        response = requests.get(
            show_url,
            headers=self._get_request_headers(),
            impersonate="chrome"
        )

        # snippet of sample response below, need to parse for showtime_id '825610'
        # <a href="https://lottery.broadwaydirect.com/enter-lottery/?lottery=825610&window=popup" class="btn btn-primary enter-button enter-lottery-link">

        showtime_id_regex = 'lottery=(.*?)\&'
        unique_showtime_ids = set()
        showtime_ids = re.findall(showtime_id_regex, response.text)
        unique_showtime_ids.update(showtime_ids)

        print(f'Found {len(unique_showtime_ids)} active showtimes for {show_name}')

        return unique_showtime_ids
        
        
    def enter_showtime_lottery(self, showtime_id, nonce_token, recaptcha_token): 
        # enter lottery

        print(f'Entering lottery for showtime_id: {showtime_id}')
        params = {
            'lottery': f'{showtime_id}',
            'window': 'popup',
        }

        # dummy data for now 
        data = {
            'dlslot_name_first': 'ed',
            'dlslot_name_last': 'edson',
            'dlslot_ticket_qty': '1',
            'dlslot_email': f'{self.email}',
            'dlslot_dob_month': '09',
            'dlslot_dob_day': '09',
            'dlslot_dob_year': '1999',
            'dlslot_zip': '10009',
            'dlslot_country': '2',
            'dlslot_agree': 'true',
            'dlslot_website': '',
            'dlslot_performance_id': f'{showtime_id}',
            'dlslot_nonce': f'{nonce_token}',
            '_wp_http_referer': f'/enter-lottery/?lottery={showtime_id}&window=popup',
        }

        if recaptcha_token:
            data['g-recaptcha-response'] = recaptcha_token

        r = requests.post(
            ENTER_INDIVIDUAL_LOTTERY_URL,
            impersonate="chrome",
            params=params,
            allow_redirects=False,
            headers=self._get_request_headers(
                content_type='application/x-www-form-urlencoded',
                ),
            data=data,
        )
        
        print(f'Entered lottery for showtime {showtime_id}')

    def _get_request_headers(self, content_type=None):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'origin': 'https://lottery.broadwaydirect.com',
            'priority': 'u=0, i',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',   
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }

        if content_type:
            headers['content-type'] = content_type

        return headers
    
    def _generate_show_url_from_show_name(self, show_name):
        return f'https://lottery.broadwaydirect.com/show/{show_name}/'
