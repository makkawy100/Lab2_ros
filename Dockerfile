FROM ros:jazzy-ros-base-noble
SHELL ["/bin/bash", "-c"]
RUN apt-get update && apt-get install -y --no-install-recommends \
    ros-jazzy-ros-gz ros-jazzy-rviz2 ros-jazzy-robot-state-publisher \
    python3-colcon-common-extensions python3-serial python3-tk \
    build-essential libgl1-mesa-dri mesa-utils \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /ws
COPY src/ /ws/src/
RUN source /opt/ros/jazzy/setup.bash && colcon build
COPY tools/container_entrypoint.sh /container_entrypoint.sh
RUN chmod +x /container_entrypoint.sh
ENTRYPOINT ["/container_entrypoint.sh"]
CMD ["ros2", "launch", "arm_simulation", "simulation.launch.py"]
