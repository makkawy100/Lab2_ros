# Setup notes: Ubuntu 22.04, ROS 2 Humble, Gazebo Fortress

This is the only configuration the project supports. It uses Gazebo Fortress (`ign gazebo`, Gazebo Sim 6), the version officially paired with Humble. It does not use Gazebo Classic (`gazebo`).

Install the standard `ros-humble-ros-gz` package only. Other Gazebo and ROS combinations can conflict with the Fortress packages.

## Install and build

Use a fresh terminal with only Humble sourced.

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y ros-humble-ros-gz ros-humble-rviz2 \
  ros-humble-robot-state-publisher python3-colcon-common-extensions \
  python3-rosdep python3-serial python3-tk git build-essential

cd ~
git clone https://github.com/makkawy100/Lab2_ros.git ros2-robotic-arm
cd ros2-robotic-arm
# Only needed the first time rosdep is used:
# sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble
colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation_humble.launch.py
```

Expected result: Gazebo Fortress opens with the arm, and RViz2 opens with `base_link` as the fixed frame and a RobotModel display. No servo is enabled.

In a second terminal:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2-robotic-arm
source install/setup.bash
ros2 run arm_control sliders
```

Set joint1 to 20 degrees and joint2 to -20 degrees, keep the duration at 3 seconds and press **Send trajectory**. The arm should move in Gazebo and RViz2 at the same time.

Without the GUI:

```bash
ros2 run arm_control trajectory_publisher --ros-args \
  -p 'positions:=[0.3, -0.4, 0.5, -0.2]' -p duration:=3.0
```

## Hardware

The firmware, protocol and pin table are described in the main README. Start in dry-run mode:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=true
```

Once the sketch is uploaded and D9, D10, common ground, external servo power, neutral position and direction have been checked, stop that launch and enable the serial output:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

The two physical servos are joint1 and joint2. All four joints move in simulation. Board upload and servo movement have not been tested.

## Headless runs and tests

```bash
ros2 launch arm_simulation simulation_humble.launch.py headless:=true rviz:=false
# Stop this launch before running the tests below.
```

With the workspace sourced:

```bash
python3 -m unittest discover -s tests -v
ign sdf -k src/arm_simulation/worlds/arm_world_fortress.sdf
python3 tools/smoke_simulation.py
python3 tools/smoke_serial.py
# Optional, runs the slider callback on a virtual display:
sudo apt install -y xvfb
python3 tools/smoke_gui.py
```

After a URDF change, rebuild the world:

```bash
python3 tools/generate_world.py
colcon build --symlink-install
```

## Version summary

| Item | Value |
|---|---|
| Ubuntu | 22.04 |
| ROS | Humble |
| Launch file | `simulation_humble.launch.py` |
| Simulator command | `ign gazebo` |
| World | `arm_world_fortress.sdf` |
| Bridge configuration | `bridge_fortress.yaml` |
| Transport message types | `ignition.msgs.*` |

## What was tested

The package build, SDF validation, joint motion, TF output, the slider callback test and the serial pseudo-terminal test were run against a Humble and Fortress 6.16.0 environment on Linux that was not a plain apt installation. The firmware was compiled for an Uno but not uploaded. Real servos and USB hardware are untested. Details and limits are in [VERIFICATION.md](VERIFICATION.md).

## Troubleshooting

- If the Gazebo window is blank, set `LIBGL_ALWAYS_SOFTWARE=1` before launching.
- If nodes from an earlier run show up or discovery looks stale, close other runs and open a fresh terminal.
- If you stop Gazebo, stop the whole launch before starting another one. Two simulators on the same topics will interfere with each other.

Gazebo and ROS pairing reference: https://gazebosim.org/docs/fortress/ros_installation/
