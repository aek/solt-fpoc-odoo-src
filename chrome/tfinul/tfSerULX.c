/* ###################################################################

                    The Factory HKA C.A.
           Departamento de Integraci�n y aplicaciones
                    www.thefactory.com.ve
                     Caracas - Venezuela

   tfSerULX : Modulo de funciones para control del puerto serial en
              sistemas Unix/Linux

   Fecha: 30/11/2008
   Version: 1.2

###################################################################*/

#include "tfSerULX.h"

int fileDesc;			// File Descriptor
struct termios options;
/*
//####################################################################
//#         Function for open and configure the Serial Port          #
//####################################################################
*/
int openPort(char pathFile[])
{
    int i=0; 
    int retfun;
    FILE *portDesc;

    for(i=0;i<15;i++)
    {
    	pathPort[i] =NUL ;
    }

    if((portDesc=fopen(pathFile,"r"))!=NUL)
    {

        fscanf(portDesc,"%s",pathPort);
		fclose(portDesc);	 

        fileDesc=open(pathPort, O_RDWR | O_NOCTTY);
        if(fileDesc==-1)
        {
    	    printf("Imposible abrir el puerto de comunicaciones\n");
	    retfun=fileDesc;
        }
        else
        { 
	    fcntl(fileDesc,F_SETFL,0);
            tcgetattr(fileDesc,&options);
            cfsetispeed(&options,B9600);
            cfsetospeed(&options,B9600);
       	    options.c_cflag |= (CLOCAL | CREAD);
       	    options.c_cflag |= PARENB;
       	    options.c_cflag &= ~ PARODD;
       	    options.c_cflag &= ~CSTOPB;
       	    options.c_cflag &= ~CSIZE;
       	    options.c_cflag |= CS8;
       	    options.c_lflag &= ~(ICANON | ECHO | ECHOE | ISIG);
      	    options.c_oflag &= ~OPOST;
	    options.c_cc[VMIN] = 0;
	    options.c_cc[VTIME] = 0;
	    options.c_iflag |=(IGNPAR);
	    options.c_iflag &=~(INPCK | PARMRK | ISTRIP);
 	    tcsetattr(fileDesc,TCSANOW,&options);

 	    printf("Apertura del puerto exitosa \n");
	    retfun=1;

		}
    }
    else 
    {
		retfun=-1;
    }

	return retfun;

}

/*
//############################################
//#  Function to configure the Serial Port   #
//############################################
*/

int setConf()
{
	
	tcgetattr(fileDesc,&options);
	options.c_cc[VTIME] = 1;
	tcsetattr(fileDesc,TCSANOW,&options);
	return 0;
}
/*
//####################################################################
//#         Function for close the Serial Port          	     #
//####################################################################
*/

int closePort()
{
	
	if((close(fileDesc))==-1)
		return fileDesc;
	else
		return 1;

}
/*
//####################################################################
//#         Function for close the Serial Port          	     #
//####################################################################
*/
int writePort(char *pArray,int size)
{
	int n;
	int i;
	char char_out[2];

	char_out[0]=NUL;
	char_out[1]=NUL;

	for(i=0;i < size;i++)
	{
		char_out[0] = *pArray;
		char_out[1] = NUL;

		pArray++;

		n = write(fileDesc,char_out,1);

		if(n == -1)
			break;
	}

	if(n == -1)
		return n;
	else
		return 1;

}
/*
//####################################################################
//#         Function for read the Serial Port     	     	     #
//####################################################################
*/

int readPort(char *rBuffer)
{

	int bytes_read = 0;
	int n = 0;
	char char_in[2];

	char_in[0]=NUL;
	char_in[1]=NUL;

	do
	{
		n = read(fileDesc, char_in, 1);
		if(n>0)
		{
			bytes_read = bytes_read + n;
			*rBuffer = char_in[0];
			rBuffer++;
		}

	} while(n > 0);

	if(n == -1)
		return n;
	else
		return (bytes_read);
}




