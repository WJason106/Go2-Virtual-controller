# 🐕 Unitree Go2 虚拟手柄控制器

本项目是一个纯 Python 写的「虚拟无线控制器」，基于unitree_mujoco、unitree_rl_lab、unitree_sdk2。本地仿真环境中，通过键盘替代实体 Unitree 手柄，控制 Go2 机器狗完成状态切换和运动控制。

---

## 📋 适用场景

- 在云服务器或 Docker 容器中进行强化学习训练与部署测试。
- 手头没有 Xbox/Switch 实体物理手柄。

---

## 🏗️ 文件介绍

| 组件 | 说明 |
|------|------|
| `wireless_controller.py` | 键盘虚拟手柄的主程序，负责监听按键并发布 DDS 指令 |
| `unitree_sdk2py_bridge.py` | 修改后的 MuJoCo 仿真底层桥接文件，负责接收虚拟指令并“伪装”成物理手柄注入到 `LowState` 中 |
| `test_recv.py` | 网络连通性测试脚本，用于排查 DDS 组播是否正常 |


---

## 🚀 使用方法

**第一步：启动仿真器**

```bash
cd ~/unitree_mujoco/simulate_python
python3 unitree_mujoco.py
```

**第二步：启动 RL 控制器**

需要对deploy中相关文件进行编译

```bash
cd ~/unitree_rl_lab/deploy/robots/go2
./go2_ctrl --network eth0
```

**第三步：启动虚拟手柄**

```bash
python3 wireless_controller.py
```

---

## 🎮 键位说明

| 按键 | 功能 | FSM 状态变化 |
|------|------|-------------|
| `1` | 站起来 | Passive → FixedStand |
| `2` | 进入运动模式 | FixedStand → Walk/Velocity |
| `3` | 趴下（阻尼保护） | 任意 → Passive |
| `W / S` | 前进 / 后退 | — |
| `A / D` | 左平移 / 右平移 | — |
| `Q / E` | 左转 / 右转 | — |
| `空格` | 急停（所有速度归零） | — |
| `Ctrl+C` | 退出程序 | — |

---
<img width="2165" height="1129" alt="TT)7 PX@W7APB94G }_V~U7" src="https://github.com/user-attachments/assets/99a91fc1-e950-4ef6-8ae4-bc13a90ef5dd" />


