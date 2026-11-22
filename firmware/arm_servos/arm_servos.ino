// Arduino Uno / Nano ATmega328P. Install the official Arduino Servo library.
#include <Servo.h>
#include "protocol.h"
Servo baseServo, shoulderServo;
char line[32]; size_t used=0; bool overflowed=false; bool attached=false;
void setup() { Serial.begin(115200); }
void acceptLine() {
  int a,b;
  if (!overflowed && parseServoCommand(line,a,b)) {
    // No pulses at startup. First valid command enables both outputs.
    baseServo.write(a); shoulderServo.write(b);
    if(!attached) { baseServo.attach(9); shoulderServo.attach(10); attached=true; }
    baseServo.write(a); shoulderServo.write(b);
    Serial.println("OK");
  } else Serial.println("ERR");
}
void loop() {
  while(Serial.available()) {
    char c=(char)Serial.read();
    if(c=='\r') continue;
    if(c=='\n') { line[used]='\0'; acceptLine(); used=0; overflowed=false; }
    else if(used<sizeof(line)-1 && !overflowed) line[used++]=c;
    else overflowed=true;
  }
  // Hold last setpoint if USB stops. This is NOT an emergency-stop system.
}
