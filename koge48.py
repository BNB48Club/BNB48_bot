import ConfigParser
import random
import json
import datetime
import time
import mysql.connector
import logging

from binance.client import Client



logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
logger = logging.getLogger(__name__)

class Koge48:
    def BNBAirDrop(self):
        logger.warning("airdroping")
        self._mycursor.execute("SELECT unix_timestamp(ts) FROM `changelog` WHERE `memo` LIKE '%bnbairdrop%' ORDER by height DESC LIMIT 1")        
        lastts = self._mycursor.fetchone()[0]
        secondsduration = time.time() - lastts

        self._mycursor.execute("SELECT *,offchain+onchain as total FROM `bnb`")
        res = self._mycursor.fetchall()

        for each in res:
            bnbamount = each[4]
            if bnbamount > 50000:
                bnbamount = 50000
            self.changeBalance(each[0],secondsduration*bnbamount/(24*3600),'bnbairdrop')
        
    def __init__(self,host,user,passwd,database):

        self._mydb = mysql.connector.connect(
            host=host,
            user=user,
            passwd=passwd,
            database=database
        )
        self._mycursor = self._mydb.cursor()

        self._prob = 0.06
        self._tries = 0
        self._cache = {}
        return


    def setEthAddress(self,userid,eth):
        updatesql = "INSERT INTO eth (uid,eth) VALUES (%s,%s) ON DUPLICATE KEY UPDATE eth=%s"
        self._mycursor.execute(updatesql,(userid,eth,eth))
        self._mydb.commit()

    def setApiKey(self,userid,apikey,apisecret):
        updatesql = "INSERT INTO apikey (uid,apikey,apisecret) VALUES (%s,%s,%s) ON DUPLICATE KEY UPDATE apikey=%s,apisecret=%s"
        self._mycursor.execute(updatesql,(userid,apikey,apisecret,apikey,apisecret))
        self._mydb.commit()
        
    def changeBalance(self,userid,number,memo=""):
        balance = self.getBalance(userid)
        assert balance + float(number) > -0.001
        newblocksql = "INSERT INTO changelog (uid,differ,memo) VALUES (%s,%s,%s)"
        self._mycursor.execute(newblocksql,(userid,number,memo))
        self._mydb.commit()

        self._cache[userid]=balance + float(number)
        return self._cache[userid]

    def _getBalanceFromDb(self,userid):
        self._mycursor.execute("SELECT `bal` FROM `balance` WHERE `uid` = {}".format(userid))
        res = self._mycursor.fetchone()
        if res is None:
            return 0
        else:
            return res[0]
    def getAirDropStatus(self,userid):
        #get eth
        self._mycursor.execute("SELECT eth FROM `eth` WHERE `uid` = {}".format(userid))
        res = self._mycursor.fetchone()
        if not res is None:
            eth = res[0]
        else:
            eth=""
        #get api
        self._mycursor.execute("SELECT apikey,apisecret FROM `apikey` WHERE `uid` = {}".format(userid))
        api = self._mycursor.fetchone()
        if api is None:
            api = ["",""]
        #get bnb balance
        self._mycursor.execute("SELECT onchain,offchain FROM `bnb` WHERE `uid` = {}".format(userid))
        bnb = self._mycursor.fetchone()
        if bnb is None:
            bnb = [0,0]
        #get last 10 airdrop
        self._mycursor.execute("SELECT *,unix_timestamp(ts) AS timestamp FROM `changelog` WHERE  `memo` LIKE '%bnbairdrop%' AND `uid` = {} ORDER BY height DESC LIMIT 10".format(userid))
        airdrops=[]
        currentts = time.time()
        for each in self._mycursor.fetchall():
            airdrops.append({"before":str(datetime.timedelta(seconds=int(currentts - each[5]))),"diff":each[2]})
        return {"eth":eth,"api":api,"bnb":bnb,"airdrops":airdrops}
            
        
    def getBalance(self,userid):
        if userid in self._cache:
            return self._cache[userid]
        else:
            balance = self._getBalanceFromDb(userid)
            self._cache[userid]=balance
            return balance
    def mine(self,minerid):
        self._tries+=1;
        if random.random()<self._prob:
            self.changeBalance(minerid,1,"mining")            
            self._tries = 0
            logger.warning("%s mined one",minerid)
            return True
        else:
            return False
