def modify(packet_gen, commit_func):
    for packet in packet_gen('-'):
        if packet.devnum == 6:
            commit_func(packet)
