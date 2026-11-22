# التشغيل السريع

المشروع فيه نسختين منفصلتين، اختار اللي تناسب ROS عندك. ملف `docs/VERIFICATION.md` موضح الاختبارات اللي اتعملت، واللي لسه محتاج هاردوير حقيقي.

## لو عندك Ubuntu 22.04 وROS 2 Humble

افتح Terminal جديد:

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y ros-humble-ros-gz ros-humble-rviz2 \
  ros-humble-robot-state-publisher python3-colcon-common-extensions \
  python3-serial python3-tk git build-essential
```

نزّل ملفات المشروع من GitHub بعد رفعه، أو فك الـZIP. ادخل المجلد اللي جواه `src` و`README.md`، وبعدها:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation_humble.launch.py
```

افتح Terminal تاني، وادخل نفس مجلد المشروع:

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run arm_control sliders
```

غيّر joint1 إلى 20 وjoint2 إلى -20 درجة، وسيب الوقت 3 ثواني. اضغط **Send trajectory**. المفروض الحركة تظهر في Gazebo Fortress وRViz2 مع بعض.

التفاصيل: [دليل Humble](docs/HUMBLE.md).

## لو عندك Ubuntu 24.04 وROS 2 Jazzy

```bash
source /opt/ros/jazzy/setup.bash
sudo apt update
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher python3-colcon-common-extensions \
  python3-serial python3-tk git build-essential
```

من مجلد المشروع:

```bash
colcon build --symlink-install
source install/setup.bash
ros2 launch arm_simulation simulation.launch.py
```

في Terminal تاني من نفس المجلد:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 run arm_control sliders
```

ما تستخدمش نفس مجلدات `build` و`install` بين Humble وJazzy. استخدم نسخة مجلد منفصلة لكل واحدة.

## السيرفوهات

المحاكاة بتشتغل من غير هاردوير. ما توصلش طاقة السيرفوهات من USB أو 5V بتاع البوردة لو الحمل محتاج مصدر خارجي. لازم مصدر مناسب ومشترك أرضي مع Arduino. توصيل الإشارة: السيرفو الأول D9 والتاني D10.

ارفع `firmware/arm_servos/arm_servos.ino` على Arduino Uno، وراجع جدول التوصيل وتعليمات المعايرة في README. أول أمر ممكن يحرك السيرفوهات ناحية وضع المنتصف، فابدأ من غير حمل وبزوايا صغيرة.

على Humble، تجربة آمنة من غير كتابة على USB:

```bash
ros2 launch arm_simulation simulation_humble.launch.py hardware:=true dry_run:=true
```

بعد رفع الفيرموير ومراجعة التوصيل والأمان، اقفل التشغيل القديم وشغّل:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

على Jazzy استخدم `simulation.launch.py` بدل `simulation_humble.launch.py`.

النسختين اتبنوا واتجربت حركتهم فعليا في المحاكاة وRViz2. كود Arduino اتعمله compile، وتجربة إرسال USB اتعملت على منفذ افتراضي. رفعه على بوردة وتحريك سيرفوهات حقيقية لسه مطلوبين. Docker موجود كاختيار إضافي، لكن تشغيله نفسه مش متجرب.

الريبو المختار Public بموافقة صاحبه، فالدكتور يقدر يفتح اللينك مباشرة. والـPDF طالب تسليم لينك GitHub في الفورم، مش ZIP بس.
