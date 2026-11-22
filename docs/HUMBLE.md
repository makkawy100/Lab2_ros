# Humble + Gazebo Fortress: Ubuntu 22.04

دي النسخة المناسبة لجهازك لو عليه ROS 2 Humble بالفعل. مش محتاج تشيل Humble أو تنزل Jazzy عشان تجربها.

The PDF recommends Jazzy with modern Gazebo, but does not state Jazzy is mandatory. This separate launch uses **Humble + Gazebo Fortress (`ign gazebo`, version 6)**. It is not Gazebo Classic (`gazebo`). The Jazzy/Harmonic launch is preserved separately.

Both share the same URDF, controller nodes, GUI and Arduino firmware. Only simulator world/plugin naming, bridge message namespaces and launch selection differ.

## Install and build

Use a fresh terminal with only Humble sourced. These commands assume ROS 2 Humble and its apt repository are already installed on native Ubuntu 22.04.

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y ros-humble-ros-gz ros-humble-rviz2 \
  ros-humble-robot-state-publisher python3-colcon-common-extensions \
  python3-rosdep python3-serial python3-tk git build-essential

cd ~
git clone https://github.com/makkawy100/ros2-robotic-arm.git
cd ros2-robotic-arm
# If this repository was already cloned, use git pull instead of cloning again.
# Only if rosdep was never initialized before:
# sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation_humble.launch.py
```

Expected: Gazebo Fortress opens with the arm, RViz2 opens with `base_link` fixed frame and RobotModel. No physical servo is enabled.

In a second terminal:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2-robotic-arm
source install/setup.bash
ros2 run arm_control sliders
```

غيّر joint1 إلى 20 درجة وjoint2 إلى -20، وسيب الوقت 3 ثواني، وبعدها اضغط **Send trajectory**. الحركة تظهر في Gazebo وRViz2 مع بعض.

Or use one command:

```bash
ros2 run arm_control trajectory_publisher --ros-args \
  -p 'positions:=[0.3, -0.4, 0.5, -0.2]' -p duration:=3.0
```

## Hardware, after safe wiring/upload

The same firmware/protocol/pin table in the main README applies. Start with dry-run:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=true
```

After uploading the sketch, checking D9/D10 and common ground, external servo power, safe neutral and direction, stop the previous launch and enable serial:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

The two real servos are joint1 and joint2; all four joints move in simulation. **Actual board upload and servo movement are not verified by this repository's software tests.**

## Headless and rerunnable tests

```bash
ros2 launch arm_simulation simulation_humble.launch.py headless:=true rviz:=false
# Stop that launch before running the self-contained tests below.
```

After sourcing the workspace:

```bash
python3 -m unittest discover -s tests -v
ign sdf -k src/arm_simulation/worlds/arm_world_fortress.sdf
ARM_VARIANT=humble python3 tools/smoke_simulation.py
ARM_VARIANT=humble python3 tools/smoke_serial.py
# Optional actual Tk callback test on a virtual display:
sudo apt install -y xvfb
ARM_VARIANT=humble python3 tools/smoke_gui.py
```

Rebuild the Fortress world after a URDF change:

```bash
python3 tools/generate_world.py --variant fortress
colcon build --symlink-install
```

## Important differences from Jazzy

| Item | Humble/Fortress | Jazzy/Harmonic |
|---|---|---|
| Ubuntu standard pairing | 22.04 | 24.04 |
| Project launch | `simulation_humble.launch.py` | `simulation.launch.py` |
| Simulator command | `ign gazebo` | `gz sim` |
| World | `arm_world_fortress.sdf` | `arm_world.sdf` |
| Bridge config | `bridge_fortress.yaml` | `bridge.yaml` |
| Transport types | `ignition.msgs.*` | `gz.msgs.*` |
| Physical firmware | Same | Same |

Do not install `ros-humble-ros-gzharmonic` for this variant. That is a non-default Humble/Harmonic pairing and can conflict with the official Humble/Fortress packages. Do not mix the build/install folders of a workspace built under different ROS distributions. If changing distros, use a separate clone or build/install bases.

## What was actually tested

A real **Humble + Fortress 6.16.0** runtime was provisioned using RoboStack/conda on Linux. All four packages built, the SDF validated, all four joints moved to target and back from the assignment topic, Gazebo feedback and TF were received, the Tk callback test passed and the real pyserial pseudoterminal test passed. Actual Gazebo and RViz2 images were inspected before/after a command.

This was not a clean apt-based installation on the student's machine. Firmware was compiled for Uno, not uploaded to a physical board. Actual servos and USB hardware remain to be tested. See [full verification](VERIFICATION.md).

If Gazebo opens but is blank, first check you used `simulation_humble.launch.py`, not the Jazzy launch. For software-rendering problems, try setting `LIBGL_ALWAYS_SOFTWARE=1` before launching. If DDS discovery is stale, close other project runs and use a fresh terminal. If you stop Gazebo, stop the whole launch before starting a new one; do not leave two simulators controlling the same topics.

Official simulator pairing/install source: https://gazebosim.org/docs/fortress/ros_installation/
