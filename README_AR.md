# التشغيل السريع

النسخة دي مخصصة لـ **Ubuntu 22.04 وROS 2 Humble مع Gazebo Fortress**. مش محتاج تنزل Jazzy ولا أي ROS تاني. ملف `docs/VERIFICATION.md` موضح الاختبارات اللي اتعملت، واللي لسه محتاج هاردوير حقيقي.

## التثبيت والتشغيل

افتح Terminal جديد:

```bash
source /opt/ros/humble/setup.bash
sudo apt update
sudo apt install -y ros-humble-ros-gz ros-humble-rviz2 \
  ros-humble-robot-state-publisher python3-colcon-common-extensions \
  python3-serial python3-tk git build-essential
```

نزّل ملفات المشروع من GitHub (Code ثم Download ZIP أو git clone)، وادخل المجلد اللي جواه `src` و`README.md`، وبعدها:

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

التفاصيل وحلول المشاكل: [دليل Humble](docs/HUMBLE.md).

## السيرفوهات

المحاكاة بتشتغل من غير هاردوير. ما توصلش طاقة السيرفوهات من USB أو 5V بتاع البوردة لو الحمل محتاج مصدر خارجي. لازم مصدر مناسب ومشترك أرضي مع Arduino. توصيل الإشارة: السيرفو الأول D9 والتاني D10.

ارفع `firmware/arm_servos/arm_servos.ino` على Arduino Uno، وراجع جدول التوصيل وتعليمات المعايرة في README. أول أمر ممكن يحرك السيرفوهات ناحية وضع المنتصف، فابدأ من غير حمل وبزوايا صغيرة.

تجربة آمنة من غير كتابة على USB:

```bash
ros2 launch arm_simulation simulation_humble.launch.py hardware:=true dry_run:=true
```

بعد رفع الفيرموير ومراجعة التوصيل والأمان، اقفل التشغيل القديم وشغّل:

```bash
ros2 launch arm_simulation simulation_humble.launch.py \
  hardware:=true dry_run:=false port:=/dev/ttyACM0
```

## إيه اللي اتجرب

المشروع اتبنى واتجربت حركته فعليا في المحاكاة وRViz2 على Humble وFortress. كود Arduino اتعمله compile، وتجربة إرسال USB اتعملت على منفذ افتراضي. رفعه على بوردة وتحريك سيرفوهات حقيقية لسه مطلوبين.

الريبو المختار Public بموافقة صاحبه، فالدكتور يقدر يفتح اللينك مباشرة. والـPDF طالب تسليم لينك GitHub في الفورم، مش ZIP بس.
