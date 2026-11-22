#include <cassert>
#include <iostream>
#include <string>
#include <cstdlib>
#include "../firmware/arm_servos/protocol.h"
int main(){
 int a=-1,b=-1;
 assert(parseServoCommand("S,0,180",a,b)&&a==0&&b==180);
 assert(parseServoCommand("S,90,45",a,b)&&a==90&&b==45);
 const char* bad[]={"","S","S,","S,90","S,90,","S,-1,90","S,181,90","S,90,999","X,90,90","S,90,90,1","S,90,90junk","S,0000,9","S,9.5,9","S, 9,9"};
 for(auto s:bad)assert(!parseServoCommand(s,a,b));
 for(int i=0;i<=180;i++)for(int j=0;j<=180;j++){
  std::string s="S,"+std::to_string(i)+","+std::to_string(j);
  assert(parseServoCommand(s.c_str(),a,b)&&a==i&&b==j);
 }
 std::cout<<"PASS: 32761 valid angle pairs and 14 malformed packets\n";
}
