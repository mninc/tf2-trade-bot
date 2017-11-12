# the TF2 trade bot!
This is a steam trade bot that trades TF2 items, automatically! Easy to setup, for non-developers!

# Installation
If you have "git" installed, you can just type
```git
git clone https://github.com/Zwork101/tf2_trade_bot.git
``` 
otherwise, just download the zip. Make sure you keep every file in the same folder
# Setup
You will need the language python3.6 or greater. If you don't have python installed, you can find the download [here](https://www.python.org/).
Each file has a description in this repo, to find out what you should do. You can ignore bot.py however, that doesn't need changing :P
If you need a more in-depth setup guide, click [here](#in-depth-setup).

# Running 
If you are here, you have added your ID and secrets to steamguard.json, password, username and api keys to settings.json, and filled out trade.data with whatever you wanted to sell or buy. You can now run bot.py! You *will* have to install some packages, but the bot will handle that part for you! Just restart the program when it tells you to. If you're having truoble with somthing or if you come across an error, make an issue in this repo and I'll respond asap!

# Credits
This bot was made completely by me, Zwork101. It is under the MIT license. I am not responsible for any loss you might receive whilst using this program. If you enjoyed this bot, steam item donations are accepted!

### With love, Zwork101

# to-do list
 * ~~Add catch for when items become unavailable to trade~~
 * Neaten and make code more efficient
 * ~~change current input to csv for trade.data~~
 * add 2 seperate logs, one for debugging, one for trades
 * add ability to sync bot's trades with backpack.tf
 * add GUI?
 
 
 # In-depth setup
 You'll need python 3.6 to use this bot, download it [here](https://www.python.org/).
When editing `.json` files, make sure to leave quotes in if they're there. Removing them will make everything crash and burn, possibly causing a threat to your life.
 1. If you have git installed, use ```git clone https://github.com/Zwork101/tf2_trade_bot.git``` to download the bot in the folder you're in. Otherwise, download the zip file and extract it into a folder.
2. If you already have your shared secret and identity secret, go to step 3. Otherwise, go [here](https://github.com/Jessecar96/SteamDesktopAuthenticator) and follow the instructions. When it asks you for an encrytption key, make sure to leave it blank. Then, go to the file you installed it in and open the "maFiles" folder. Open the file with numbers in its name in a text editor. Find your shared_secret and identity_secret (eg "shared_secret":"bla" - your shared secret is bla). You can always do CTRL+F to search to file if you don't want to scroll along.
3. Open "steamguard.json" in a text editor. Where it says "steam64 id" (next to "steamid") paste in the 64-bit steam id of the account. If you can't find this, go [here](https://steamid.io/), paste in the profile URL of the account and copy the steamID64. Where it says "steam shared secret" paste your shared secret. Where it says "steam identity secret" paste your identity secret. Save the file and close it.
4. Open "settings.json" in a text editor. Where it says "steamAPI key" paste your steam API key (if you don't have one go [here](https://steamcommunity.com/dev/apikey) - it doesn't matter what you put as the domain). To the right of "username" paste your username (the one you use when signing in) where it says "username here", and where to the right of "password" paste your password. Next, paste your backpack.tf API key where it says "backpack.tf key". If you don't have one, get one [here](https://backpack.tf/developer/apikey/view) (again, the site URL doesn't matter. In the comments you should say it's for a trading bot). To the right of "accept_escrow" put a 1 if you want trades that would incur an escrow period to be accepted, and a 0 if you don't. To the left of "decline_trades", put a 0 if you want incorrect trades to be ignored, and a 1 if you want them to be declined. To the left of "confirm_options", put "trades" if you want only trades accepted by the bot to be confirmed and "all" if you want all trades to be confirmed. Please note - it is more secure to only confirm trades the bot has made. If you confirm all trades anyone who could access your account could take items from you (for example if you're on a shared computer where you stay signed in).
5. Open "whitelist.data" in a text editor. Delete everything in there, and put 64-bit steam ids in there separated by a comma. Trades from these people will be accepted no matter what the contents are.
6. Open "trade.csv" in a text editor. Delete the last two lines. In here, you can put the details of all the items you want to buy and sell. Each line is a new item to be bought or sold. First, write down the name of the item (if it has a comma in it's name, use $$ instead - so "Taunt: Rock, Paper, Scissors" would be "Taunt: Rock$$ Paper$$ Scissors"). Then write a comma. Now, you'll need to do some maths. There are 5 fields you need to fill - scrap, reclaimed, refined, keys and buds. It's easier to work this out from the right. For this example we'll say you want 1 key, 23.88 ref. Nobody uses buds, so we'll leave them out. You want one key for this item - so the key value is 1. There's 23 refined metal - so ref is 23. There's two reclaimed metal, so rec is 2, and there are two scrap metal so scrap is 2. Now, place all these numbers together with a . between each one. It's scrap.rec.ref.key.bud, so the value would be 2.2.23.1.0 . Easy, right? ("no", everyone says). Put another comma on the line and now you have to put whether you'll be buying or selling the item. For this example we'll be selling, so put sell. That's it! With our example (to sell a Taunt: Rock, Paper, Scissors for 1 key 23.88 ref), the finished line would be `Taunt: Rock$$ Paper$$ Scissors, 2.2.23.1.0, sell`. Do this for every item.
7. That's it! Feel free to run the bot by double-clicking "bot.py". The bot should guide you through the installation of some packages, but this is a one time process so won't happen every time you want to run the bot. If you have any questions or it doesn't work, feel free to [join the discord](https://discord.gg/BdBBSNj) - there are lots of regular users of the bot who will be happy to help.

Happy profit-making!
