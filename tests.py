from L2Message import L2Message
def top_prioritys(queues, queue_num=0):
    tupel_packets = queues#[queue_num]
    used_proritys = {}
    for packet in tupel_packets:
        if packet[0] not in used_proritys:
            used_proritys[packet[0]] = packet
        elif used_proritys[packet[0]][1] > packet[1]:
            used_proritys[packet[0]] = packet

    return used_proritys


def min_key_func(dict):
    if dict is None:
        return None
    min_time = 0
    min_key = 0
    for key in dict.keys():
        if min_time==0:
            min_time = dict[key]
            min_key = key
        elif dict[key] < min_time:
            min_time = dict[key]
            min_key = key
    print(min_time)
    return min_key


def mac_to_number(mac):
    return int(mac.replace(':', ''), 16)

def return_l2_by_mac(mac,queues):
    for queue in queues.values():
        if mac == queue[0]:
            return queue[2]

    return None
def gps(timeline, transmission_rate,queues, queue_num=0, printing_flag=1):
    current_time = timeline #timeline.events[0].scheduled_time

    tupel_packets = top_prioritys(queues)
    end_point = current_time + len(tupel_packets) * transmission_rate

    # Use a set to store unique MAC addresses
    # Sum the numeric representations of unique MAC addresses
    total_sum = sum(mac_to_number(mac) for mac in tupel_packets)

    rate = transmission_rate / total_sum  # find rate
    end_times = {}
    min=0
    for p in tupel_packets.values():
        end_times[p[0]] = p[2].message_size / (rate * mac_to_number(p[0]))  # TODO: need to check if true
    min = min_key_func(end_times)

    return return_l2_by_mac(min,tupel_packets)

l1 = L2Message("00:00:00:01","",10,"bobo")
l2 = L2Message("00:00:00:02","",10,"bobo")
l3 = L2Message("00:00:00:03","",10,"bobo")
l11 = L2Message("00:00:00:01","",10,"bobo")
queues = [("00:00:00:01",1,l1),("00:00:00:02",2,l2),("00:00:00:03",3,l3),("00:00:00:01",4,l11)]
min = gps(4,1.4,queues)
print("mac:",min.src_mac)