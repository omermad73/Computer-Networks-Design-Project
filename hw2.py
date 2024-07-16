import math
import copy
def round_up_after_5th_digit(number):
    multiplier = 10 ** 5
    return math.ceil(number * multiplier) / multiplier


class Message:
    def __init__(self, packet_Number, size, flow, arrival):
        self.id = packet_Number
        self.size = size  # Mbit
        self.flow = flow  # Mbit
        self.arrival = arrival

    def __str__(self):
        return f"Message(id={self.id}, flow={self.flow})"


def find_longest_wait(messages):
    m = messages[0]
    for messge in messages:
        if m.scheduling > messge.scheduling:
            m = messge
    messages.remove(m)
    return m


def find_first_to_come(messages):  # FIFO - reutn the first message that arived
    m = messages[0]
    for messge in messages:
        if m.arrival == messge.arrival and m.flow < messge.flow:
            m = messge
        elif m.arrival > messge.arrival:
            m = messge
    messages.remove(m)
    return m


def find_first_to_come_with_priority(messages,
                                     time):  # priority - reutn the first message that arived but with priority
    m = messages[0]
    flag = False
    for messge in messages:
        if time > messge.arrival:
            if flag == False:
                m = messge
                flag = True
            elif m.flow < messge.flow:
                m = messge
                flag = True

            elif m.flow == messge.flow and m.arrival > messge.arrival:
                m = messge
                flag = True

    if not flag:
        m = find_first_to_come(messages)
        return m
    messages.remove(m)
    return m


def sum_flow(list, queue_list):  # sum the flows of the acives flows
    sum = 0
    for i in range(0, len(list)):
        if queue_list[i]:
            sum += list[i]
    return sum


def next_mess_time(messages, time=0):  # returning the time of the first arrive. or the n numberd if used time after time.
    time = messages[0].arrival
    for mess in messages:
        if mess.arrival < time:
            time = mess.arrival
    return time


def next_mess(messages, time):  # geeting the message on time "time"
    m = []
    for messge in messages:
        if messge.arrival == time:
            m.append(messge)

    for mess in m:
        messages.remove(mess)
    return m


def mess_to_list(m_list, queue_list, flow_list):  # sorting the messages to thiere list priority
    for messge in m_list:
        for i in range(0, len(flow_list)):
            if messge.flow == flow_list[i]:
                queue_list[i].append(messge)


def prints_queses(queue_list):  # sorting the messages to thiere list priority
    i = 0
    for queue in queue_list:
        i += 1
        for packet in queue:
            print("in queue", i, "there is packet", packet.id)

def GPS_Scheduling(packets, transmission_rate, flg = 0):
    if flg == 0:
        print("GPS Scheduling:")
    order_of_packets = []
    current_time = 0
    packets.sort(key=lambda x: x.arrival)  # Sort packets by arrival time first
    not_ready_packets = []
    for packet in packets: not_ready_packets.append(packet)
    ready_packets = []
    while not_ready_packets or ready_packets:
        # While there is packet hasnt get fully serviced
        for packets in not_ready_packets:
            if packets.arrival <= current_time and packets.flow not in [packet.flow for packet in ready_packets]:
                ready_packets.append(packets)
                not_ready_packets.remove(packets)
                #if there is a packet that has arrived and not in the ready queue, add it to the ready queue


        if ready_packets:
            rate = transmission_rate/sum(packet.flow for packet in ready_packets)   #find rate
            time_min = min((packet.size / (rate * packet.flow) for packet in ready_packets),
                           default=end_point)
            #find the minimum time to service the packet

            filtered_packets = [packet.arrival for packet in not_ready_packets if packet.flow not in [p.flow for p in ready_packets]]

            lowest_arrival = min(filtered_packets) - current_time if filtered_packets else -1
            if lowest_arrival != -1:
                time_min = min (time_min, lowest_arrival)
            #find the minimum time to the next packet arrival which is flow_id not in the ready queue


            for packet in ready_packets:
                packet.size = packet.size - rate * packet.flow * time_min
            for packet in ready_packets:
                if packet.size == 0:
                    order_of_packets.append(packet.id)
                    ready_packets.remove(packet)
                    packet.end_time = current_time + time_min
                    if flg == 0:
                        print(packet.id,packet.end_time)
            current_time = current_time + time_min
    return order_of_packets

def find_pack(id, packets):
    for packet in packets:
        if packet.id == id:
            return packet
    return None

def PGPS_Scheduling(packets, transmission_rate):
    print("PGPS Scheduling:")
    current_time = 0
    packets.sort(key=lambda x: x.arrival)  # Sort packets by arrival time first
    copy_packets = []
    for packet in packets: copy_packets.append(copy.deepcopy(packet))
    #making deep cppy of packets
    list_arrived_GPS = GPS_Scheduling(packets, transmission_rate, 1)

    mid_ready_packets = []


    while copy_packets or mid_ready_packets:

        for i in copy_packets:
            if i.arrival <= current_time and i.id not in mid_ready_packets:
                mid_ready_packets.append(i.id)

        #list of packets that have been serviced by GPS

        # While there is packet hasnt get fully serviced

        first_finished_GPS = next((x for x in list_arrived_GPS if x in mid_ready_packets), None)
        if first_finished_GPS:
            id = first_finished_GPS
            pack = find_pack(id, copy_packets)
            current_time = current_time + pack.size/transmission_rate
            print(pack.id,current_time)
            mid_ready_packets.remove(id)
            copy_packets.remove(pack)


R = 1.4  # Mbit
flow1 = 1
flow2 = 2 * flow1
flow3 = 2 * flow2
flow_list = [flow1, flow2, flow3]
num_of_flows = 3



m1 = Message(1, 5.6, flow2, 0)
m2 = Message(2, 6, flow3, 1)
m3 = Message(3, 0.6, flow1, 3)
m4 = Message(4, 0.8, flow1, 7)
m5 = Message(5, 3.8, flow3, 7)
messages = [m1, m2, m3, m4, m5]

total_packet_size = sum(message.size for message in messages)
end_point = total_packet_size * R

time = 0
queue_type = 'PGPS'
if queue_type == 'FIFO':
    while messages:
        m = find_first_to_come(messages)
        time = time + m.size / R
        print(m.id, round_up_after_5th_digit(time))

elif queue_type == 'Priority':
    if messages:
        m = find_first_to_come(messages)
        time = time + m.size / R
        print(m.id, time)
    while messages:
        m = find_first_to_come_with_priority(messages, time)
        time = time + m.size / R
        print(m.id, round_up_after_5th_digit(time))

elif queue_type == "GPS":
    GPS_Scheduling(messages, R)

elif queue_type == "PGPS":
    PGPS_Scheduling(messages, R)