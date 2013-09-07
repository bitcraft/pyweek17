def pack(a, b):
    return (a << 4) | b

def unpack(a):
    return (a >> 4) & 0x0F, a & 0x0F
