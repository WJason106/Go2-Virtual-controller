基于unitree_mujoco、unitree_rl_lab、unitree_sdk2
特别适用于以下场景：
* 在云服务器或 Docker 容器中进行强化学习训练与部署测试。
* 手头没有 Xbox/Switch 实体物理手柄。

* wireless_controller.py: 键盘虚拟手柄的主程序，负责监听按键并发布 DDS 指令。
* unitree_sdk2py_bridge.py: 修改后的 MuJoCo 仿真底层桥接文件，负责接收虚拟指令并“伪装”成物理手柄注入到 `LowState` 中。
* test_recv.py: 网络连通性测试脚本，用于排查 DDS 组播是否正常。

  
<img width="2165" height="1129" alt="TT)7 PX@W7APB94G }_V~U7" src="https://github.com/user-attachments/assets/72a0530b-cbd3-4078-9240-d6f4b4e45efa" />

1.先在unitree_mujoco中正常启动仿真，
2.在编译好的unitree_rl_lab的deploy中启动相关的可执行文件（如：./go2_ctrl --network eth0）
3.运行wireless_controller.py进行指令发送
（4.测试可以采用test_recv.py）
