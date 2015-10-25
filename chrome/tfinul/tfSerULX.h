#ifndef _TFSERULX_H_
#define _TFSERULX_H_

#include <termios.h>

char pathPort[15];
int openPort(char pathFile[]);
int closePort();
int writePort(char *pArray,int size);
int readPort(char *rBuffer);
int setConf();

#endif
