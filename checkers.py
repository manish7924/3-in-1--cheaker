# checkers.py
import requests
import secrets
import user_agent
import time
import json
import random
from bs4 import BeautifulSoup
from user_agent import generate_user_agent as elia

# Globals for Checkers
TOKEN_TTL = 600
GMAIL_TOKENS = {'TL': None, 'gaps': None, 'timestamp': 0}
USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]
check_counter = {"aol": 0}
tokens = {"aol": {}}

# --- GMAIL LOGIC ---
def get_tokens_from_google():
    base = 'https://accounts.google.com/_/signup'
    headers = {
        'user-agent': user_agent.generate_user_agent(),
        'google-accounts-xsrf': '1',
    }
    try:
        gaps = ''.join(secrets.choice("qwertyuiopasdfghjklzxcvbnm") for _ in range(secrets.randbelow(16)+15))
        cookies = {'__Host-GAPS': gaps}
        
        r1 = requests.post(
            base + '/validatepersonaldetails',
            params={'hl': 'ar', '_reqid': '74404', 'rt': 'j'},
            data={
                'f.req': '["AEThLlymT9V_0eW9Zw42mUXBqA3s9U9ljzwK7Jia8M4qy_5H3vwDL4GhSJXkUXTnPL_roS69KYSkaVJLdkmOC6bPDO0jy5qaBZR0nGnsWOb1bhxEY_YOrhedYnF3CldZzhireOeUd-vT8WbFd7SXxfhuWiGNtuPBrMKSLuMomStQkZieaIHlfdka8G45OmseoCfbsvWmoc7U","EİZON","EizonxTool","EİZON","EizonxTool",0,0,null,null,null,0,null,1,[],1]',
                'deviceinfo': '[null,null,null,null,null,"TR",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,1,null,0,1,"",null,null,1,1,2]',
            },
            headers=headers,
            cookies=cookies,
            timeout=12
        )
        if r1.status_code != 200 or '",null,"' not in r1.text:
            return None, None
            
        TL = r1.text.split('",null,"')[1].split('"')[0]
        gaps_cookie = r1.cookies.get('__Host-GAPS')
        return TL, gaps_cookie
    except:
        return None, None

def get_valid_tokens():
    global GMAIL_TOKENS
    current_time = time.time()
    if GMAIL_TOKENS['TL'] and current_time < (GMAIL_TOKENS['timestamp'] + TOKEN_TTL):
        return GMAIL_TOKENS['TL'], GMAIL_TOKENS['gaps']
    
    TL, gaps = get_tokens_from_google()
    if TL and gaps:
        GMAIL_TOKENS['TL'] = TL
        GMAIL_TOKENS['gaps'] = gaps
        GMAIL_TOKENS['timestamp'] = current_time
        return TL, gaps
    return None, None

class GmailChecker:
    def __init__(self, username, TL, gaps):
        self.username = username.split("@")[0] if "@" in username else username
        self.TL = TL
        self.gaps = gaps
        self.base = 'https://accounts.google.com/_/signup'
        self.headers = {
            'user-agent': user_agent.generate_user_agent(),
            'google-accounts-xsrf': '1',
        }

    def check(self):
        if not self.TL or not self.gaps:
            return False
        try:
            r2 = requests.post(
                self.base + '/usernameavailability',
                params={'TL': self.TL},
                cookies={'__Host-GAPS': self.gaps},
                data={
                    'continue': 'https://mail.google.com/mail/u/0/',
                    'ddm': '0',
                    'flowEntry': 'SignUp',
                    'service': 'mail',
                    'theme': 'mn',
                    'f.req': f'["TL:{self.TL}","{self.username}",0,0,1,null,0,5167]',
                    'azt': 'AFoagUUtRlvV928oS9O7F6eeI4dCO2r1ig:1712322460888',
                    'cookiesDisabled': 'false',
                    'deviceinfo': '[null,null,null,null,null,"NL",null,null,null,"GlifWebSignIn",null,[],null,null,null,null,2,null,0,1,"",null,null,2,2]',
                    'gmscoreversion': 'undefined',
                    'flowName': 'GlifWebSignIn'
                },
                headers=self.headers,
                timeout=12
            )
            return r2.status_code == 200 and '"gf.uar",1' in r2.text
        except:
            return False

# --- AOL LOGIC ---
def _new_session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return s

def fetch_tokens(provider):
    base_url = f"https://login.{provider}.com/account/create"
    s = _new_session()
    r = s.get(base_url, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    hidden = {inp.get("name"): inp.get("value") for inp in soup.find_all("input", {"type": "hidden"}) if inp.get("name")}
    return {"cookies": r.cookies.get_dict(), "_session": s, **hidden}

def check_aol_username(username):
    provider = "aol"
    global check_counter, tokens
    if not tokens[provider] or (check_counter[provider] % 20 == 0):
        tokens[provider] = fetch_tokens(provider)
    check_counter[provider] += 1
    token = tokens[provider]
    s = token.get("_session")
    
    payload = {
        "browser-fp-data": json.dumps({"webdriver":0, "language":"en-US", "ts": {"render": int(time.time() * 1000)}}),
        "userId": username,
        "crumb": token.get("crumb"),
        "acrumb": token.get("acrumb"),
        "sessionIndex": token.get("sessionIndex"),
        "specId": "yidregsimplified",
        "context": "REGISTRATION",
        "yidDomain": "aol.com",
        "firstName": "John",
        "lastName": "Doe",
        "password": "Password1234!",
        "mm": "05", "dd": "12", "yyyy": "1990"
    }
    
    headers = {
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded',
        'user-agent': random.choice(USER_AGENTS)
    }
    
    try:
        resp = s.post('https://login.aol.com/account/create/validate', data=payload, headers=headers, cookies=token["cookies"])
        data = resp.json()
        if data.get("step") == 2 or ("fields" in data and "userId" in data["fields"] and "error" not in data["fields"]["userId"]):
            return True
        return False
    except:
        check_counter[provider] = 0
        return False

# --- FAKEMAIL LOGIC ---
def solve_recaptcha():
    while True:
        try:
            anchor_url = "https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LfEUPkgAAAAAKTgbMoewQkWBEQhO2VPL4QviKct&co=aHR0cHM6Ly9oaTIuaW46NDQz&hl=en&v=XrIDux0s7SoNe6_IHkjGC92W&size=invisible"
            params = anchor_url.split('?')[1]
            r = requests.get(f'https://www.google.com/recaptcha/enterprise/anchor?{params}', timeout=10)
            token = r.text.split('recaptcha-token" value="')[1].split('"')[0]
            payload = f"v={params.split('v=')[1].split('&')[0]}&reason=q&c={token}&k=6LfEUPkgAAAAAKTgbMoewQkWBEQhO2VPL4QviKct&co=aHR0cHM6Ly9oaTIuaW46NDQz&hl=en&size=invisible"
            headers = {
                "User-Agent": elia(),
                "Referer": f"https://www.google.com/recaptcha/enterprise/anchor?{params}",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            resp = requests.post('https://www.google.com/recaptcha/enterprise/reload', data=payload, headers=headers, timeout=10)
            return resp.text.split('resp","')[1].split('"')[0]
        except:
            time.sleep(2)
            continue

def check_fakemail(email):
    if "@" not in email:
        return False
    prefix, domain_name = email.split("@", 1)
    while True:
        solve = solve_recaptcha()
        data = {
            'domain': domain_name,
            'prefix': prefix,
            'recaptcha': solve,
        }
        headers = {
            'User-Agent': elia(),
            'Accept': "application/json, text/plain, */*",
            'authorization': "Basic bnVsbA==",
        }
        response = requests.post("https://hi2.in/api/custom", data=data, headers=headers)
        if response.status_code == 429:
            time.sleep(5)
            continue
        try:
            result = response.json()
            return 'expiry' in result
        except:
            return False
