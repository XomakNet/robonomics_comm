# -*- coding: utf-8 -*-
#
# Robonomics market support node.
#

from robonomics_market.msg import Ask, Bid
from binascii import hexlify, unhexlify
from .pubsub import publish, subscribe
from urllib.parse import urlparse
from threading import Thread
import rospy

def bid2dict(b):
    return { 'model'    : b.model,
             'token'    : b.token,
             'cost'     : b.cost,
             'count'    : b.count,
             'lighthouseFee' : b.lighthouseFee,
             'salt'     : hexlify(b.salt).decode('utf-8'),
             'signature': hexlify(b.signature).decode('utf-8'),
             'deadline' : b.deadline }

def ask2dict(a):
    return { 'model'    : a.model,
             'objective': a.objective,
             'token'    : a.token,
             'cost'     : a.cost,
             'count'    : a.count,
             'validator'    : a.validator,
             'validatorFee' : a.validatorFee,
             'salt'     : hexlify(a.salt).decode('utf-8'),
             'signature': hexlify(a.signature).decode('utf-8'),
             'deadline' : a.deadline }

class Market:
    def __init__(self):
        '''
            Robonomics market initialisation.
        '''
        rospy.init_node('robonomics_market')
        self.market_topic = rospy.get_param('~market_topic')
        ipfs_api = urlparse(rospy.get_param('~ipfs_http_provider')).netloc.split(':')
        self.ipfs_api = '/ip4/{0}/tcp/{1}'.format(ipfs_api[0], ipfs_api[1])

        self.incoming_bid = rospy.Publisher('incoming/bid', Bid, queue_size=10)
        self.incoming_ask = rospy.Publisher('incoming/ask', Ask, queue_size=10)
        rospy.Subscriber('sending/bid', Bid, lambda m: publish(self.ipfs_api, self.market_topic, bid2dict(m)))
        rospy.Subscriber('sending/ask', Ask, lambda m: publish(self.ipfs_api, self.market_topic, ask2dict(m)))

    def spin(self):
        '''
            Waiting for the new messages.
        '''
        def incoming_thread():
            for m in subscribe(self.ipfs_api, self.market_topic):
                if 'objective' in m:
                    msg = Ask()
                    msg.model     = m['model']
                    msg.objective = m['objective']
                    msg.token     = m['token']
                    msg.cost      = m['cost']
                    msg.count     = m['count']
                    msg.validator    = m['validator']
                    msg.validatorFee = m['validatorFee']
                    msg.salt      = unhexlify(m['salt'].encode('utf-8'))
                    msg.signature = unhexlify(m['signature'].encode('utf-8'))
                    msg.deadline  = m['deadline']
                    self.incoming_ask.publish(msg)
                else:
                    msg = Bid()
                    msg.model     = m['model']
                    msg.token     = m['token']
                    msg.cost      = m['cost']
                    msg.count     = m['count']
                    msg.lighthouseFee = m['lighthouseFee']
                    msg.salt      = unhexlify(m['salt'].encode('utf-8'))
                    msg.signature = unhexlify(m['signature'].encode('utf-8'))
                    msg.deadline  = m['deadline']
                    self.incoming_bid.publish(msg)
        Thread(target=incoming_thread, daemon=True).start()
        rospy.spin()
