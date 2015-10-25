#ifndef _TFFNULX_H_
#define _TFFNULX_H_

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <malloc.h>
#include <dirent.h>
#include <time.h>
#include <sys/ioctl.h>

#define STX 0X02
#define ETX 0X03
#define ENQ 0X05
#define ACK 0X06
#define EOT 0X04
#define NAK 0X15
#define ETB 0X17
#define MASK 0X7FFF
#define NUL 0X00
#define LF 0X0A
/*
////////////////////////////////////////
// prototypes of the public functions //
////////////////////////////////////////
*/
int  OpenFpctrl(char path_port[]);
int  CloseFpctrl(void);
int  ReadFpStatus(char *ptrsts,char *ptrerr, char *path_file);
int  UploadStatus(char *ptrsts,char *ptrerr,char path_file[]);
int  UploadStatusCmd(char command[],char *path_file);
int  CheckFprinter(void);
int  SendCmd(char command[]);
int  SendNCmd(char *n_command);
int  SendFileCmd(char path_file[]);
int  UploadReportCmd(char command[],char *path_file);

#endif /*// _TFFNULX_H_*/
