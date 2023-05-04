# (ↄ) 2017-2022 eli fessler (frozenpandaman), clovervidia
# https://github.com/frozenpandaman/s3s
# License: GPLv3

import subprocess
from loguru import logger

from .s3s.iksm import *
A_VERSION = '2.2.2'
pth = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

APP_USER_AGENT = 'Mozilla/5.0 (Linux; Android 11; Pixel 5) ' \
		'AppleWebKit/537.36 (KHTML, like Gecko) ' \
		'Chrome/94.0.4606.61 Mobile Safari/537.36'


def log_in(ver):
	'''Logs in to a Nintendo Account and returns a session_token.'''

	global S3S_VERSION
	S3S_VERSION = ver

	auth_state = base64.urlsafe_b64encode(os.urandom(36))

	auth_code_verifier = base64.urlsafe_b64encode(os.urandom(32))
	auth_cv_hash = hashlib.sha256()
	auth_cv_hash.update(auth_code_verifier.replace(b"=", b""))
	auth_code_challenge = base64.urlsafe_b64encode(auth_cv_hash.digest())

	app_head = {
		'Host':                      'accounts.nintendo.com',
		'Connection':                'keep-alive',
		'Cache-Control':             'max-age=0',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent':                'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.61 Mobile Safari/537.36',
		'Accept':                    'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8n',
		'DNT':                       '1',
		'Accept-Encoding':           'gzip,deflate,br',
	}

	body = {
		'state':                               auth_state,
		'redirect_uri':                        'npf71b963c1b7b6d119://auth',
		'client_id':                           '71b963c1b7b6d119',
		'scope':                               'openid user user.birthday user.mii user.screenName',
		'response_type':                       'session_token_code',
		'session_token_code_challenge':        auth_code_challenge.replace(b"=", b""),
		'session_token_code_challenge_method': 'S256',
		'theme':                               'login_form'
	}

	url = 'https://accounts.nintendo.com/connect/1.0.0/authorize'
	r = session.get(url, headers=app_head, params=body)

	post_login = r.history[0].url

	print("\nMake sure you have fully read the \"Token generation\" section of the readme before proceeding. To manually input a token instead, enter \"skip\" at the prompt below.")
	print("\nNavigate to this URL in your browser:")
	print(post_login)
	print("Log in, right click the \"Select this account\" button, copy the link address, and paste it below:")
	return post_login, auth_code_verifier


def login_2(use_account_url, auth_code_verifier):
	while True:
		try:
			if use_account_url == "skip":
				return "skip"
			session_token_code = re.search('de=(.*)&', use_account_url)
			return get_session_token(session_token_code.group(1), auth_code_verifier)
		except KeyboardInterrupt:
			print("\nBye!")
			return "skip"
		except AttributeError:
			print("Malformed URL. Please try again, or press Ctrl+C to exit.")
			print("URL:", end=' ')
			return "skip"
		except KeyError: # session_token not found
			print("\nThe URL has expired. Please log out and back into your Nintendo Account and try again.")
			return "skip"
		except Exception as ex:
			print(f'ex: {ex}')
			return 'skip'


def post_battle_to_stat_ink(**kwargs):
	user_id = kwargs.get('user_id')
	session_token = kwargs.get('session_token')
	api_key = kwargs.get('api_key')
	user_lang = kwargs.get('acc_loc') or 'zh-CN'
	logger.bind(cron=True).debug(f'post_battle_to_stat_ink: {user_id}')
	logger.bind(cron=True).debug(f'session_token: {session_token}')
	logger.bind(cron=True).debug(f'api_key: {api_key}')

	path_folder = f'{pth}/s3s_user'
	if not os.path.exists(path_folder):
		os.mkdir(path_folder)
	os.chdir(path_folder)

	# get s3s code
	s3s_folder = f'{path_folder}/s3s_git'
	if not os.path.exists(s3s_folder):
		cmd = f'git clone https://github.com/frozenpandaman/s3s {s3s_folder}'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')
		os.chdir(s3s_folder)
	else:
		os.chdir(s3s_folder)
		cmd = f'git pull'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')

	path_user_folder = f'{path_folder}/{user_id}'
	if not os.path.exists(path_user_folder):
		os.mkdir(path_user_folder)
	os.chdir(path_user_folder)

	for _f in ('s3s', 'iksm', 'utils'):
		cmd = f"cp {s3s_folder}/{_f}.py {path_user_folder}/{_f}.py"
		logger.bind(cron=True).debug(f'cli: {cmd}')
		subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')

	CONFIG_DATA = {
		"api_key": api_key,
		"acc_loc": f"{user_lang}|JP",
		"gtoken": "111",
		"bullettoken": "222",
		"session_token": session_token,
		"f_gen": "https://api.imink.app/f"
	}
	config_file = open(f"{path_user_folder}/config.txt", "w")
	config_file.seek(0)
	config_file.write(json.dumps(CONFIG_DATA, indent=4, sort_keys=False, separators=(',', ': ')))
	config_file.close()

	# edit s3s for acc_loc and agent
	cmd_list = [
		"""sed -i "100,1000s/agent[^,]*,/agent': 'https:\/\/t.me\/splatoon3_bot',/g" s3s.py""",
		"""sed -i 's/!= os.path/== os.path/g' s3s.py"""
	]
	for cmd in cmd_list:
		logger.bind(cron=True).debug(f'cli: {cmd}')
		os.system(cmd)

	cmd = 'python3 s3s.py -r'
	logger.bind(cron=True).debug(path_user_folder)
	logger.bind(cron=True).debug(cmd)
	rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
	logger.bind(cron=True).debug(f'cli: {rtn}')

	battle_cnt = 0
	url = ''
	for line in rtn.split('\n'):
		line = line.strip()
		if not line:
			continue
		if 'uploaded to https://stat.ink' in line:
			battle_cnt += 1
			url = line.split('to ')[1].split('spl3')[0]

	logger.bind(cron=True).debug(f'result: {battle_cnt}, {url}')
	if battle_cnt:
		return battle_cnt, f'{url}spl3'


def post_battle_to_stat_ink_s3si_ts(**kwargs):
	user_id = kwargs.get('user_id')
	session_token = kwargs.get('session_token')
	api_key = kwargs.get('api_key')
	user_lang = kwargs.get('acc_loc') or 'zh-CN'
	if not user_lang or user_lang == 'None':
		user_lang = 'zh-CN'
	logger.bind(cron=True).debug(f'post_battle_to_stat_ink: {user_id}')
	logger.bind(cron=True).debug(f'session_token: {session_token}')
	logger.bind(cron=True).debug(f'api_key: {api_key}')

	path_folder = f'{pth}/s3s_user'
	if not os.path.exists(path_folder):
		os.mkdir(path_folder)
	os.chdir(path_folder)

	# get s3s code
	s3s_folder = f'{path_folder}/s3sits_git'
	if not os.path.exists(s3s_folder):
		cmd = f'git clone https://github.com/spacemeowx2/s3si.ts {s3s_folder}'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')
		os.chdir(s3s_folder)
	else:
		os.chdir(s3s_folder)
		os.system('git restore .')
		cmd = f'git pull'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')

	CONFIG_DATA = {
		"userLang": user_lang,
		"loginState": {
			"sessionToken": session_token
		},
		"statInkApiKey": api_key
	}
	path_config_file = f'{s3s_folder}/config_{user_id}.json'
	if not os.path.exists(path_config_file):
		with open(path_config_file, 'w') as f:
			f.write(json.dumps(CONFIG_DATA, indent=2, sort_keys=False, separators=(',', ': ')))
	else:
		for cmd in (
			f"""sed -i "s/userLang[^,]*,/userLang\": \"{user_lang}\",/g" {path_config_file}""",
			f"""sed -i "s/sessionToken[^,]*,/sessionToken\": \"{session_token}\",/g" {path_config_file}""",
			f"""sed -i "s/statInkApiKey[^,]*,/statInkApiKey\": \"{api_key}\",/g" {path_config_file}""",
		):
			logger.bind(cron=True).debug(f'cli: {cmd}')
			os.system(cmd)

	# edit agent
	cmd_list = [
		"""sed -i "1,5s/s3si.ts/s3si.ts - t.me\/splatoon3_bot/g" ./src/constant.ts""",
	]
	for cmd in cmd_list:
		logger.bind(cron=True).debug(f'cli: {cmd}')
		os.system(cmd)

	cmd = f'/home/anyeccc/.deno/bin/deno run -Ar ./s3si.ts -n -p {path_config_file}'
	logger.bind(cron=True).debug(path_config_file)
	logger.bind(cron=True).debug(cmd)
	rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
	logger.bind(cron=True).debug(f'cli: {rtn}')

	battle_cnt = 0
	coop_cnt = 0
	url = ''
	for line in rtn.split('\n'):
		line = line.strip()
		if not line:
			continue
		if 'exported to https://stat.ink' in line:
			if 'salmon3' in line:
				coop_cnt += 1
			else:
				battle_cnt += 1
			url = line.split('to ')[1].split('spl3')[0].split('salmon3')[0][:-1]

	logger.bind(cron=True).debug(f'result: {battle_cnt}, {coop_cnt}, {url}')
	if battle_cnt or coop_cnt:
		return battle_cnt, coop_cnt, url


def update_s3si_ts():
	path_folder = f'{pth}/s3s_user'
	if not os.path.exists(path_folder):
		os.mkdir(path_folder)
	os.chdir(path_folder)

	# get s3s code
	s3s_folder = f'{path_folder}/s3sits_git'
	if not os.path.exists(s3s_folder):
		cmd = f'git clone https://github.com/spacemeowx2/s3si.ts {s3s_folder}'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')
		os.chdir(s3s_folder)
	else:
		os.chdir(s3s_folder)
		os.system('git restore .')
		cmd = f'git pull'
		rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
		logger.bind(cron=True).debug(f'cli: {rtn}')

	# edit agent
	cmd_list = [
		"""sed -i "1,5s/s3si.ts/s3si.ts - t.me\/splatoon3_bot/g" ./src/constant.ts""",
	]
	for cmd in cmd_list:
		logger.bind(cron=True).debug(f'cli: {cmd}')
		os.system(cmd)


def exported_to_stat_ink(user_id, session_token, api_key, user_lang):
	logger.bind(cron=True).debug(f'exported_to_stat_ink: {user_id}')
	logger.bind(cron=True).debug(f'session_token: {session_token}')
	logger.bind(cron=True).debug(f'api_key: {api_key}')
	user_lang = user_lang or 'zh-CN'

	s3sits_folder = f'{pth}/s3s_user/s3sits_git'
	os.chdir(s3sits_folder)

	path_config_file = f'{s3sits_folder}/config_{user_id}.json'
	if not os.path.exists(path_config_file):
		config_data = {
			"userLang": user_lang,
			"loginState": {
				"sessionToken": session_token
			},
			"statInkApiKey": api_key
		}
		with open(path_config_file, 'w') as f:
			f.write(json.dumps(config_data, indent=2, sort_keys=False, separators=(',', ': ')))
	else:
		for cmd in (
			f"""sed -i "s/userLang[^,]*,/userLang\": \"{user_lang}\",/g" {path_config_file}""",
			f"""sed -i "s/sessionToken[^,]*,/sessionToken\": \"{session_token}\",/g" {path_config_file}""",
			f"""sed -i "s/statInkApiKey[^,]*,/statInkApiKey\": \"{api_key}\",/g" {path_config_file}""",
		):
			logger.bind(cron=True).debug(f'cli: {cmd}')
			os.system(cmd)

	cmd = f'/home/anyeccc/.deno/bin/deno run -Ar ./s3si.ts -n -p {path_config_file}'
	logger.bind(cron=True).debug(cmd)
	rtn = subprocess.run(cmd.split(' '), stdout=subprocess.PIPE).stdout.decode('utf-8')
	logger.bind(cron=True).debug(f'{user_id} cli: {rtn}')

	battle_cnt = 0
	coop_cnt = 0
	url = ''
	for line in rtn.split('\n'):
		line = line.strip()
		if not line:
			continue
		if 'exported to https://stat.ink' in line:
			if 'salmon3' in line:
				coop_cnt += 1
			else:
				battle_cnt += 1
			url = line.split('to ')[1].split('spl3')[0].split('salmon3')[0][:-1]

	logger.bind(cron=True).debug(f'{user_id} result: {battle_cnt}, {coop_cnt}, {url}')
	if battle_cnt or coop_cnt:
		return battle_cnt, coop_cnt, url
