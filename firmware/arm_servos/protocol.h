#ifndef ARM_PROTOCOL_H
#define ARM_PROTOCOL_H
#include <stddef.h>
// Strict, bounded decimal parser. No heap allocation or permissive atoi().
inline bool parseServoCommand(const char* s, int& a, int& b) {
  if (!s || s[0] != 'S' || s[1] != ',') return false;
  size_t i = 2;
  int values[2] = {0,0};
  for (int n=0; n<2; ++n) {
    int digits=0;
    while (s[i]>='0' && s[i]<='9') {
      if (++digits>3) return false;
      values[n]=values[n]*10+(s[i++]-'0');
    }
    if (!digits || values[n]>180) return false;
    if (n==0) { if(s[i++]!=',') return false; }
  }
  if (s[i]!='\0') return false;
  a=values[0]; b=values[1]; return true;
}
#endif
