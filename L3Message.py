import queue
import math
import copy
from Switch import Switch
from Event import Event
from L2Message import L2Message
import random


class L3Message(L2Message):
    def __init__(self, src_mac, dst_mac, message_payload, message_type,arrival_time,priority,flow_id):
        super().__init__(src_mac,dst_mac,message_payload,message_type)

        self.arrival_time = arrival_time
        self.priority = priority
        self.start_time = None
        self.end_time = None
        self.flow_id = flow_id