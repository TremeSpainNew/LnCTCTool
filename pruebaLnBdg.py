from loconet_bridge import LocoNetBridge

ln = LocoNetBridge()

ln.connect_bridge()
print(ln.ping())

print(ln.connect_loconet("192.168.25.1", 1234))

print(ln.lncv_start(6020, 1))
print(ln.lncv_read(0))
print(ln.lncv_write(5, 6))
print(ln.lncv_stop())

ln.close()