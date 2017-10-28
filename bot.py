import os
import sys
import json
import time
from distutils.version import LooseVersion
import importlib
import pip
from enum import Enum
import logging
import csv
import subprocess

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
declined_trades = None
past_time = time.time()
start_time = time.time()

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

    """
    The manager for trades. This will be used to organize trades and keep everything from falling apart.
    Prams: client (steampy.client.SteamClient object) and conf (steampy.confirmation.ConfirmationExecutor)
    Public values: client and conf (see above)
    Public functions: accept, check_trades_content, get_new_trades, check_good_trades, check_bad_trades
    """

    def __init__(self, client, conf):
        self._trades = []
        self._pending_trades = []
        self._try_confs = []
        self._declined_trades = []
        self.client = client
        self.conf = conf


    def decline(self, trade):
        if decline_trades:
            self.client.decline_trade_offer(trade.id)
        if trade.id not in self._declined_trades:
            self._declined_trades.append(trade.id)


    def accept(self, trade):
        """
        The accept function handles accepting trades. This is important, because different errors could occur.
        Prams: (self), trade (Trade object)
        Output: None
        """
        try:
            self.client.accept_trade_offer(trade.id)
            return True
        except BaseException as BE:
            if BE.__class__ == KeyError:
                print(f'ERROR: Issue confirming trade: {trade.id}, trying again')
                #self._trades.remove(trade)
                self._pending_trades.append(trade)
            logging.warning(f'TRADE ACCEPT ERROR: {type(BE).__name__}: {BE}')
            return False


    def check_trades_content(self):
        """
        This will check the current trades in self._pending_trades and decide if they are correct or not
        Then it will move the good trades to self._declined_trades and self._trades after acccepting/declining
        trade offers.
        Prams: (self)
        Output: None
        """
        for trade in range(len(self._pending_trades)-1,-1,-1):
            trade = self._pending_trades[trade]
            sell_value = 0
            buy_value = 0
            extra_sell = []
            extra_buy = []
            if not trade.items_to_give:
                self._pending_trades.remove(trade)
                self._trades.append(trade)
                self.accept(trade)
                continue
            exit_trade = False
            for item in trade.items_to_give:
                if not exit_trade:
                    if item not in sell_trades:
                        if item in currencies.values():
                            extra_sell.append(item)
                        else:
                            print('[TRADE]: Unknown item we\'re giving, declining')
                            self.decline(trade)
                            self._pending_trades.remove(trade)
                            logging.info("DECLINING TRADE WITH UN-KNOWN ITEM")
                            exit_trade = True
                    else:
                        sell_value = add_values(float(sell_trades[item]), float(sell_value))

            if exit_trade:
                continue

            for item in trade.items_to_receive:
                if item in buy_trades:
                    buy_value = add_values(float(buy_trades[item]), float(buy_value))
                elif item in currencies.values():
                    extra_buy.append(item)

            sell_curr = sort(extra_sell)
            buy_curr = sort(extra_buy)
            sell_value += calculate(sell_curr[0], sell_curr[1], sell_curr[2], sell_curr[3], sell_curr[4])
            buy_value += calculate(buy_curr[0], buy_curr[1], buy_curr[2], buy_curr[3], buy_curr[4])

            if sell_value <= buy_value:
                print(f'[TRADE]: Looks good! They gave us:\n{str(trade.items_to_receive)}')
                print(f'[TRADE]: We gave them:\n{str(trade.items_to_give)}')
                print('[TRADE]: Attempting to accept offer')
                try:
                    logging.info(f"ATTEMPTING TRADE: {trade.id}\nSELL: {sell_value} BUY:{buy_value}\n{trade.trade}")
                    self._trades.append(trade)
                    self._pending_trades.remove(trade)
                    self.accept(trade)
                except ConfirmationExpected:
                    logging.warning(f'FAILED TO CONFIRM TRADE: {trade.id} (FIRST TRY)')
                    self._try_confs.append(trade.id)
            else:
                print(f'[TRADE]: No good! They offered us:\n{str(trade.items_to_receive)}')
                print(f'[TRADE]: For our:\n{str(trade.items_to_give)}')
                print('[TRADE]: Declining offer')
                logging.info(f"DECLINING INVALID TRADE: {trade.id}\nSELL: {sell_value} BUY:{buy_value}\n{trade.trade}")
                self.decline(trade)
                self._pending_trades.remove(trade)


    def get_new_trades(self):
        """
        Collects new trades, will compare them to current trades to ensure they are new. Accepts if the sender
        is whitelisted, delcines if the user is a scammer or escrow. If not, moved it to
        self._pending_trades (list)
        Prams: (self)
        Output: None
        """
        new_trades = client.get_trade_offers()['response']
        #logging.debug(new_trades)
        for new_trade in new_trades['trade_offers_received']:
            if (not new_trade['tradeofferid'] in [t.id for t in self._trades]) \
                    or (new_trade['tradeofferid'] in self._declined_trades):
                id64 = 76561197960265728 + new_trade['accountid_other']
                trade = Trade(new_trade, id64)
                logging.info(f"FOUND NEW TRADE: {trade.id}")
                if str(id64) in whitelist:
                    print(f"[WHITELIST]: Neat! The user sending this trade is whitelisted! Attempting confirmation (STEAM ID:{id64})")
                    logging.info(f'TRADE WHITELISTED ATTEMPTING TRADE: {trade.id}')
                    self.accept(trade)
                    self._trades.append(trade)
                    continue
                print(f'[TRADE]: Found trade (ID: {trade.id})')
                if self._check_partner(trade):
                    if not accept_escrow and trade.escrow:
                        print("[TRADE]: Trade is escrow, declining")
                        logging.info(f'DECLINING ESCROW TRADE: {trade.trade}')
                        self.decline(trade)
                    else:
                        self._pending_trades.append(trade)


    def _check_partner(self, trade):
        """
        To check if the user is a scammer from backpack.tf and steamrep. This uses the backpack.tf API.
        The API will supply the steamrep stats for the user. If the user is a scammer, it
        will decline the trade and move it to self._declined_trades.
        Prams: (self), trade (Trade object)
        Output: None
        """
        print("[TRADE]: Checking for trade bans on backpack.tf and steamrep.com")
        rJson = requests.get(f"https://backpack.tf/api/users/info/v1?",
                             data={'key':bkey, 'steamids':trade.other_steamid}).json()

        logging.debug(str(rJson))
        if "bans" in rJson['users'][trade.other_steamid].keys():
            if "steamrep_caution" in rJson['users'][trade.other_steamid]['bans'] or \
                            "steamrep_scammer" in rJson['users'][trade.other_steamid]['bans']:
                print("[steamrep.com]: SCAMMER")
                print('[TRADE]: Ending trade...')
                logging.info(f"DECLINED SCAMMER (ID:{trade.other_steamid})")
                self.decline(trade)
                return False

            print('[steamrep.com]: User is not banned')
            if "all" in rJson['users'][trade.other_steamid]['bans']:
                print('[backpack.tf]: SCAMMER')
                print('[TRADE]: Ending trade...')
                logging.info(f"DECLINED SCAMMER (ID:{trade.other_steamid})")
                self.decline(trade)
                return False
            print('[backpack.tf]: User is clean')
        print("[backpack.tf/steamrep.com]: User is clean")
        return True


    def check_bad_trades(self):
        """
        Looks at the current trades in self._trades and checks if the trade has become invalid (eg
        if the trade was cancled). It will remove it from trades and report what happened to the user
        Prams: (self)
        Output: None
        """
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
        """
        This method does 2 things. The first thing it does is check to see if trades have been accepted.
        If they have, they will be removed from self._trades and will report that the trade was accepted.
        The second thing is to try and confirm trades that are having issues confirming. If it was confirmed,
        it will be removed from self._try_confs, and report to user it was confirmed.
        Prams: (self)
        Output: None
        """
        for trade_index in range(len(self._trades) - 1, -1, -1):
            trade = self._trades[trade_index]
            status = trade.status()
            if status == TradeOfferStatus.ACCEPTED.value:
                print(f'[TRADE]: Accepted trade {trade.id}')
                self._trades.remove(trade)
                logging.info(f'TRADE {trade.id} WAS ACCEPTED')


    def confirm_check(self):
        if confirm_settings == 'all':
            logging.debug('ACCEPTING EVERYTHING')
            for confirmation in self.conf._get_confirmations():
                self.conf._send_confirmation(confirmation)
                logging.info(f'SENT CONFIRMATION FOR CONF WITH ID OF {confirmation.id}')
        elif confirm_settings == 'trade':
            for tradeid in self._try_confs:
                try:
                    self.conf.send_trade_allow_request(tradeid)
                    print(f'[TRADE]: Accepted trade {tradeid}')
                    logging.info(f'TRADE {tradeid} WAS ACCEPTED (after manual confirmation)')
                    self._try_confs.remove(tradeid)
                except ConfirmationExpected:
                    logging.debug(f'CONFIRMATION FAILED ON {tradeid}')


class Trade:

    """
    This is an object mainly to store data about a trade, and make it easy to access. It can also
    the currency in the trade and fetch the status of the trade.
    Prams: trade_json (dict), other_steamid (str)
    Public values: self.trade (dict), self.escrow (int), self.items_to_give (list), self.items_to_receive (list),
    self.id (int/str), self.other_steamid (str)
    Public functions: sort, status
    """

    def __init__(self, trade_json:dict, other_steamid:int):
        self.trade = trade_json
        self.escrow = int(trade_json['escrow_end_date'])
        self.items_to_give = self._items_to_give()
        self.items_to_receive = self._items_to_receive()
        self.id = trade_json["tradeofferid"]
        self.other_steamid = str(other_steamid)

    def _items_to_receive(self):
        """
        Adds all items to self.items_to_receive as their market name. Should only be used in initialization.
        Prams: (self)
        Output: item_names (list)
        """
        item_names = []
        for assetID in self.trade['items_to_receive']:
            item_names.append(self.trade['items_to_receive'][assetID]['market_name'])
        return item_names

    def _items_to_give(self):
        """
        Adds all items to self.items_to_give as their market name. Should only be used in initialization.
        Prams: (self)
        Output: item_names (list)
        """
        item_names = []
        for assetID in self.trade['items_to_give']:
            item_names.append(self.trade['items_to_give'][assetID]['market_name'])
        return item_names

    def sort(self, typ):
        """
        Counts the amount of a currency type there is in one side of the trade. "sort" is sort 
        of misleading (see what I did there), it just counts how many scraps, recs, ref, keys and
        buds there are.
        Prams: (self), type (str)
        Output: curr (list)
        """
        if typ == 'sell':
            return sort(self.items_to_receive)
        else:
            return sort(self.items_to_give)

    def status(self):
        """
        Fetches the status of the trade from steam. This way we can get live data.
        Prams: (self)
        Output: trade_json['trade_offer_state'] (int/str)
        """
        try:
            trade_json = client.get_trade_offer(self.id)['response']['offer']
        except KeyError:
            #If key error, the trade doesn't exist anymore. If so, it's invalid
            trade_json = {'trade_offer_state':1}
        return trade_json['trade_offer_state']
      
def add_values(v1, v2):
    v1_rem, v2_rem = int(str(v1).split('.')[1]), int(str(v2).split('.')[1])
    ref = int(v1) + int(v2)
    
    v1_rec, v2_rec = v1_rem // 33, v2_rem // 33
    v1_rem, v2_rem = v1_rem - v1_rec * 33, v2_rem - v2_rec * 33
    
    srp_added = v1_rem + v2_rem
    v1_rec += srp_added // 33
    srp_added -= (srp_added // 33) * 33
    
    rec_added = v1_rec + v2_rec
    ref += rec_added // 3
    rec_added -= (rec_added // 3) * 3
    
    return float(str(ref) + '.' + str(rec_added*33 + srp_added))

def sort(items:list):
    curr = [0,0,0,0,0]
    for item in items:
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

def check_for_updates():
    with open('__version__', 'r') as file:
        curr_version = file.read()
    r = requests.get('https://raw.githubusercontent.com/Zwork101/tf2-trade-bot/master/__version__')
    new_version = r.text
    if LooseVersion(new_version) > LooseVersion(curr_version):
        print('[PROGRAM]: A new version is available, would you like to install?')
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
    #For each currency, add it using add_values function
    total_value = 0.0
    for scrap in range(scrapC):
        total_value = add_values(total_value, .11)
    for rec in range(recC):
        total_value = add_values(total_value, .33)
    for ref in range(refC):
        total_value = add_values(total_value, 1.0)
    for key in range(keyC):
        total_value = add_values(total_value, float(key_price))
    for bud in range(budC):
        total_value = add_values(total_value, float(bud_price))
    return total_value

def check_install(pkg, c, imp=''):
    try:
        importlib.import_module(pkg)
        print(f'[PROGRAM]: Required package is installed {c}/{len(packages)}')
        logging.debug(f"MODULE {pkg} IS INSTALLED")
    except:
        logging.info(f"MODULE {pkg} IS NOT INSTALLED")
        if imp:
            pkg = imp
        print('[PROGRAM]: A required package is not installed, installing...')
        pip.main(['install', pkg])
        print('[PROGRAM]: Installed package! Please restart this program to continue.')
        input('press enter to close program...\n')
        os._exit(0)

# def check_trade(trade_obj, items_value, typ):
#     curr = trade_obj.sort(typ)
#     value = calculate(curr[0], curr[1], curr[2], curr[3], curr[4])
#     if typ == 'sell':
#         b_curr = trade_obj.sort('buy')
#         items_value += calculate(b_curr[0], b_curr[1], b_curr[2], b_curr[3], b_curr[4])
#     else:
#         s_curr = trade_obj.sort('sell')
#         items_value += calculate(s_curr[0], s_curr[1], s_curr[2], s_curr[3], s_curr[4])
#
#     logging.debug(f"TRADE {trade_obj.id} is a {typ} trade, and is worth {value}, with items being {items_value}")
#     if typ == 'sell':
#         if value >= items_value:
#             return True
#         else:
#             return False
#     else:
#         if value <= items_value:
#             return True
#         else:
#             return False

def heartbeat():
    global past_time
    print(f"[HEARTBEAT]: ~{90 - int(time.time() - past_time)} seconds until next heartbeat")
    if int(time.time() - past_time) >= 90:
        p = requests.post(f"https://backpack.tf/api/aux/heartbeat/v1?", data={"token": token, "automatic": "all"})
        if p.status_code != 200:
            print(f'[HEARTBEAT]: Error when sending heartbeat: {p.json()["message"]}')
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
                    decline_trades = data.get('decline_trades', 1)
                    confirm_settings = data.get('confirm_options', 'trades')
                except KeyError as k:
                    logging.warning(f'SETTINGS FILE MISSING {k} VALUE')
                    print(f'[settings.json]: Whoops! You are missing the {k} value')
                    input('Press enter to close program...\n')
                    os._exit(1)
            except json.JSONDecodeError:
                logging.warning('INVALID SETTINGS FILE')
                print('[PROGRAM]: Whoops! It would seem that you settings.json file is invalid!')
                input('press enter to close program...\n')
                os._exit(1)
        logging.debug("LOADED SETTINGS")

    except FileNotFoundError:
        logging.warning("SETTINGS NOT FOUND, CREATING")
        print('[PROGRAM]: File settings.json not found! Would you like to make one?')
        yn = input('[y/n]: ')
        if yn[0].lower() == 'y':
            apikey = input('[settings.json]: Enter your steam API key. (https://steamcommunity.com/dev/apikey)\n')
            password = input('[settings.json]: Enter your password. \n')
            username = input('[settings.json]: Enter your username. \n')
            bkey = input('[settings.json]: Enter your backpack.tf API key. (https://backpack.tf/api/register)\n')
            accept_escrow = input('[settings.json]: Accept escrow trades? (0 for no, 1 for yes)\n')
            print('[PROGRAM]: Writing data to file...')
            with open('settings.json', 'w') as file:
                json.dump({'apikey':apikey, 'password':password, 'username':username, 'bkey':bkey,
                           "accept_escrow":accept_escrow}, file)
            print('[PROGRAM]: Wrote to file')
        else:
            print("[PROGRAM]: Can't run without user information.")
            input('Press enter to close program...\n')
            os._exit(1)

    client = SteamClient(apikey)
    conf = None

    print('[PROGRAM]: Obtaining bud and key values from backpack.tf...')
    rJson = requests.get(f'https://backpack.tf/api/IGetCurrencies/v1?key={bkey}').json()['response']
    logging.debug(f"KEY VALUE RESPONSE: {rJson}")
    if rJson['success']:
        key_price = rJson['currencies']['keys']['price']['value']
        bud_price = rJson['currencies']['earbuds']['price']['value']
        print(f'[PROGRAM]: Obtained values! KEY <{key_price} ref>, BUD <{bud_price} keys>.')
        logging.debug("OBTAINED KEY AND BUD VALUES")
    else:
        logging.fatal("FAILED TO OBTAIN KEY AND BUG VALUES")
        print(f'[backpack.tf]: {rJson["message"]}')
        input('Press enter to close program...\n')
        os._exit(1)

    try:
        client.login(username, password, 'steamguard.json')
    except json.decoder.JSONDecodeError:
        logging.warning("STEAMGUARD FILE INVALID")
        print('[steamguard.json]: Unable to read file.')
        input('Press enter to close program...\n')
        os._exit(1)
    except FileNotFoundError:
        logging.warning("UNABLE TO FIND STEAMGAURD FILE")
        print('[steamguard.json]: Unable to find file.')
        input('Press enter to close program...\n')
        os._exit(1)
    except InvalidCredentials:
        logging.info("CREDENTIALS INVALID")
        print('[PROGRAM]: Your username, password, ID and/or secrets are invalid.')
        input('Press enter to close program...\n')
        os._exit(1)
    else:
        conf = confirmation.ConfirmationExecutor(
            client.steam_guard['identity_secret'],
            client.steam_guard['steamid'],
            client._session)
        logging.info("CREATED CLIENT AND CONFIRMATION MANAGER")

    print(f'[PROGRAM]: Connected to steam! Logged in as {username}')
    try:
        with open('trade.csv', 'r') as file:
            reader = csv.DictReader(file)
            count = 1
            fails = []
            for row in reader:
                count += 1
                try:
                    if row['type'].strip()[0].lower() == 's':
                        p = row['price'].split('.')
                        p = [int(i) for i in p]
                        price = calculate(p[0], p[1], p[2], p[3], p[4])
                        sell_trades[row['item_name'].strip().replace("$$", ",")] = price
                    elif row['type'].strip()[0].lower() == 'b':
                        p = row['price'].split('.')
                        p = [int(i) for i in p]
                        price = calculate(p[0], p[1], p[2], p[3], p[4])
                        buy_trades[row['item_name'].strip().replace("$$", ",")] = price
                except AttributeError:
                    fails.append(count)
            logging.info(f'LOADED TRADE DATA: BUY: {buy_trades} SELL: {sell_trades}')
    except FileNotFoundError:
        logging.warning("TRADE FILE NOT FOUND")
        print('[trade.data]: Unable to find file.')
        input('Press enter to close program...\n')
        os._exit(1)
    print(f'[CSV]: Failed to load these lines: {fails}')
    print('[PROGRAM]: Finished loading trading data.')
    # yn = input("Would you like to sync to backpack.tf listings?\n[y/n]: ")
    # if yn[0].lower() == 'y':
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
    #         ref, keys = classified['currencies']['metal'], classified['currencies']['keys']
    #         sep = str(ref).split('.')
    #         if len(sep) == 2:
    #             price = calculate(int(sep[0])/11, 0, int(sep[0]), keys, 0)
    #         else:
    #             price = calculate(0, 0, int(ref), keys, 0)
    #         if market_type:
    #             sell_trades[market_name] = price
    #         else:
    #             buy_trades[market_name] = price
    # print(buy_trades)
    # print(sell_trades)
    # os._exit(0)

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

    print('[PROGRAM]: Everything ready, starting trading.')
    print('[PROGRAM]: Press Ctrl+C to close at any time.')

    manager = TradeManager(client, conf)

    while True:
        if time.time() - start_time >= 3600:
            pass
            #subprocess.call(["python", os.path.join(sys.path[0], __file__)] + sys.argv[1:])
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
            manager.confirm_check()
            print('[TRADE-MANAGER]: STEP 5 (check confirmations) COMPLETE')
            logging.debug("(STEP 5 COMPLETE)")
            print('[PROGRAM]: Cooling down... (10)')

        except InterruptedError:
            os._exit(0)

        except BaseException as BE:
            print(f'[ERROR]: {type(BE).__name__}: {BE}')
            logging.warning(f"UNEXPECTED ERROR: {type(BE).__name__}: {BE}")

        time.sleep(10)
