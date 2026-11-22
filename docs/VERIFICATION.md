# Requirement and verification checklist

Verified on 22 November 2026. Read this together with the README, not as a claim of physical hardware completion.

## Actual environment and limits

- ROS 2 Jazzy + Gazebo Harmonic `gz-sim 8.10.0`, and a separate ROS 2 Humble + Gazebo Fortress `ign-gazebo 6.16.0`, Linux x86_64.
- Both real ROS/Gazebo runtimes were provisioned using RoboStack/conda, not full native Ubuntu 24.04/22.04 apt desktop installs. The native Ubuntu 24.04/Jazzy and Ubuntu 22.04/Humble instructions follow the official supported distro/simulator pairings, but were not reinstalled via apt during this work.
- Gazebo GUI and RViz2 were launched on a virtual X display with software OpenGL. Actual screenshots were inspected before/after a trajectory. This is a real rendered simulator, not an illustration.
- A binary dependency issue in that development runtime's bridge package required a local runtime-library repair before integration tests. That repair is not part of this repository and is not a claim of a clean conda bootstrap. The repository's colcon build itself passed for all four packages.
- No physical Arduino, servo, USB board upload or real PWM measurement was available.
- No Docker engine was available. The Dockerfile and runner are supplied, but container build, display sharing and USB passthrough remain unverified.
- Humble/Fortress is separately implemented and runtime-tested. See `HUMBLE.md`, `humble_*.json` and `humble_*.png`.

## Assignment, section by section

| PDF section | Requirement | Implementation and result |
|---|---|---|
| Overview | Model, visualize, publish trajectories, microcontroller bridge | Four ROS packages and firmware supplied. Software pipeline tested. Physical servo step remains. |
| Deadline | Announced separately | No deadline invented or submission claimed. |
| Deliverable | One GitHub repo, all project packages | `src/` contains all four project packages. External ROS dependencies are listed in README/package manifests, not copied into source. |
| 1 / Figure 1 | Base 8 cm, L1 12 cm, L2 15 cm, L3 9 cm, tip 6 cm | URDF dimensions checked by automated tests. World generated from that URDF via `gz sdf -p`. |
| 1 | Simple boxes/cylinders acceptable | Five primitive-shape physical links, no mesh downloads. |
| 2.1 | Links with visual, collision, inertial | All five links checked; positive masses and inertia diagonals. |
| 2.1 | Connected chain rooted at base_link | URDF chain validated. Four TF child frames received during simulation. World mounting fixed joint only in SDF. |
| 2.2 / 6.2 | At least four revolute joints | `joint1..joint4` with limits. Base Z rotation, other joints Y. |
| 3 | SDF world and ros_gz_bridge | `arm_world.sdf` embeds converted URDF model plus controller plugins; YAML bridges clock, commands and real feedback. `gz sdf -k` passed. |
| 3 | Model visible in gz sim | Actual Gazebo screenshot inspected. All four joints moved to commanded positions and back. |
| 4.1 | JointTrajectory names/radians/timing | Python message publisher uses exact URDF names, radians and sec/nanosec. Validation rejects malformed/nonfinite/out-of-range inputs. Multiple points and interpolation tested. |
| 4.1 | Velocity, acceleration, effort optional | Left empty; nonempty values rejected to avoid unsupported semantics. |
| 4.2 | Python publisher to exact assignment topic | `trajectory_publisher` publishes `/arm_controller/joint_trajectory`. Tested in actual ROS. |
| 4.3 | Same command moves Gazebo and RViz2 | Real Gazebo states bridge into `/joint_states`; robot_state_publisher produces TF. Actual before/after GUI screenshots inspected for both apps. |
| 4.3 | RViz RobotModel, fixed frame base_link | Committed RViz config; RViz screenshot showed model and Global Status OK. |
| 4.3 | Actual joint feedback into ROS | Feedback received from Gazebo, not command-derived fake states. Four target/home checks passed. |
| 5.1 | At least two physical servos and a board | Firmware targets Uno/Nano with D9/D10. Actual board and two servos must be supplied and tested by student. NOT completed physically. |
| 5.2 | ROS subscriber converts and sends to board | `serial_bridge`, real ROS subscription and real pyserial writes tested through a pseudoterminal. 250 packets, 41 distinct interpolated values; final packet `S,107,67`. |
| 5.3 | Implement both transport sides | USB serial sender and Arduino parser supplied. Firmware compiled for Arduino Uno using the actual Arduino AVR core and Servo library. |
| 5.3 | Convert radians, clamp degrees | Mapping and clamping unit tests passed. Firmware parser accepts 0..180 only. |
| 5.3 | Document transport/message format | README specifies 115200 8N1 and `S,a,b` followed by LF; ACK/ERR format included. |
| 5.4 | Pin mapping table and external power/common ground | README table has D9/D10, common ground and externally powered servo supply. First-command motion and no emergency-stop warning included. |
| 5.5 | Manual GUI publishes command | Actual Tk slider controls and actual Send button callback tested against real ROS and Gazebo states. Targets 30 and -20 degrees reached. |
| 5.5 | GUI command simultaneously moves simulation/RViz/real servos | Software branches tested; same launch/topic wiring provided. Full physical demonstration remains unverified. |
| 6.1 | README build/run/deps/transport/pins | Supplied, with Arabic quick start, native and Docker paths, troubleshooting and safety notes. |
| 6.2 | Firmware uploaded and >=2 servos respond | Firmware compile PASS. Board upload and physical response NOT tested, must be done by student. |
| 6.2 | Repository link submitted through form | Owner must submit. No form submission or instructor access is claimed. The selected repository is public, so instructor access does not require a collaborator invitation. |

## Tests that passed on both ROS variants

The same source code is shared, with separate simulator worlds, bridge configs and launch files. Test evidence without a prefix is Jazzy; `humble_` evidence is Humble. Firmware/parser tests are distro-independent. Native apt installation and Docker were not tested.

1. `colcon build --symlink-install`: all four packages built separately under Jazzy and Humble.
2. `gz sdf -k` (Harmonic) and `ign sdf -k` (Fortress): both committed worlds valid.
3. Python unit tests: **20 passed**, including names, times, finite numbers, limits, interpolation, preemption, servo conversion and URDF dimensions/properties.
4. C++ firmware parser: all **32,761 valid two-servo angle pairs** plus **14 malformed packets** passed.
5. Arduino Uno actual compile: **3,496 bytes flash**, **274 bytes static RAM**. This is compile evidence, not upload evidence.
6. Live ROS/Gazebo motion test: all four joints reached `[0.3, -0.4, 0.5, -0.2]` radians, then returned to zero; actual feedback and four TF children received. Numerical errors in this ideal simulated controller were below `0.000001 rad`. That precision is not promised for real servos.
7. Real ROS + pyserial PTY test: **250 packets**, **41 distinct**, final `S,107,67`. No physical serial adapter or board claimed.
8. GUI callback integration: Tk sliders set to 30/-20 degrees, button invoked, published one JointTrajectory, actual Gazebo joint1/joint2 reached the targets.
9. Gazebo and RViz2 visually inspected using actual screenshots in `test_results/`.

## Before the student submits

- Run the project on the intended machine.
- Upload the sketch to the actual board and wire two suitable externally powered servos with common ground.
- Check neutral, direction and safe ranges with horns unloaded.
- Demonstrate GUI -> same trajectory topic -> both visualizers and the physical servos.
- Capture the real demo as needed by the instructor.
- Check that the instructor can open the selected public repository, then submit its link through the announced form.

The files are implemented and software-tested. The assignment is not described as fully completed because the real hardware and submission steps remain.
