import copy
from GNO import GNO


class L2Message(GNO):
    header_size = 14

    def __init__(self, src_mac, dst_mac, message_payload, message_type):
        super().__init__("L2Message")
        self.src_mac = src_mac
        self.dst_mac = dst_mac
        self.message_payload = message_payload
        self.message_size = message_payload + L2Message.header_size
        self.message_type = message_type


    def __copy__(self):
        return L2Message(self.src_mac, self.dst_mac, self.message_payload, self.message_type)
