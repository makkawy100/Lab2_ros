# ROS 2 Robotic Arm (Lab 2)

A four-joint robotic arm for a university robotics assignment. The project contains a URDF model, a Gazebo Fortress simulation, RViz2 visualization, a Python trajectory publisher, a slider GUI, and a USB serial bridge to an Arduino that drives two servos.

Target platform: Ubuntu 22.04, ROS 2 Humble, Gazebo Fortress (`ign gazebo`).

The project uses Gazebo Fortress (Gazebo Sim 6), the version officially paired with Humble, rather than Gazebo Classic.

**Status.** The simulation pipeline was tested in simulation only. The Arduino firmware was compiled but never uploaded, and no physical servo has been driven yet. See [docs/VERIFICATION.md](docs/VERIFICATION.md) for what was and was not tested.

## Repository layout

```text
src/
  arm_description/   URDF and RViz configuration
  arm_simulation/    Fortress world, bridge configuration, launch file
  arm_control/       trajectory publisher, slider GUI, simulation adapter
  arm_hardware/      USB serial bridge
firmware/arm_servos/ Arduino sketch and command parser
tools/               world generator and smoke tests
tests/               Python and C++ unit tests
docs/                setup guide and requirement checklist
test_results/        output of the test runs and screenshots
```

All four packages are written for this project. Standard ROS, Gazebo and Arduino dependencies are installed separately.

## 1. Install and run

These steps assume ROS 2 Humble is already installed on Ubuntu 22.04 (`/opt/ros/humble/setup.bash` exists). If not, follow the [official Humble installation guide](https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html) first.

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y ros-humble-ros-gz ros-humble-rviz2 \
  ros-humble-robot-state-publisher python3-colcon-common-extensions \
  python3-rosdep python3-serial python3-tk git build-essential

cd ~
git clone https://github.com/makkawy100/Lab2_ros.git ros2-robotic-arm
cd ros2-robotic-arm

# Only needed the first time rosdep is used on this machine:
# sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro humble

colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation_humble.launch.py
```

This opens Gazebo Fortress and RViz2. The world file already contains the arm, converted from the URDF in this repository. RViz2 uses `base_link` as the fixed frame and shows the joint positions reported by Gazebo. No hardware is enabled by default.

In a second terminal:

```bash
source /opt/ros/humble/setup.bash
cd ~/ros2-robotic-arm
source install/setup.bash
ros2 run arm_control sliders
```

Move the sliders and press **Send trajectory**. A safe first test is `joint1 = 20`, `joint2 = -20` degrees with a duration of 3 seconds.

The same motion can be sent without the GUI:

```bash
ros2 run arm_control trajectory_publisher --ros-args \
  -p 'positions:=[0.3, -0.4, 0.5, -0.2]' -p duration:=3.0
```

To run the simulation without windows (useful for testing):

```bash
ros2 launch arm_simulation simulation_humble.launch.py headless:=true rviz:=false
```

More notes and troubleshooting are in [docs/HUMBLE.md](docs/HUMBLE.md).

## 2. Architecture and message contract

```text
Python publisher / Tk sliders
       |
       v
/arm_controller/joint_trajectory   trajectory_msgs/msg/JointTrajectory
       |                                      |
       v                                      v
arm_control/sim_adapter              arm_hardware/serial_bridge
50 Hz linear interpolation           50 Hz interpolation, rad -> degrees
       |                                      |
/sim/joint{1..4}/cmd_pos              USB 115200 baud, ASCII "S,a,b\n"
       |                                      |
ros_gz_bridge -> Gazebo              Arduino parser -> servo pins 9, 10
       |
/arm/joint_state -> bridge -> /joint_states -> robot_state_publisher
                                                           |
                                                           v
                                                     /tf -> RViz2
```

Joint feedback comes only from Gazebo. Nothing in the project publishes fake joint states. Simulation and hardware subscribe to the same trajectory topic and share the same interpolation code (`arm_control/core.py`). When both run in one launch, they use simulation time, so pausing Gazebo also pauses the commanded trajectory. Real servos keep holding their last target, so this is not an emergency stop.

Accepted commands:

- Exactly `joint1` to `joint4`, each once, in any order.
- One or more points with positions only, in radians.
- `time_from_start` positive and strictly increasing across points.
- A zero header stamp, meaning "start now". Commands with a nonzero stamp are rejected instead of being silently ignored.
- Empty velocities, accelerations and effort.
- Positions within `[-pi/2, +pi/2]` and a speed of at most `1.5 rad/s` per segment. If a command is rejected for speed, increase the duration.
- A new accepted command replaces the remaining part of the old one, starting from the current interpolated position. This is a plain topic interface, not an action server.
- There is no collision checking. Use small, slow motions and watch the clearance to the ground and to the servo mounts.

A command can also be sent with the standard ROS CLI:

```bash
ros2 topic pub --once /arm_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  '{joint_names: [joint1, joint2, joint3, joint4], points: [{positions: [0.3, -0.4, 0.5, -0.2], time_from_start: {sec: 3, nanosec: 0}}]}'
```

## 3. Dimensions and modelling assumptions

Lengths are in metres in the files.

| Link | Assignment length | Implementation |
|---|---:|---|
| base_link | 8 cm height | Cylinder, height 0.08, radius 0.04, bottom at z = 0 |
| L1 | 12 cm height | Box, z-length 0.12 |
| L2 | 15 cm | Box, x-length 0.15 |
| L3 | 9 cm | Box, x-length 0.09 |
| end_effector | 6 cm | Box, x-length 0.06 |

Chain: `base_link -> joint1 -> L1 -> joint2 -> L2 -> joint3 -> L3 -> joint4 -> end_effector`.

`joint1` rotates about Z. Joints 2, 3 and 4 rotate about their local Y axis. The assignment gives only link lengths, so the masses, widths, joint limits and axis choices are my own assumptions and do not come from measurements of the real hardware. Every link has visual, collision and inertial elements. The end effector is a single rigid box, not a gripper; the fourth joint is the wrist.

The SDF world adds a fixed `world -> base_link` joint so the arm stays in place. The URDF keeps `base_link` as its root. `robot_state_publisher` may print the usual KDL warning about inertia on the root link. It does not affect the TF tree or the visualization.

After changing the URDF, regenerate the world and rebuild:

```bash
python3 tools/generate_world.py
colcon build --symlink-install
```

The world uses a local ground plane and light, so no Fuel models are downloaded. Gazebo drives the joints with an ideal velocity-based position controller. The simulation checks the commanded kinematics only. It says nothing about real motor torque, payload or contact behaviour.

## 4. Hardware: Arduino Uno/Nano with two servos

Install the Arduino IDE or `arduino-cli`, the `arduino:avr` core and the **Servo** library. Open `firmware/arm_servos/arm_servos.ino`, select Arduino Uno (or a Nano with the matching bootloader) and upload.

With `arduino-cli`:

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install Servo
arduino-cli board list
arduino-cli compile --fqbn arduino:avr:uno firmware/arm_servos
# Use the port reported by "board list":
arduino-cli upload --fqbn arduino:avr:uno --port /dev/ttyACM0 firmware/arm_servos
```

### Wiring

**Disconnect servo power while wiring. Do not power loaded servos from the 5 V pin or from USB.** Use an external regulated supply that matches the servo voltage rating and can deliver the stall current.

| Arduino | Connects to |
|---|---|
| D9 | Servo 1 signal (joint1, base rotation) |
| D10 | Servo 2 signal (joint2, shoulder) |
| GND | External supply negative and both servo ground wires |
| External supply positive | Both servo power wires |
| USB | PC to Arduino (logic power and serial data) |

Only joints 1 and 2 are wired in the minimal build. Joints 3 and 4 exist only in simulation. Mount the servo horns with the logical neutral at 90 degrees, first without a load. **The first valid command enables the servos, and they may move toward the commanded position immediately.** Hobby servos give no position feedback and the sketch has no emergency stop, so keep a power switch within reach.

### USB protocol

115200 baud, 8N1, newline-terminated ASCII:

```text
S,107,67\n
```

This sets servo 1 to 107 degrees and servo 2 to 67 degrees. The terminator is a real LF byte. The firmware accepts `S,<0..180>,<0..180>` and replies `OK\n` for valid input or `ERR\n` otherwise. It rejects extra fields, malformed numbers and lines that overflow the 31-character buffer. If USB is lost, it holds the last target.

Host-side mapping: `clamp(round(offset + direction * radians * 180/pi), 0, 180)`. The defaults are offsets `[90, 90]` and directions `[1, 1]`. To reverse a servo, set its direction to `-1`. Check the real mechanical range before using larger motions.

### Enabling the hardware

First run the bridge in dry-run mode, which writes nothing to the serial port:

```bash
ros2 launch arm_simulation simulation_humble.launch.py hardware:=true dry_run:=true
```

Publish a command with the sliders and the bridge logs lines like `TX dry-run: S,...`.

After the sketch is uploaded, the wiring is checked and the servo supply is connected, stop that launch and run:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

Start the sliders in another sourced terminal. A single command now drives Gazebo, RViz2 and both servo channels. **This physical step has not been tested yet.**

For hardware only, without the simulator:

```bash
ros2 run arm_hardware serial_bridge --ros-args \
  -p dry_run:=false -p port:=/dev/ttyACM0 \
  -p 'offsets:=[90.0, 90.0]' -p 'directions:=[1.0, 1.0]'
```

Close the Arduino Serial Monitor first, because it holds the port. If access is denied, check `ls -l /dev/ttyACM0` and add your user to the `dialout` group, then log out and back in. Some boards appear as `/dev/ttyUSB0`.

## 5. Running the tests

Make sure no other copy of the project is running.

```bash
python3 -m unittest discover -s tests -v
g++ -std=c++11 -Wall -Wextra -Werror tests/test_protocol.cpp -o /tmp/arm-protocol-test
/tmp/arm-protocol-test

# The following need the built workspace sourced (source install/setup.bash):
ign sdf -k src/arm_simulation/worlds/arm_world_fortress.sdf
python3 tools/smoke_simulation.py
python3 tools/smoke_serial.py

# Optional GUI test, needs a virtual display:
sudo apt install -y xvfb
python3 tools/smoke_gui.py
```

The smoke tests start and stop their own simulation or bridge and overwrite the reports in `test_results/`. The serial test uses a pseudo-terminal, not a real board. The GUI test sets the Tk sliders from code, calls the button callback and checks the joint feedback from Gazebo. It is not a test with a physical mouse or servos.

## 6. Submission notes

The repository is public, so it can be opened without being added as a collaborator. Do not commit access tokens or other credentials.

## References

- [Gazebo Fortress and ROS 2 Humble pairing](https://gazebosim.org/docs/fortress/ros_installation/)
- Assignment handout (PDF), Sections 1 to 6.
