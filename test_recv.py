import time
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_ import WirelessController_

def test_handler(msg: WirelessController_):
    print(f"✅ 收到虚拟手柄信号! keys: 0x{msg.keys:04X}, lx: {msg.lx:.2f}, ly: {msg.ly:.2f}")

if __name__ == '__main__':
    ChannelFactoryInitialize(1, "eth0")
    sub = ChannelSubscriber("rt/wireless_controller", WirelessController_)
    sub.Init(test_handler, 10)
    print("🎧 正在监听 rt/wirelesscontroller ... (请在另一个终端运行并按 1/2/W/A 等键)")
    while True:
        time.sleep(1)
