# Requirement and verification checklist

Last updated 22 November 2026. Read this together with the README. It does not claim that the physical hardware part is done.

## Test environment and limits

- ROS 2 Humble with Gazebo Fortress (`ign-gazebo 6.16.0`) on Linux x86_64.
- The ROS and Gazebo runtime used for testing was a RoboStack/conda environment, not a native Ubuntu 22.04 apt installation. The apt-based instructions in the README follow the officially supported Humble and Fortress pairing but were not reinstalled and re-run from scratch.
- The Gazebo GUI and RViz2 were run on a virtual X display with software OpenGL, and the screenshots in `test_results/` come from that run.
- A binary dependency problem in that test environment's bridge package needed a local runtime-library fix before the integration tests would run. That fix is not part of this repository.
- The newer setuptools in that environment rejected `colcon build --symlink-install`, so the build there used plain `colcon build`. The symlink-install build on native Ubuntu was not tested.
- No Arduino board, servo or USB adapter was available. Nothing was uploaded and no PWM output was measured.

## Assignment requirements

| Section | Requirement | Implementation and status |
|---|---|---|
| Overview | Model, visualize, publish trajectories, microcontroller bridge | Four ROS packages and firmware. Software pipeline tested. The physical servo step is open. |
| Deliverable | One GitHub repository with all project packages | `src/` holds all four packages. External dependencies are listed in the README and package manifests. |
| 1 / Figure 1 | Base 8 cm, L1 12 cm, L2 15 cm, L3 9 cm, tip 6 cm | URDF dimensions are checked by unit tests. The world is generated from the URDF with `ign sdf -p`. |
| 1 | Simple boxes and cylinders are acceptable | Five primitive-shape links, no meshes. |
| 2.1 | Links with visual, collision and inertial elements | All five links checked, with positive mass and inertia. |
| 2.1 | Connected chain rooted at base_link | Chain checked by a unit test. Four child frames were received on `/tf` during simulation. The world mount joint exists only in the SDF. |
| 2.2 / 6.2 | At least four revolute joints | `joint1` to `joint4`, with limits. Joint 1 rotates about Z, the others about Y. |
| 3 | SDF world and ros_gz_bridge | `arm_world_fortress.sdf` contains the converted model and controller plugins. `bridge_fortress.yaml` bridges the clock, the commands and the joint feedback. `ign sdf -k` passed. |
| 3 | Model visible in Gazebo | Screenshot checked. All four joints moved to the commanded positions and back. |
| 4.1 | JointTrajectory names, radians, timing | The publisher uses the exact URDF joint names. Malformed, non-finite and out-of-range inputs are rejected. Multi-point trajectories and interpolation are covered by tests. |
| 4.1 | Velocity, acceleration, effort optional | Left empty. Non-empty values are rejected because they are not supported. |
| 4.2 | Python publisher on the assignment topic | `trajectory_publisher` publishes on `/arm_controller/joint_trajectory`. Tested with ROS running. |
| 4.3 | One command moves Gazebo and RViz2 | Gazebo joint states are bridged to `/joint_states`, and `robot_state_publisher` produces the TF. Before and after screenshots of both applications were checked. |
| 4.3 | RViz RobotModel, fixed frame base_link | RViz configuration is committed. The screenshot shows the model with status OK. |
| 4.3 | Joint feedback into ROS | Feedback comes from Gazebo, not from the command. Target and home positions were reached in the live test. |
| 5.1 | At least two servos and a board | Firmware for Uno/Nano on D9 and D10. A board and two servos still have to be connected and tested. Not done. |
| 5.2 | ROS subscriber converts and sends to the board | `serial_bridge` was tested with a real ROS subscription and pyserial over a pseudo-terminal: 251 packets, 41 distinct values, final packet `S,107,67`. |
| 5.3 | Both sides of the transport | Serial sender and Arduino parser. The firmware compiled for Arduino Uno with the AVR core and the Servo library. |
| 5.3 | Convert radians, clamp degrees | Mapping and clamping covered by unit tests. The firmware accepts 0 to 180 only. |
| 5.3 | Document the message format | README describes 115200 8N1 and `S,a,b` followed by LF, plus the OK and ERR replies. |
| 5.4 | Pin table, external power, common ground | README table lists D9, D10, common ground and an external supply, with warnings about first-command motion and the missing emergency stop. |
| 5.5 | Manual GUI publishes a command | The Tk slider callback was tested against ROS and Gazebo feedback. Targets of 30 and -20 degrees were reached. |
| 5.5 | One command moves simulation, RViz2 and the servos | The software branches were tested. The physical demonstration is still open. |
| 6.1 | README with build, run, dependencies, transport, pins | Provided. |
| 6.2 | Firmware uploaded, two servos respond | Compile passed. Upload and servo response are untested. |
| 6.2 | Repository link submitted | To be done through the course form. |

## Results

1. `colcon build`: all four packages built (plain build, see limits above).
2. `ign sdf -k`: the world file is valid.
3. Python unit tests: 20 passed. They cover joint names, times, finite values, limits, interpolation, preemption, servo conversion and the URDF dimensions and properties.
4. C++ firmware parser: all 32,761 valid angle pairs and 14 malformed packets handled correctly.
5. Arduino Uno compile: 3,496 bytes of flash and 274 bytes of RAM. This shows that it compiles, not that it runs on a board.
6. Live ROS and Gazebo test: all four joints reached `[0.3, -0.4, 0.5, -0.2]` rad and returned to zero, with feedback and four child frames on `/tf`. Errors were below 0.000001 rad. This is an ideal simulated controller, so real servos will be less precise.
7. ROS with pyserial over a pseudo-terminal: 251 packets, 41 distinct, final `S,107,67`. No physical serial device was used.
8. GUI callback: the Tk sliders were set to 30 and -20 degrees, the button was invoked, one JointTrajectory was published and joints 1 and 2 reached the targets in Gazebo.
9. Screenshots of Gazebo and RViz2 before and after a command are in `test_results/`.

## Still to do

- Run the project on the target Ubuntu 22.04 machine.
- Upload the sketch to a board and wire two externally powered servos with a common ground.
- Check neutral position, direction and safe ranges with the horns unloaded.
- Demonstrate one command moving Gazebo, RViz2 and the servos together.
- Submit the repository link through the course form.
