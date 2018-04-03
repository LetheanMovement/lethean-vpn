
import time
import logging
import pickle
from util import *

class AuthId(object):
    """
    Single paymentid session class.
    All payments for given paymentid are in one session.
    """
    
    def __init__(self, authid, serviceid, cost, balance):
        self.id = authid
        self.balance = 0
        self.serviceid = serviceid
        self.cost = cost
        self.created = time.time()
        self.charged_count = 0
        self.lastModify = time.time()
        if (balance > 0):
            self.topUp(balance)
        self.discharged_count = 0
        
    def getId(self):
        return(self.id)

    def show(self):
        logging.info("""PaymentId %s:
            serviceid %s,
            created at %s
            modified at %s
            balance %f
            cost per minute %f
            minutes left %f
            charged_count %d
            discharged_count %d
            """ % (self.id, self.serviceid, timefmt(self.created), timefmt(self.lastModify), self.balance, self.cost, self.balance / self.cost, self.charged_count, self.discharged_count))
        
    def topUp(self, balance):
        self.balance += balance
        self.lastModify = time.time()
        self.lastCharge = time.time()
        self.charged_count += 1
        logging.debug("Authid %s: Topup %f, new balance %f" % (self.getId(), balance, self.balance))
    
    def spend(self, minutes):
        self.balance -= (self.cost * minutes)
        self.lastModify = time.time()
        self.lastDisCharge = time.time()
        self.discharged_count += 1
        logging.debug("Authid %s: Spend %f minutes, cost %f, new balance %f" % (self.getId(), minutes, self.cost * minutes, self.balance))
    
    def getBalance(self):
        return(self.balance)
    
    def checkAlive(self):
        return(self.balance > 0)

class AuthIds(object):
    """Active payments sessions container"""
    
    def __init__(self):
        self.payments = {}
        self.lastmodify = time.time()
        
    def update(self, paymentid):
        if paymentid.getId() in self.payments.keys():
            self.topUp(paymentid.getId(), paymentid.getBalance())
        else:
            self.payments[paymentid.getId()] = paymentid
        
    def topUp(self, paymentid, balance):
        self.payments[paymentid].topUp(balance)

    def spend(self, paymentid, balance):
        self.payments[paymentid].spend(balance)
        
    def get(self, paymentid):
        if (paymentid in self.payments):
            return(self.payments[paymentid])
        else:
            return(None)

    def remove(self, paymentid):
        self.payments.pop(paymentid.getId())
        
    def show(self):
        logging.warning("Authids: %d ids, last updated %s" %(len(self.payments),timefmt(self.lastmodify)))
        for id, paymentid in self.payments.items():
            paymentid.show()
        
    def cleanup(self):
        fresh = 0
        deleted = 0
        for id in self.payments.keys():
            if not self.payments[id].checkAlive():
                self.payments.pop(id)
                deleted += 1
            else:
                fresh += 1
        logging.info("Authids clean: %d deleted, %d fresh" % (deleted, fresh))
                
    def getFromWallet(self,services):
        """Connect to wallet and ask for all payments from last height"""
        # Hardcoded payment
        s1 = AuthId("authid1", "1A", services.get("1A").getCost(), 1)
        s2 = AuthId("authid2", "2B", services.get("2B").getCost(), 10)
        s3 = AuthId("authid3", "1A", services.get("1A").getCost(), 20)
        s4 = AuthId("authid1", "1A", services.get("1A").getCost(), 10)
        self.update(s1)
        self.update(s2)
        self.update(s3)
        self.update(s4)

    def save(self, filename):
        self.cleanup()
        self.lastmodify=time.time()
        logging.info("Saving authids db into %s" % (filename))
        with open(filename, 'wb') as output:
            pickle.dump(self, output, pickle.HIGHEST_PROTOCOL)
