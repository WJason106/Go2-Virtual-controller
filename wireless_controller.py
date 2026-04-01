#!/usr/bin/env python3
"""
virtual_joystick.py  —  Unitree Go2 虚拟无线控制器
用途：没有实体手柄时，通过键盘驱动 go2_ctrl 的 FSM 状态切换和速度控制。

运行：python3 virtual_joystick.py
"""

import sys
import time
import tty
import termios
import select

# ============================================================
# unitree_sdk2py 导入（基于你服务器上的实际 API）
# ============================================================
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.idl.unitree_go.msg.dds_ import WirelessController_

# ============================================================
# DDS 配置  —  必须和 unitree_mujoco.py / go2_ctrl 一致
# ============================================================
DOMAIN_ID = 1
INTERFACE = "eth0"
TOPIC     = "rt/wireless_controller"

# ============================================================
# 按钮位掩码定义（keys 字段）
# ============================================================
# keys 是一个整数，每个 bit 对应一个按钮：
#
#   Bit 0  (0x0001) = R1
#   Bit 1  (0x0002) = L1
#   Bit 2  (0x0004) = START
#   Bit 3  (0x0008) = SELECT
#   Bit 4  (0x0010) = R2 (RT)
#   Bit 5  (0x0020) = L2 (LT)
#   Bit 6  (0x0040) = F1
#   Bit 7  (0x0080) = F2
#   Bit 8  (0x0100) = A
#   Bit 9  (0x0200) = B
#   Bit 10 (0x0400) = X
#   Bit 11 (0x0800) = Y
#   Bit 12 (0x1000) = D-pad UP
#   Bit 13 (0x2000) = D-pad RIGHT
#   Bit 14 (0x4000) = D-pad DOWN
#   Bit 15 (0x8000) = D-pad LEFT
#
# ★ 如果按 1/2/3 后 go2_ctrl 没反应，优先改这里 ★

BTN_R1     = 0x0001
BTN_L1     = 0x0002
BTN_START  = 0x0004
BTN_SELECT = 0x0008
BTN_R2     = 0x0010   # RT
BTN_L2     = 0x0020   # LT
BTN_F1     = 0x0040
BTN_F2     = 0x0080
BTN_A      = 0x0100
BTN_B      = 0x0200
BTN_X      = 0x0400
BTN_Y      = 0x0800

# FSM 切换组合键
COMBO_LT_A  = BTN_L2 | BTN_A    # Passive  → FixStand
COMBO_START = BTN_START          # FixStand → Velocity
COMBO_LT_B  = BTN_L2 | BTN_B    # → Passive

# ============================================================
# 摇杆 / 发布配置
# ============================================================
LX_STEP    = 0.15
LY_STEP    = 0.15
RX_STEP    = 0.15
MAX_VAL    = 1.0
MIN_VAL    = -1.0
PUBLISH_HZ = 50
PULSE_FRAMES = 20   # 脉冲持续帧数（~160ms @ 50Hz）


# ============================================================
# 非阻塞键盘读取
# ============================================================
class RawTerminal:
    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)

    def __enter__(self):
        tty.setraw(self.fd)
        return self

    def __exit__(self, *args):
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

    @staticmethod
    def get_key(timeout=0.005):
        if select.select([sys.stdin], [], [], timeout)[0]:
            return sys.stdin.read(1)
        return None


# ============================================================
# 主控制器
# ============================================================
def clamp(val, lo=MIN_VAL, hi=MAX_VAL):
    return max(lo, min(hi, val))


def main():
    # --- DDS 初始化 ---
    print(f"[INIT] ChannelFactoryInitialize(domain={DOMAIN_ID}, iface={INTERFACE})")
    ChannelFactoryInitialize(DOMAIN_ID, INTERFACE)

    # --- 创建 Publisher ---
    pub = ChannelPublisher(TOPIC, WirelessController_)
    pub.Init()
    print(f"[INIT] Publisher ready on topic: {TOPIC}")

    # --- 状态 ---
    lx = 0.0   # 左摇杆 X：左右平移
    ly = 0.0   # 左摇杆 Y：前后
    rx = 0.0   # 右摇杆 X：转向
    ry = 0.0

    pending_keys = 0
    pulse_counter = 0
    running = True

    interval = 1.0 / PUBLISH_HZ

    print()
    print("=" * 56)
    print("  Unitree Go2 虚拟无线控制器已启动")
    print("=" * 56)
    print()
    print("  按键说明：")
    print("    1       LT+A   Passive  → FixStand")
    print("    2       START  FixStand → Velocity")
    print("    3       LT+B   → Passive")
    print("    w/s     前进 / 后退       (ly)")
    print("    a/d     左移 / 右移       (lx)")
    print("    q/e     左转 / 右转       (rx)")
    print("    空格    速度清零")
    print("    x       退出")
    print()
    print(f"  发布频率: {PUBLISH_HZ} Hz  |  Topic: {TOPIC}")
    print(f"  Domain: {DOMAIN_ID}  |  Interface: {INTERFACE}")
    print("-" * 56)

    with RawTerminal() as _term:
        while running:
            t0 = time.monotonic()

            # 读键
            ch = RawTerminal.get_key(timeout=0.001)
            if ch is not None:
                if ch == '1':
                    pending_keys = COMBO_LT_A
                    pulse_counter = PULSE_FRAMES
                    print("  >> LT+A  (Passive → FixStand)  keys=0x{:04X}".format(COMBO_LT_A))
                elif ch == '2':
                    pending_keys = COMBO_START
                    pulse_counter = PULSE_FRAMES
                    print("  >> START (FixStand → Velocity) keys=0x{:04X}".format(COMBO_START))
                elif ch == '3':
                    pending_keys = COMBO_LT_B
                    pulse_counter = PULSE_FRAMES
                    print("  >> LT+B  (→ Passive)           keys=0x{:04X}".format(COMBO_LT_B))
                elif ch == 'w':
                    ly = clamp(ly + LY_STEP)
                    print(f"  ly = {ly:+.2f}  (前进)")
                elif ch == 's':
                    ly = clamp(ly - LY_STEP)
                    print(f"  ly = {ly:+.2f}  (后退)")
                elif ch == 'a':
                    lx = clamp(lx - LX_STEP)
                    print(f"  lx = {lx:+.2f}  (左移)")
                elif ch == 'd':
                    lx = clamp(lx + LX_STEP)
                    print(f"  lx = {lx:+.2f}  (右移)")
                elif ch == 'q':
                    rx = clamp(rx + RX_STEP)
                    print(f"  rx = {rx:+.2f}  (左转)")
                elif ch == 'e':
                    rx = clamp(rx - RX_STEP)
                    print(f"  rx = {rx:+.2f}  (右转)")
                elif ch == ' ':
                    lx = ly = rx = ry = 0.0
                    print("  >> 速度归零")
                elif ch == 'x' or ch == '\x03':  # x 或 Ctrl+C
                    print("\n[EXIT] 退出虚拟手柄。")
                    running = False
                    continue

            # 计算当前按键
            if pulse_counter > 0:
                current_keys = pending_keys
                pulse_counter -= 1
                if pulse_counter == 0:
                    pending_keys = 0
            else:
                current_keys = 0
            
            # 构建消息
            msg = WirelessController_(lx=lx, ly=ly, rx=rx, ry=ry, keys=current_keys)

            # 发布
            pub.Write(msg)

            # 控制频率
            elapsed = time.monotonic() - t0
            sleep_time = interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    print("[DONE] 虚拟手柄已退出。终端已恢复。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[EXIT] Ctrl+C")
    except Exception as ex:
        # 确保终端恢复
        try:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN,
                              termios.tcgetattr(sys.stdin.fileno()))
        except Exception:
            pass
        print(f"\n[ERROR] {ex}")
        import traceback; traceback.print_exc()
        sys.exit(1)


