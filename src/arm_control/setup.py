from setuptools import setup
setup(name='arm_control', version='1.0.0', packages=['arm_control'],
      data_files=[('share/ament_index/resource_index/packages', ['resource/arm_control']),
                  ('share/arm_control', ['package.xml'])],
      install_requires=['setuptools'], zip_safe=True,
      maintainer='Project Maintainer', maintainer_email='maintainer@example.com',
      description='Robotic arm assignment', license='MIT',
      entry_points={'console_scripts': ['trajectory_publisher = arm_control.publisher:main', 'sliders = arm_control.sliders:main', 'sim_adapter = arm_control.sim_adapter:main']})
