# ROS 2 Robotic Arm Assignment

A four-revolute-joint arm with URDF, Gazebo Harmonic simulation, RViz2 feedback, a Python trajectory publisher, a slider GUI, and a two-servo Arduino USB bridge.

**Two separate tested variants:**

| Your machine | Use this guide | Launch |
|---|---|---|
| Ubuntu 22.04 + ROS 2 Humble | [Humble/Fortress quick start](docs/HUMBLE.md) | `simulation_humble.launch.py` |
| Ubuntu 24.04 + ROS 2 Jazzy | Native steps below | `simulation.launch.py` |

Both use modern Gazebo, not Gazebo Classic. Do not source Humble and Jazzy in one terminal. Use separate workspace build/install folders when switching distributions. The optional Jazzy Docker path remains untested.

The assignment PDF recommends modern `gz sim` with Jazzy in Section 3. The final deliverable is a repository link. Real board upload, servo response, and the physical full-pipeline demonstration still need to be done by the student. See [verification](docs/VERIFICATION.md).

## ابدأ من هنا

- لو جهازك Ubuntu 22.04 وعليه Humble، افتح [دليل Humble](docs/HUMBLE.md). النسخة دي اتجربت على Humble وGazebo Fortress فعليا، ومش محتاج تشيل Humble.
- لو عندك Ubuntu 24.04 وROS 2 Jazzy، نفّذ خطوات التشغيل المباشر.
- أول تشغيل للمحاكاة من غير سيرفوهات. الهاردوير مقفول افتراضيا، ومش هيتفتح غير لما تختار `hardware:=true dry_run:=false`.
- بعد فتح المحاكاة، شغّل أداة السلايدرز، غيّر الزوايا واضغط **Send trajectory**. المفروض نفس الحركة تظهر في Gazebo وRViz2.
- النسختين اتبنوا واتجربوا فعليا، Jazzy مع Harmonic وHumble مع Fortress، وفيه صور ونتائج اختبارات. تجربة السيرفوهات الحقيقية ورفع الكود على البوردة لسه مطلوبين.

## Repository layout

```text
src/
  arm_description/   URDF and RViz configuration
  arm_simulation/    Separate Harmonic/Fortress worlds, bridges and launches
  arm_control/       trajectory publisher, slider GUI, interpolation adapter
  arm_hardware/      USB serial bridge
firmware/arm_servos/  Arduino Uno/Nano sketch and strict packet parser
tools/               world generator and live smoke tests
tests/               Python and C++ tests
docs/                requirement checklist and test notes
test_results/        actual test reports and screenshots
```

These four packages are all project-specific packages. Standard ROS/Gazebo/Arduino dependencies are installed separately, not vendored into this repository.

## 1. Native Ubuntu 24.04 + Jazzy

First install ROS 2 Jazzy using the [official Ubuntu instructions](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html). The commands here assume `/opt/ros/jazzy/setup.bash` exists and the ROS apt repository is configured.

```bash
sudo apt update
sudo apt install -y ros-jazzy-desktop ros-jazzy-ros-gz \
  ros-jazzy-robot-state-publisher python3-colcon-common-extensions \
  python3-rosdep python3-serial python3-tk git build-essential
source /opt/ros/jazzy/setup.bash

git clone https://github.com/makkawy100/Lab2_ros.git ros2-robotic-arm
cd ros2-robotic-arm
# Only if rosdep has never been initialized on this machine:
# sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation.launch.py
```

This opens Gazebo and RViz2. The SDF world already contains the arm, generated from the committed URDF. Simulation starts unpaused. RViz uses `base_link` as its fixed frame and receives the actual Gazebo joint feedback.

In a **second terminal**:

```bash
source /opt/ros/jazzy/setup.bash
cd ~/ros2-robotic-arm  # adjust if you cloned elsewhere
source install/setup.bash
ros2 run arm_control sliders
```

Move a slider and press **Send trajectory**. A safe first test is `joint1 = 20 degrees`, `joint2 = -20 degrees`, duration `3 seconds`.

Or publish from Python without the GUI:

```bash
ros2 run arm_control trajectory_publisher --ros-args \
  -p 'positions:=[0.3, -0.4, 0.5, -0.2]' -p duration:=3.0
```

Headless simulation for testing:

```bash
ros2 launch arm_simulation simulation.launch.py headless:=true rviz:=false
```

## 2. Optional isolated Jazzy Docker option

For a Humble machine, prefer the tested [native Humble/Fortress variant](docs/HUMBLE.md). This optional path is only for running the Jazzy baseline without installing it into the host.

**Docker build/runtime has not been executed in the development test environment.** The application was tested with real Jazzy and Harmonic outside Docker. This option is supplied to keep the host Humble installation unchanged, not as a claim of container verification. Jazzy/Harmonic is the tested runtime pairing; the native apt installation procedure itself was not rerun.

These steps assume native Linux with a working X11/Xwayland `DISPLAY`. They do not cover Windows/WSL, macOS, a remote SSH display or Wayland-only sessions without Xwayland.

```bash
sudo apt update
sudo apt install -y docker.io xauth git
sudo systemctl start docker

git clone https://github.com/makkawy100/Lab2_ros.git ros2-robotic-arm
cd ros2-robotic-arm
sudo docker build -t ros2-arm:jazzy .
bash tools/docker_run.sh
```

The script shares only the X11 display authorization needed for GUI access, uses software rendering, and opens Gazebo/RViz. Docker images take disk space and the first build downloads dependencies. It does not install Jazzy into the host Humble environment.

In another host terminal, find the running container and open the sliders:

```bash
sudo docker exec -it ros2-arm bash -lc \
  'source /opt/ros/jazzy/setup.bash; source /ws/install/setup.bash; ros2 run arm_control sliders'
```

A one-shot command inside the same container:

```bash
sudo docker exec -it ros2-arm bash -lc \
  'source /opt/ros/jazzy/setup.bash; source /ws/install/setup.bash; ros2 run arm_control trajectory_publisher'
```

Stop with Ctrl+C in the launch terminal. If a container remains after an interrupted terminal, run `sudo docker stop ros2-arm`. For a headless container, use:

```bash
sudo docker run --rm --name ros2-arm --network host ros2-arm:jazzy \
  ros2 launch arm_simulation simulation.launch.py headless:=true rviz:=false
```

The Docker image entrypoint sources Jazzy and the built workspace for the command. The `docker exec` commands source them explicitly because exec bypasses the image entrypoint.

## 3. Architecture and message contract

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
/sim/joint{1..4}/cmd_pos              USB 115200 baud, ASCII S,a,b\n
       |                                      |
ros_gz_bridge -> Gazebo              Arduino parser -> servo PWM pins 9,10
       |
actual /arm/joint_state -> bridge -> /joint_states -> robot_state_publisher
                                                           |
                                                           v
                                                     /tf -> RViz2
```

Only Gazebo publishes joint feedback. There is no fake joint-state publisher hiding a disconnected simulator. Simulation and hardware subscribe to the same trajectory and use the same pure-Python interpolation code. In a combined launch they both use simulation time, so pausing Gazebo pauses the commanded trajectory. Real servos still hold their latest target; this is not an emergency stop.

Supported commands:

- Exactly `joint1`, `joint2`, `joint3`, `joint4`, each once; order may vary.
- One or more positions-only points, angles in radians.
- Every `time_from_start` strictly increases and is positive.
- Zero header timestamp means start immediately. Scheduled nonzero stamps are rejected rather than silently ignored.
- Velocities, accelerations and effort must be empty, as allowed by the assignment.
- Position limits are `[-pi/2, +pi/2]`; segment speed above `1.5 rad/s` is rejected. Increase duration if a command is rejected.
- A new accepted command replaces the remaining old trajectory continuously from the currently interpolated target. It is not a ROS action server.
- No collision planner is provided. Use small, slow motions and check ground/servo clearance. Arbitrary joint combinations can collide.

A standard ROS CLI message also works:

```bash
ros2 topic pub --once /arm_controller/joint_trajectory \
  trajectory_msgs/msg/JointTrajectory \
  '{joint_names: [joint1, joint2, joint3, joint4], points: [{positions: [0.3, -0.4, 0.5, -0.2], time_from_start: {sec: 3, nanosec: 0}}]}'
```

## 4. Dimensions and modelling assumptions

All lengths are in metres in the files.

| Link | Assignment length | Implemented size/direction |
|---|---:|---|
| base_link | 8 cm height | Cylinder, height 0.08, radius 0.04, bottom at z=0 |
| L1 | 12 cm height | Box, z-length 0.12 |
| L2 | 15 cm | Box, x-length 0.15 |
| L3 | 9 cm | Box, x-length 0.09 |
| end_effector | 6 cm | Box, x-length 0.06 |

Chain: `base_link -> joint1 -> L1 -> joint2 -> L2 -> joint3 -> L3 -> joint4 -> end_effector`.

`joint1` rotates about Z; joints 2, 3 and 4 rotate about local Y. The assignment gives lengths, not masses, widths, exact motor limits, axes or servo calibration. Those are documented engineering choices here, not measured properties of the user's hardware. All links include visual, collision and positive box/cylinder inertial properties. The end effector is one simple rigid box, not a powered opening/closing gripper. Its wrist connection is the fourth revolute joint.

The SDF adds a `world -> base_link` mounting constraint. The URDF still has the assignment's `base_link` root and all five physical links. `robot_state_publisher` may print the standard KDL warning about root-link inertia. TF/visualization work; no KDL dynamics solver is used.

Rebuild the SDF after changing the URDF:

```bash
python3 tools/generate_world.py
colcon build --symlink-install
```

The world uses local ground/light geometry and does not download Fuel models. Gazebo uses ideal velocity-based position actuation; this is kinematic command validation, not validation of real motor torque, payload or contact behaviour.

## 5. Hardware: Arduino Uno/Nano and at least two servos

Install the official Arduino IDE or CLI, board core `arduino:avr` and library **Servo**. Open `firmware/arm_servos/arm_servos.ino`, choose **Arduino Uno** (or compatible Nano with the right bootloader) and upload to your board.

CLI example after installing Arduino CLI:

```bash
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install Servo
arduino-cli board list
arduino-cli compile --fqbn arduino:avr:uno firmware/arm_servos
# Replace the port after checking board list:
arduino-cli upload --fqbn arduino:avr:uno --port /dev/ttyACM0 firmware/arm_servos
```

### Wiring

**Disconnect servo power while wiring. Do not power loaded servos from the board's 5 V pin or USB.** Use an external regulated supply sized for the actual servo model and stall current. Check the servo's voltage rating.

| Arduino connection | Connects to |
|---|---|
| D9 | Servo 1 signal, joint1/base rotation |
| D10 | Servo 2 signal, joint2/shoulder |
| GND | External supply negative and both servo ground wires |
| External supply positive | Both servo positive power wires, within their rated voltage |
| USB | PC to Arduino, board logic power and serial data |

Only the first two joints are wired in the minimum build. Joints 3 and 4 remain simulated. Mount horns safely with the logical neutral at 90 degrees, initially without a mechanical load. **The first valid command enables the servos and can move them toward neutral.** There is no position feedback from hobby servos and no physical emergency stop in this sketch. Keep a physical power switch within reach.

### USB protocol

115200 baud, 8N1, newline-terminated ASCII:

```text
S,107,67\n
```

This sets servo 1 to 107 degrees and servo 2 to 67 degrees. The wire contains a real LF byte, not a backslash followed by n. The firmware accepts `S,<0..180>,<0..180>`, replies `OK\n` on valid input or `ERR\n` otherwise. It rejects extra fields, invalid numbers and overflowed lines. Maximum receive buffer is 31 characters plus terminator. On USB loss it holds the last target rather than dropping a loaded arm. This hold behaviour is not a safety guarantee.

Host mapping: `clamp(round(offset + direction * radians * 180/pi), 0, 180)`. Defaults: offsets `[90,90]`, directions `[1,1]`. Reverse a servo with direction `-1`, not by reversing supply polarity. Real servo ranges must be checked mechanically. Send only small moves until calibration is confirmed.

### Start safely, then enable hardware

First test the bridge **without writing serial**:

```bash
ros2 launch arm_simulation simulation.launch.py hardware:=true dry_run:=true
```

Then publish with the GUI. The bridge prints `TX dry-run: S,...` and no board is accessed.

Once the sketch is uploaded, wiring checked and servo power safely supplied, stop the previous launch and run:

```bash
ros2 launch arm_simulation simulation.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

Open the sliders in another sourced terminal. One command now feeds Gazebo, RViz2 and both real servo channels. **The physical part of this test has not been performed for this repository.**

For hardware-only operation with no simulator:

```bash
ros2 run arm_hardware serial_bridge --ros-args \
  -p dry_run:=false -p port:=/dev/ttyACM0 \
  -p 'offsets:=[90.0,90.0]' -p 'directions:=[1.0,1.0]'
```

Close Arduino Serial Monitor before running the bridge. If access is denied, check `ls -l /dev/ttyACM0` and add your user to `dialout`, then log out/in. Do not use `chmod 777` on serial devices. Ports can be `/dev/ttyUSB0` on some boards.

For Docker, reconnect the USB port to the container explicitly by adding `--device /dev/ttyACM0:/dev/ttyACM0` to `tools/docker_run.sh`'s `docker run` command, and pass `hardware:=true dry_run:=false port:=/dev/ttyACM0` as script arguments. Do not expose the device until ready to enable the real servos. Container USB operation has not been tested here.

## 6. Tests you can rerun

Run with no other copy of this project active:

```bash
python3 -m unittest discover -s tests -v
g++ -std=c++11 -Wall -Wextra -Werror tests/test_protocol.cpp -o /tmp/arm-protocol-test
/tmp/arm-protocol-test
# After sourcing Jazzy and install/setup.bash:
gz sdf -k src/arm_simulation/worlds/arm_world.sdf
python3 tools/smoke_simulation.py
python3 tools/smoke_serial.py
# Optional GUI test requires Xvfb:
sudo apt install -y xvfb
python3 tools/smoke_gui.py
```

The smoke tests launch and stop their own simulation/bridge; they overwrite reports in `test_results/`. The serial test uses a pseudoterminal, not real hardware. The GUI test sets actual Tk sliders and invokes the actual button callback, then checks actual Gazebo feedback. It is not a physical mouse/servo test.

## 7. Submission

The selected repository is public with the owner's approval, so the instructor can open its URL without collaborator access. The owner still needs to submit the repository link through the course form. A ZIP is a useful backup but does not replace the required repository link unless the instructor agrees. Do not publish access tokens or board credentials.

## Sources

- User-supplied assignment PDF, 5 pages, Sections 1 through 6.
- [Gazebo Fortress/Humble pairing](https://gazebosim.org/docs/fortress/ros_installation/)
- [Gazebo Harmonic/ROS pairing and installation](https://gazebosim.org/docs/harmonic/ros_installation/)
- [Gazebo joint position controller parameters](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1JointPositionController.html)
- [Gazebo joint-state publisher](https://gazebosim.org/api/sim/8/classgz_1_1sim_1_1systems_1_1JointStatePublisher.html)
- [ros_gz_bridge Jazzy message mappings and YAML configuration](https://raw.githubusercontent.com/gazebosim/ros_gz/jazzy/ros_gz_bridge/README.md)
- [Official Jazzy ROS base Docker image definition](https://raw.githubusercontent.com/osrf/docker_images/master/ros/jazzy/ubuntu/noble/ros-base/Dockerfile)
