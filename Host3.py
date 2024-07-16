from Host2 import Host2
import random
from L2Message import L2Message


class Host3(Host2):
    def __init__(self, mac,dst_rnd_set = None, seed = 42,total_tx_bytes=0, total_rx_bytes=0, nic=-1):
        super().__init__(mac,dst_rnd_set,seed, total_tx_bytes, total_rx_bytes, nic)