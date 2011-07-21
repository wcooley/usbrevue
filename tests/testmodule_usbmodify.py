def modify(generator, commit):

    for packet in generator():
        if len(packet.data) >= 2:
            packet.ts_sec += packet.data[1] * packet.data[0]

        packet.epnum += 1

        if packet.devnum == 3:
            continue

        commit(packet)
