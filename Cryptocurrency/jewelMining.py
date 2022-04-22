
from web3 import Web3
import json
import sys
import time
import os
from datetime import datetime, timezone
import math

# Load JSONs
f = open('abi.json')  # contains functions in quest contract
abi = json.load(f)
f.close()

f = open('config.json')  # contains config info
config = json.load(f)
f.close()

# Default RPC
# RPC = "https://harmony-0-rpc.gateway.pokt.network"
RPC = "https://api.harmony.one"

# Wallet info from config
wallet_address = config['wallet']['address']
private_key = config['wallet']['privateKey']

# Set up RPC
provider = Web3(Web3.HTTPProvider(RPC))

# Set up Quest
questContract = provider.eth.contract(address=config['questContract'], abi=abi)

# Main loop


def main():
    try:
        os.system('clear')  # clear terminal
        checkForQuests()  # loop
    except Exception as err:
        sys.stdout.flush()
        sys.stdout.write(err)


def checkForQuests():
    try:
        # loop indefinitely
        while True:
            sys.stdout.write('\n1. Checking active quest\n')
            sys.stdout.flush()

            # collects all active quests
            activeQuests = questContract.functions.getActiveQuests(wallet_address).call()
            sys.stdout.write('2. Got active quest\n')
            sys.stdout.flush()

            # displays finish time for any quests in progress
            runningQuests = list(filter(lambda x: (x[6] >= time.time()), activeQuests))  # x[6] is the unix timestamp when the quest will finish

            # wait until 15 stamina has been spent: 15 total stamina * 10 minutes per stamina spent * 60s per minute
            if len(runningQuests) > 0:
                for quest in runningQuests:
                    # remove quest from runningQuests if 15 stamina can't be spent before it would complete
                    if quest[6] - time.time() < (15*10*60):
                        runningQuests.remove(quest)
                    else:
                        fifteen = int(15*10*60) + 60 # wait until 15 stamina have been spent, plus an extra minute to be safe
                        waittime = int(math.ceil(quest[4] + fifteen - time.time()))
                        endtime_utc = datetime.utcfromtimestamp(quest[4] + fifteen) # quest[4] has the time the quest started
                        endtime_local = endtime_utc.replace(tzinfo=timezone.utc).astimezone(tz=None).strftime('%m-%d %H:%M')
                        output_str = f'3. Quest led by hero {quest[2][0]} will complete at {endtime_local}, in {int(math.ceil(waittime/60))} minutes\n'
                        sys.stdout.write(output_str)
                        sys.stdout.flush()

                        for s in range(1, waittime):
                            time.sleep(1)
                            # Every 1m print the number of minutes left
                            if s % 60 == 0:
                                output_str = f'{int(math.ceil((waittime - s)/60))}'
                                sys.stdout.write(output_str)
                                sys.stdout.flush()
                                if s % 600 == 0:
                                    sys.stdout.write('\n')
                                    sys.stdout.flush()
                            # Every 10s print a dot
                            elif s % 10 == 0:
                                sys.stdout.write('.')
                                sys.stdout.flush()

            # complete any quests that need to be completed
            doneQuests = list(filter(lambda x: (x not in runningQuests), activeQuests))

            if len(doneQuests) > 0:
                for quest in doneQuests:
                    heroID = quest[2][0]
                    output_str = f'3. Completing quest led by hero {heroID}\n'
                    sys.stdout.write(output_str)
                    sys.stdout.flush()
                    completeQuest(heroID)

            # checks heroes stamina if there are no active quests (this only works if you only intend to run 1 quest at a time)
            if len(activeQuests) == 0:
                stamina = 0
                heroID, stamina = checkStamina()
                # if all heroes from config have max stamina, start the mining quest
                if stamina > 0:
                    startQuest(heroID)
                else:
                    sys.stdout.write('Not Ready...\n')
                    sys.stdout.flush()

            # always wait 5 seconds before rerunning the loop
            time.sleep(10)

    # ValueError called when RPC call fails. This code waits 5s and then retries the whole loop
    except ValueError:
        time.sleep(10)
        checkForQuests()  # rerun the loop


def completeQuest(heroID):
    try:
        # set up transaction to complete mining quest led by heroID
        nonce = provider.eth.getTransactionCount(wallet_address)  # need to run this each time, this is basically the transaction # for the wallet
        tx = questContract.functions.cancelQuest(heroID).buildTransaction({
            'gas': 2000000,  # this combined with gas price leads to max gas of 0.05 ONE
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)

        # output 0x format transaction hash
        output_str = f'4. Completed quest with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    # ValueError called when RPC call fails. This code waits 5s and then retries to checkForQuests loop
    except ValueError:
        time.sleep(10)


def checkStamina():
    # figure out which hero has the highest stamina
    try:
        maxStamina = 0
        for hero in config['heroIDs']:
            stamina = questContract.functions.getCurrentStamina(hero).call()
            if stamina > maxStamina:
                maxHero = hero
                maxStamina = stamina
        output_str = f'3. Hero {maxHero} has highest stamina: {maxStamina}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()
        return maxHero, maxStamina
    except ValueError:
        time.sleep(10)


def startQuest(heroID):
    try:
        # set up transaction to start mining quest with hero with max stamina
        nonce = provider.eth.getTransactionCount(wallet_address)

        # UPDATE THIS ONCE JEWEL MINING IS RELEASED
        tx = questContract.functions.startQuest([heroID], config['jewelMiningContract'], 1).buildTransaction({
            'gas': 2000000,
            'gasPrice': provider.toWei('35', 'gwei'),
            'from': wallet_address,
            'nonce': nonce
        })
        signed_tx = provider.eth.account.sign_transaction(tx, private_key=private_key)
        receipt = provider.eth.send_raw_transaction(signed_tx.rawTransaction)
        output_str = f'4. Started quest with tx hash {receipt.hex()}\n'
        sys.stdout.write(output_str)
        sys.stdout.flush()

    except ValueError:
        time.sleep(10)


main()
