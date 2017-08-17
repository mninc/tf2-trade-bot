import os
import sys
import json
import time
from distutils.version import LooseVersion
import importlib
import pip

apikey = ''
password = ''
username = ''
bkey = ''
buy_trades = {}
sell_trades = {}
items = {}
key_price = 0
bud_price = 0
escrow = None
currencies = {'bud':'Earbuds', 'ref':'Refined Metal', 'rec':'Reclaimed Metal', 'scrap':'Scrap Metal', 'key':'Mann Co. Supply Crate Key'}
packages = ['steampy', 'requests', 'bs4', 'backpackpy']
declined_trades = []
past_time = time.time()

start_text = """
  _____    _____  ____         _____    ____        _      ____  U _____ u       ____     U  ___ u _____   
 |_ " _|  |" ___||___"\       |_ " _|U |  _"\ u U  /"\  u |  _"\ \| ___"|/    U | __")u    \/"_ \/|_ " _|  
   | |   U| |_  uU __) |        | |   \| |_) |/  \/ _ \/ /| | | | |  _|"       \|  _ \/    | | | |  | |    
  /| |\  \|  _|/ \/ __/ \      /| |\   |  _ <    / ___ \ U| |_| |\| |___        | |_) |.-,_| |_| | /| |\   
 u |_|U   |_|    |_____|u     u |_|U   |_| \_\  /_/   \_\ |____/ u|_____|       |____/  \_)-\___/ u |_|U   
 _// \\\_  )(\\\,- <<  //       _// \\\_  //   \\\_  \\\    >>  |||_   <<   >>      _|| \\\_       \\\   _// \\\_  
(__) (__)(__)(_/(__)(__)     (__) (__)(__)  (__)(__)  (__)(__)_) (__) (__)    (__) (__)     (__) (__) (__) 

Created by: Zwork101    Github: https://github.com/Zwork101    Steam: https://steamcommunity.com/id/ZWORK101\n
"""
  
def check_for_updates():
    with open('__version__', 'r') as file:
        curr_version = file.read()
    r = requests.get('https://raw.githubusercontent.com/Zwork101/tf2-trade-bot/master/__version__')
    new_version = r.text
    if LooseVersion(new_version) > LooseVersion(curr_version):
        print('[PROGRAM]: New version is available, would you like to install?')
        yn = input('[y/n]: ')
        if yn[0].lower() == 'y':
            print('[Installer]: Starting installation...', end='')
            bot_update = requests.get('https://raw.githubusercontent.com/Zwork101/tf2-trade-bot/master/bot.py')
            with open('__version__', 'w') as file:
                file.write(new_version)
                print('.', end='')
            with open('bot.py', 'w') as file:
                file.write(bot_update.text)
                print('.')
            print('Update complete! Restart now.')
            input('press enter to close program...\n')
            os._exit(0)

def calculate(scrapC, recC, refC, keyC, budC):
    BeyC = budC * bud_price
    refK = (BeyC * key_price) + (keyC * key_price)
    totalR = (scrapC * .11) + (recC * .33) + refC
    totalR += refK
    return totalR

def check_install(pkg, c, imp=''):
    try:
        print(f"Checking install on {pkg}")
        importlib.import_module(pkg)
        print(f'[PROGRAM]: Required package is installed {c}/4')
    except:
        if imp:
            pkg = imp
        print('[PROGRAM]: A required package is not installed, installing...')
        pip.main(['install', pkg])
        print('[PROGRAM]: Installed package! Please restart this program to continue.')
        input('press enter to close program...\n')
        os._exit(0)

def check_trade(cli_obj, trade_obj, items_value, id, typ):
    curr = trade_obj.sort(typ)
    value = calculate(curr[0], curr[1], curr[2], curr[3], curr[4])
    if typ == 'sell':
        if value >= items_value:
            print(f'[TRADE]: Looks good! They gave us:\n{str(trade_obj.items_to_receive)}')
            print(f'[TRADE]: We gave them:\n{str(trade_obj.items_to_give)}')
            cli_obj.accept_trade_offer(id)
            return True
        else:
            print(f'[TRADE]: No good! They offered us:\n{str(trade_data.items_to_receive)}')
            print(f'[TRADE]: For our:\n{str(trade_data.items_to_give)}')
            cli_obj.decline_trade_offer(id)
            declined_trades.append(id)
        return False
    else:
        if value >= items_value:
            print(f'[TRADE]: Looks good! They gave us:\n{str(trade_obj.items_to_receive)}')
            print(f'[TRADE]: We gave them:\n{str(trade_obj.items_to_give)}')
            cli_obj.accept_trade_offer(id)
            return True
        else:
            print(f'[TRADE]: No good! They offered us:\n{str(trade_data.items_to_receive)}')
            print(f'[TRADE]: For our:\n{str(trade_data.items_to_give)}')
            cli_obj.decline_trade_offer(id)
            declined_trades.append(id)
        return False

class Parser:

    def __init__(self, trade_json:dict):
        self.trade = trade_json
        self.escrow = bool(trade_json['escrow_end_date'])
        self.items_to_receive = self.items_to_give()
        self.items_to_give = self.items_to_receive()

    def _items_to_give(self):
        item_names = []
        for assetID in self.trade['items_to_receive']:
            item_names.append(self.trade['items_to_receive'][assetID]['market_name'])
        return item_names

    def _items_to_receive(self):
        item_names = []
        for assetID in self.trade['items_to_give']:
            item_names.append(self.trade['items_to_give'][assetID]['market_name'])
        return item_names

    def sort(self, typ):
        curr = [0, 0, 0, 0, 0]
        if typ == 'sell':
            for item in self.items_to_receive:
                if item == currencies['scrap']:
                    curr[0] += 1
                elif item == currencies['rec']:
                    curr[1] += 1
                elif item == currencies['ref']:
                    curr[2] += 1
                elif item == currencies['key']:
                    curr[3] += 1
                elif item == currencies['bud']:
                    curr[4] += 1
        else:
            for item in self.items_to_give:
                if item == currencies['scrap']:
                    curr[0] += 1
                elif item == currencies['rec']:
                    curr[1] += 1
                elif item == currencies['ref']:
                    curr[2] += 1
                elif item == currencies['key']:
                    curr[3] += 1
                elif item == currencies['bud']:
                    curr[4] += 1
        return curr

if __name__ == '__main__':
    print(start_text)

    for pkg in packages:
        check_install(pkg, packages.index(pkg)+1, '' if pkg!='backpackpy' else 'backpack.py')

    from bs4 import BeautifulSoup
    from steampy.client import SteamClient
    from steampy.exceptions import InvalidCredentials
    #from backpackpy import listings
    import requests

    check_for_updates()

    try:
        with open('settings.json', 'r') as cfg:
            try:
                data = json.load(cfg)
                try:
                    apikey, password, username, bkey, accept_escrow = data['apikey'],\
                                            data['password'], data['username'], data['bkey'], data['accept_escrow']
                    token = requests.get(f"https://backpack.tf/api/aux/token/v1?key={bkey}").json()['token']
                except KeyError as k:
                    print(f'[settings.json]: Whoops! You are missing the {k} value')
                    input('press enter to close program...\n')
                    os._exit(1)
            except json.JSONDecodeError:
                print('[PROGRAM]: Whoops! It would seem that you settings.json folder is invalid!')
                input('press enter to close program...\n')
                os._exit(1)

    except FileNotFoundError:
        print('[PROGRAM]: File settings.json not found! Would you like to make one?')
        yn = input('[y/n]: ')
        if yn[0].lower() == 'y':
            apikey = input('[settings.json]: enter your steam API key. (https://steamcommunity.com/dev/apikey)\n')
            password = input('[settings.json]: enter your password. \n')
            username = input('[settings.json]: enter your username. \n')
            bkey = input('[settings.json]: enter your backpack.tf API key. (https://backpack.tf/api/register)\n')
            accept_escrow = input('[settings.json]: accept escrow trades? (0 for no, 1 for yes)\n')
            print('[PROGRAM]: Writing data to file...')
            with open('settings.json', 'w') as file:
                json.dump({'apikey':apikey, 'password':password, 'username':username, 'bkey':bkey,
                           "accept_escrow":accept_escrow}, file)
            print('[PROGRAM]: Wrote to file')
        else:
            print("[PROGRAM]: Can't run without user information.")
            input('press enter to close program...\n')
            os._exit(1)

    client = SteamClient(apikey)
    try:
        client.login(username, password, 'steamguard.json')
    except json.decoder.JSONDecodeError:
        print('[steamguard.json]: Unable to read file.')
        input('press enter to close program...\n')
        os._exit(1)
    except FileNotFoundError:
        print('[steamguard.json]: Unable to find file.')
        input('press enter to close program...\n')
        os._exit(1)
    except InvalidCredentials:
        print('[PROGRAM]: your username and/or password and/or secrets and/or ID is invalid.')
        input('press enter to close program...\n')
        os._exit(1)

    print(f'[PROGRAM]: Connected to steam! Logged in as {username}')
    try:
        with open('trade.data', 'r') as file:
            count = 1
            for line in file:
                try:
                    item, price, typ = line.split(',')
                    item, price, typ = item.strip(), price.strip(), typ.strip()
                    if typ[0].lower() == 's':
                        sell_trades[item] = float(price)
                    else:
                        buy_trades[item] = float(price)
                except ValueError:
                    print(f'[trade.data]: Whoops! Invalid data on line {count}, make sure each line looks like the following,')
                    print('<item market name>, <price (float)>, <type (sell, buy)>')
                    input('press enter to close program...\n')
                    os._exit(1)
                count += 1
    except FileNotFoundError:
        print('[trade.data]: Unable to find file.')
        input('press enter to close program...\n')
        os._exit(1)
    print('[PROGRAM]: Finished loading trading data.')

    print('[PROGRAM]: Obtaining bud and key values from backpack.tf...')
    rJson = requests.get(f'https://backpack.tf/api/IGetCurrencies/v1?key={bkey}').json()['response']
    if rJson['success']:
        key_price = float(rJson['currencies']['keys']['price']['value'])
        bud_price = float(rJson['currencies']['earbuds']['price']['value'])
        print(f'[PROGRAM]: Obtained values! KEY <{key_price} ref>, BUD <{bud_price} keys>.')
    else:
        print(f'[backpack.tf]: {rJson["message"]}')
        input('press enter to close program...\n')
        os._exit(1)

    print('[PROGRAM]: Everything ready, starting trading.')
    print('[PROGRAM]: Press ctrl+C to close at any time.')

    while True:
        try:
            print(f"[HEARTBEAT]: {90 - int(time.time() - past_time)} seconds until can send next heartbeat")
            if int(time.time() - past_time) >= 90:
                p = requests.post(f"https://backpack.tf/api/aux/heartbeat/v1?", data={"token":token, "automatic":"all"})
                if p.status_code is not 200:
                    print(f'[HEARTBEAT]: Error when sending heartbeat > {p.json()["message"]}')
                else:
                    print("[HEARTBEAT]: Sent heartbeat to backpack.tf")
                    past_time = time.time()
            try:
                trades = client.get_trade_offers()
                print('got trade offers')
            except json.decoder.JSONDecodeError:
                print("[PROGRAM]: Unexpected error, taking a break (10 seconds).")
                time.sleep(10)
                print('Starting again...')
                continue

            for trade in trades['response']['trade_offers_received']:
                trade_id = trade['tradeofferid']
                if trade_id not in declined_trades:
                    other_id = trade['accountid_other']
                    declined = False
                    id64 = 76561197960265728 + other_id
                    print(f'[TRADE]: Found trade (ID: {trade_id})')
                    print("[TRADE]: Checking for trade bans for backpack.tf and steamrep.com")
                    rJson = requests.get(f"https://backpack.tf/api/users/info/v1?key={bkey}&steamids={id64}").json()
                    if "bans" in rJson['users'][str(id64)].keys():
                        if "steamrep_caution" in rJson['users'][str(id64)]['bans'] or \
                                "steamrep_scammer" in rJson['users'][str(id64)]['bans']:
                            print("[steamrep.com]: WARNING SCAMMER")
                            print('[TRADE]: Ending trade...')
                            client.decline_trade_offer(trade_id)
                            declined_trades.append(trade_id)
                            print('Looking for trades...')
                            continue
                        print('[steamrep.com]: User is not banned')
                        if "all" in rJson['users'][str(id64)]['bans']:
                            print('[backpack.tf]: WARNING SCAMMER')
                            print('[TRADE]: Ending trade...')
                            client.decline_trade_offer(trade_id)
                            declined_trades.append(trade_id)
                            print('Looking for trades...')
                            continue
                    print("[TRADE]: User is safe to trade with")
                    trade_data = Parser(trade)
                    if not bool(escrow) and trade_data.escrow:
                        declined_trades.append(trade_id)
                        client.decline_trade_offer(trade_id)
                        print("[TRADE]: This user's trade is escrow, declined")
                        continue
                    sell_value = 0

                    for item in trade_data.items_to_give:
                        print(item)
                        if item in sell_trades:
                            sell_value += sell_trades[item]

                    if not sell_value:
                        buy_value = 0
                        for item in trade_data.items_to_receive:
                            if item in buy_trades.keys():
                                buy_value += buy_trades[item]

                        if not buy_value:
                            print(f"[TRADE]: This trade has nothing we are looking for! They offered "
                                  f"us:\n{str(trade_data.items_to_receive)}")
                            print(f'[TRADE]: For our:\n{str(trade_data.items_to_give)}')
                            client.decline_trade_offer(trade_id)
                            declined_trades.append(trade_id)

                        else:
                            check_trade(client, trade_data, buy_value, trade_id, 'buy')

                    else:
                        check_trade(client, trade_data, sell_value, trade_id, 'sell')

            time.sleep(10)

        except InterruptedError:
            os._exit(0)

        except BaseException as BE:
            print(f'[PROGRAM]: {BE}')
