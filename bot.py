import os
import json
import time
from distutils.version import LooseVersion
import importlib
import pip
from enum import Enum
import logging


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
whitelist = []
currencies = {'bud':'Earbuds', 'ref':'Refined Metal', 'rec':'Reclaimed Metal', 'scrap':'Scrap Metal', 'key':'Mann Co. Supply Crate Key'}
packages = ['steampy', 'requests']
declined_trades = []
past_time = time.time()

logging.basicConfig(filename='trade.log', level=logging.DEBUG,
                    format='[%(asctime)s][%(levelname)s][%(name)s]: %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

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

class TradeOfferStatus(Enum):
    INVALID = 1
    ACTIVE = 2
    ACCEPTED = 3
    EXPIRED = 4
    CANCELED = 6
    INVALID_ITEMS = 8
    WAIT_CONF = 9
    WAIT_SFAC = 10
    ESCROW = 11


class TradeManager:

    def __init__(self, client, conf):
        self._trades = []
        self._pending_trades = []
        self._try_confs = []
        self._declined_trades = []
        self.client = client
        self.conf = conf


    def accept(self, trade):
        try:
            self.client.accept_trade_offer(trade.id)
            return True
        except BaseException as BE:
            logging.warning(f'TRADE ACCEPT ERROR: {type(BE).__name__}: {BE}')
            return False
            

    def check_trades_content(self):
        for trade in range(len(self._pending_trades)-1,-1,-1):
            trade = self._pending_trades[trade]
            sell_value = 0
            buy_value = 0
            for item in trade.items_to_give:
                if item in sell_trades:
                    sell_value += sell_trades[item]

            for item in trade.items_to_receive:
                if item in buy_trades.keys():
                    buy_value += buy_trades[item]

            logging.debug(f'TRADE: {trade.id}\nSELL-VALUE: {sell_value}\tBUY-VALUE: {buy_value}')

            if not buy_value and not sell_value:
                print(f"[TRADE]: This trade has nothing we are looking for! They offered "
                      f"us:\n{str(trade.items_to_receive)}")
                print(f'[TRADE]: For our:\n{str(trade.items_to_give)}')
                self.client.decline_trade_offer(trade.id)
                self._declined_trades.append(trade.id)
                logging.info(f'DECLINED TRADE: {trade.id}\nREASON: Nothing of interest')
                continue

            if sell_value > buy_value:
                response = check_trade(trade, sell_value, 'sell')
            else:
                response = check_trade(trade, buy_value, 'buy')

            if response:
                print(f'[TRADE]: Looks good! They gave us:\n{str(trade.items_to_receive)}')
                print(f'[TRADE]: We gave them:\n{str(trade.items_to_give)}')
                print('[TRADE]: Attempting to accept offer')
                try:
                    logging.info(f"ATTEMPTING TRADE: {trade.id}\nSELL: {sell_value} BUY:{buy_value}\n{trade.trade}")
                    self.accept(trade)
                    self._trades.append(trade)
                except ConfirmationExpected:
                    logging.warning(f'FAILED TO CONFIRM TRADE: {trade.id} (FIRST TRY)')
                    self._try_confs.append(trade.id)
                self._pending_trades.remove(trade)
                self._trades.append(trade)
            else:
                print(f'[TRADE]: No good! They offered us:\n{str(trade.items_to_receive)}')
                print(f'[TRADE]: For our:\n{str(trade.items_to_give)}')
                print('[TRADE]: Declining offer')
                logging.info(f"DECLINING INVALID TRADE: {trade.id}\nSELL: {sell_value} BUY:{buy_value}\n{trade.trade}")
                self.client.decline_trade_offer(trade.id)
                self._declined_trades.append(trade.id)
                self._pending_trades.remove(trade)

    def get_new_trades(self):
        new_trades = client.get_trade_offers()['response']
        logging.debug(str(new_trades))
        for new_trade in new_trades['trade_offers_received']:
            if new_trade['tradeofferid'] not in [t.id for t in self._trades] \
                    or new_trade['tradeofferid'] in self._declined_trades:
                id64 = 76561197960265728 + new_trade['accountid_other']
                trade = Trade(new_trade, id64)
                logging.info(f"FOUND NEW TRADE: {trade.id}")
                if str(id64) in whitelist:
                    print(f"[WHITELIST]: Neat! This trade is whitelisted! Attempting confirmation (STEAM ID:{id64})")
                    logging.info(f'TRADE WHITELISTED ATTEMPTING TRADE: {trade.id}')
                    self.accept(trade)
                    self._trades.append(trade)
                    continue
                print(f'[TRADE]: Found trade (ID: {trade.id})')
                if self._check_partner(trade):
                    if not accept_escrow and trade.escrow:
                        print("[TRADE]: Trade is escrow, declining")
                        logging.info(f'DECLINING ESCROW TRADE: {trade.trade}')
                        self.client.decline_trade_offer(trade.id)
                        self._declined_trades.append(trade.id)
                    else:
                        self._pending_trades.append(trade)


    def _check_partner(self, trade):
        print("[TRADE]: Checking for trade bans for backpack.tf and steamrep.com")
        rJson = requests.get(f"https://backpack.tf/api/users/info/v1?",
                             data={'key':bkey, 'steamids':trade.other_steamid}).json()

        logging.debug(str(rJson))
        if "bans" in rJson['users'][trade.other_steamid].keys():
            if "steamrep_caution" in rJson['users'][trade.other_steamid]['bans'] or \
                            "steamrep_scammer" in rJson['users'][trade.other_steamid]['bans']:
                print("[steamrep.com]: WARNING SCAMMER")
                print('[TRADE]: Ending trade...')
                logging.info(f"DECLINED SCAMMER (ID:{trade.other_steamid})")
                self.client.decline_trade_offer(trade.id)
                self._declined_trades.append(trade.id)
                return False

            print('[steamrep.com]: User is not banned')
            if "all" in rJson['users'][trade.other_steamid]['bans']:
                print('[backpack.tf]: WARNING SCAMMER')
                print('[TRADE]: Ending trade...')
                logging.info(f"DECLINED SCAMMER (ID:{trade.other_steamid})")
                self.client.decline_trade_offer(trade.id)
                self._declined_trades.append(trade.id)
                return False
            print('[backpack.tf]: User is clean')
        print("[backpack.tf/steamrep.com]: User is clean")
        return True


    def check_bad_trades(self):
        for trade_index in range(len(self._trades)-1, -1, -1):
            trade = self._trades[trade_index]
            status = trade.status()
            if status == TradeOfferStatus.INVALID.value:
                print(f'[ERROR]: Trade offer id {trade.id} seems to be invalid')
                self._trades.remove(trade)
                logging.warning(f'TRADE {trade.id} BECAME invalid')
            elif status == TradeOfferStatus.CANCELED.value:
                print(f'[TRADE]: Trade {trade.id} was canceled.')
                self._trades.remove(trade)
                logging.warning(f'TRADE {trade.id} BECAME canceled')
            elif status == TradeOfferStatus.EXPIRED.value:
                print(f'[TRADE]: Trade {trade.id} has expired... How did that happen?')
                self._trades.remove(trade)
                logging.warning(f'TRADE {trade.id} BECAME expired')
            elif status == TradeOfferStatus.INVALID_ITEMS.value:
                print(f'[TRADE]: Items attempting to trade became invalid. {trade.id}')
                self._trades.remove(trade)
                logging.warning(f'TRADE {trade.id} BECAME invalid_items')
            elif status == TradeOfferStatus.ESCROW.value and not accept_escrow:
                print('[ERROR]: Whoops, escrow trade was confirmed. Sorry about that')
                self._trades.remove(trade)
                logging.fatal(f'ACCEPTED ESCROW TRADE')

    def check_good_trades(self):
        for trade_index in range(len(self._trades) - 1, -1, -1):
            trade = self._trades[trade_index]
            status = trade.status()
            if status == TradeOfferStatus.ACCEPTED.value:
                print(f'[TRADE]: Accepted trade {trade.id}')
                self._trades.remove(trade)
                logging.info(f'TRADE {trade.id} WAS ACCEPTED')

        for tradeid in self._try_confs:
            try:
                self.conf.send_trade_allow_request(tradeid)
                print(f'[TRADE]: Accepted trade {tradeid}')
                logging.info(f'TRADE {tradeid} WAS ACCEPTED (after manual confirmation)')
            except ConfirmationExpected:
                logging.debug(f'CONFIRMATION FAILED ON {tradeid}')


class Trade:

    def __init__(self, trade_json:dict, other_steamid:int):
        self.trade = trade_json
        self.escrow = int(trade_json['escrow_end_date'])
        self.items_to_give = self._items_to_give()
        self.items_to_receive = self._items_to_receive()
        self.id = trade_json["tradeofferid"]
        self.other_steamid = str(other_steamid)

    def _items_to_receive(self):
        item_names = []
        for assetID in self.trade['items_to_receive']:
            item_names.append(self.trade['items_to_receive'][assetID]['market_name'])
        return item_names

    def _items_to_give(self):
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

    def status(self):
        trade_json = client.get_trade_offer(self.id)['response']['offer']
        return trade_json['trade_offer_state']

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
    min = 0
    BeyC = budC * bud_price
    maj = (BeyC * key_price) + (keyC * key_price)
    maj_scrap = int(scrapC / 3)
    scrapC -= maj_scrap * 3
    recC += maj_scrap
    maj_rec = int(recC / 3)
    recC -= maj_rec * 3
    refC += maj_rec

    if scrapC % 3:
        if scrapC == 1:
            min += .11
        else:
            min += .22

    if recC % 3:
        if recC == 1:
            min += .33
        else:
            min += .66

    maj += refC

    return maj + min

def check_install(pkg, c, imp=''):
    try:
        importlib.import_module(pkg)
        print(f'[PROGRAM]: Required package is installed {c}/{len(packages)}')
        logging.debug(f"MODUAL {pkg} IS INSTALLED")
    except:
        logging.info("MODUAL {pkg} IS NOT INSTALLED")
        if imp:
            pkg = imp
        print('[PROGRAM]: A required package is not installed, installing...')
        pip.main(['install', pkg])
        print('[PROGRAM]: Installed package! Please restart this program to continue.')
        input('press enter to close program...\n')
        os._exit(0)

def check_trade(trade_obj, items_value, typ):
    curr = trade_obj.sort(typ)
    value = calculate(curr[0], curr[1], curr[2], curr[3], curr[4])
    logging.debug(f"TRADE {trade_obj.id} is a {typ} trade, and is worth {value}, with items being {items_value}")
    if typ == 'sell':
        if value >= items_value:
            return True
        else:
            return False
    else:
        if value <= items_value:
            return True
        else:
            return False

def heartbeat():
    global past_time
    print(f"[HEARTBEAT]: {90 - int(time.time() - past_time)} seconds until can send next heartbeat")
    if int(time.time() - past_time) >= 90:
        p = requests.post(f"https://backpack.tf/api/aux/heartbeat/v1?", data={"token": token, "automatic": "all"})
        if p.status_code != 200:
            print(f'[HEARTBEAT]: Error when sending heartbeat > {p.json()["message"]}')
            logging.warning(f"ERROR SENDING HEARTBEAT: {p.json()['message']}")
        else:
            print("[HEARTBEAT]: Sent heartbeat to backpack.tf")
            logging.info("HEARTBEAT SENT")
            past_time = time.time()

if __name__ == '__main__':
    print(start_text)

    for pkg in packages:
        check_install(pkg, packages.index(pkg)+1, '' if pkg!='backpackpy' else 'backpack.py')

    from steampy.client import SteamClient
    from steampy import confirmation
    from steampy.exceptions import InvalidCredentials, ConfirmationExpected
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
                    logging.warning(f'SETTINGS FILE MISSING {k} VALUE')
                    print(f'[settings.json]: Whoops! You are missing the {k} value')
                    input('press enter to close program...\n')
                    os._exit(1)
            except json.JSONDecodeError:
                logging.warning('INVALID SETTINGS FILE')
                print('[PROGRAM]: Whoops! It would seem that you settings.json folder is invalid!')
                input('press enter to close program...\n')
                os._exit(1)
        logging.debug("LOADED SETTINGS")

    except FileNotFoundError:
        logging.warning("SETTINGS NOT FOUND, CREATING")
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
    conf = None

    try:
        client.login(username, password, 'steamguard.json')
    except json.decoder.JSONDecodeError:
        logging.warning("STEAMGUARD FILE INVALID")
        print('[steamguard.json]: Unable to read file.')
        input('press enter to close program...\n')
        os._exit(1)
    except FileNotFoundError:
        logging.warning("UNABLE TO FIND STEAMGAURD FILE")
        print('[steamguard.json]: Unable to find file.')
        input('press enter to close program...\n')
        os._exit(1)
    except InvalidCredentials:
        logging.info("CREDENTIALS INVALID")
        print('[PROGRAM]: your username and/or password and/or secrets and/or ID is invalid.')
        input('press enter to close program...\n')
        os._exit(1)
    else:
        conf = confirmation.ConfirmationExecutor(
            client.steam_guard['identity_secret'],
            client.steam_guard['steamid'],
            client._session)
        logging.info("CREATED CLIENT AND CONFIRMATION MANAGER")

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
                    logging.warning("TRADE DATA IS IN AN INVALID FORMAT")
                    print(f'[trade.data]: Whoops! Invalid data on line {count}, make sure each line looks like the following,')
                    print('<item market name>, <price (float)>, <type (sell, buy)>')
                    input('press enter to close program...\n')
                    os._exit(1)
                count += 1
            file.seek(0)
            slash_n = '\n'
            logging.info(f'LOADED TRADE DATA: {file.read().replace(slash_n, "   ")}')
    except FileNotFoundError:
        logging.warning("TRADE FILE NOT FOUND")
        print('[trade.data]: Unable to find file.')
        input('press enter to close program...\n')
        os._exit(1)
    print('[PROGRAM]: Finished loading trading data.')

    # #yn = input("Would you like to sync to backpack.tf listings?\n[y/n]: ")
    # #if yn[0].lower() == 'y':
    #     steamid = client.steam_guard['steamid']
    #     steam_inv = requests.get(f'http://steamcommunity.com/inventory/{steamid}/440/2?l=english&count=5000').json()
    #     bp_listings = requests.get("https://backpack.tf/api/classifieds/listings/v1?", data={'token':token}).json()
    #     class_id = False
    #     for classified in bp_listings["listings"]:
    #         asset_id = classified['id']
    #         for item in steam_inv['assets']:
    #             if item['assetid'] == classified['id']:
    #                 class_id = item['classid']
    #         if class_id:
    #             for item in steam_inv['descriptions']:
    #                 if item['classid'] == class_id:
    #                     market_name = item['market_name']
    #         market_type = classified['intent']
    #         price = None

    try:
        with open('whitelist.data', 'r') as file:
            steam_ids = file.read()
            if steam_ids:
                for steam_id in steam_ids.split(','):
                    whitelist.append(steam_id)
        print(f'[WHITELIST]: Whitelist created with the following ids: {whitelist}')
        logging.info(f"LOADED WHITELIST: {whitelist}")
    except FileNotFoundError:
        logging.debug("WHITELIST NOT FOUND")


    print('[PROGRAM]: Obtaining bud and key values from backpack.tf...')
    rJson = requests.get(f'https://backpack.tf/api/IGetCurrencies/v1?key={bkey}').json()['response']
    logging.debug(f"KEY VALUE RESPONSE: {rJson}")
    if rJson['success']:
        key_price = float(rJson['currencies']['keys']['price']['value'])
        bud_price = float(rJson['currencies']['earbuds']['price']['value'])
        print(f'[PROGRAM]: Obtained values! KEY <{key_price} ref>, BUD <{bud_price} keys>.')
        logging.debug("OBTAINED KEY AND BUD VALUES")
    else:
        logging.fatal("FAILED TO OBTAIN KEY AND BUG VALUES")
        print(f'[backpack.tf]: {rJson["message"]}')
        input('press enter to close program...\n')
        os._exit(1)

    print('[PROGRAM]: Everything ready, starting trading.')
    print('[PROGRAM]: Press ctrl+C to close at any time.')

    manager = TradeManager(client, conf)

    while True:
        try:
            heartbeat()
            try:
                manager.get_new_trades()
                print('[TRADE-MANAGER] STEP 1 (get new trades) COMPLETE')
                logging.debug("(STEP 1 COMPLETE)")
            except json.decoder.JSONDecodeError:
                print("[PROGRAM]: Unexpected error, taking a break (10 seconds).")
                time.sleep(10)
                print('Starting again...')
                continue

            manager.check_trades_content()
            print('[TRADE-MANAGER]: STEP 2 (check new trades) COMPLETE')
            logging.debug("(STEP 2 COMPLETE)")
            manager.check_bad_trades()
            print('[TRADE-MANAGER]: STEP 3 (check for trades gone bad) COMPLETE')
            logging.debug("(STEP 3 COMPLETE)")
            manager.check_good_trades()
            print('[TRADE-MANAGER]: STEP 4 (check for successful trades) COMPLETE')
            logging.debug("(STEP 4 COMPLETE)")
            print('[PROGRAM]: Cooling down... (10)')

        except InterruptedError:
            os._exit(0)

        except BaseException as BE:
            print(f'[ERROR]: {type(BE).__name__}: {BE}')
            logging.warning(f"UNEXPECTED ERROR: {type(BE).__name__}: {BE}")

        time.sleep(10)
