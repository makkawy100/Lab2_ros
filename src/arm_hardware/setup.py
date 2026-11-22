from setuptools import setup
setup(name='arm_hardware', version='1.0.0', packages=['arm_hardware'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/arm_hardware']),
                  ('share/arm_hardware', ['package.xml'])],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Project Maintainer', maintainer_email='maintainer@example.com',
      description='Robotic arm assignment', license='MIT',
      entry_points={'console_scripts': ['serial_bridge = arm_hardware.serial_bridge:main']})
