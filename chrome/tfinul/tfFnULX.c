/* ###################################################################

                    The Factory HKA C.A.
           Departamento de Integración y aplicaciones
                    www.thefactory.com.ve
                     Caracas - Venezuela

   tfFnULX.c : Modulo de funciones de interfaz de comandos para 
	      Impresoras de the Factory HKA C.A.

   Fecha: 01/12/2008
   Version: 1.2

###################################################################*/

#include "tfFnULX.h"
#include "tfSerULX.h"
/*////////////////////
//Global Variables//
//////////////////// */

char LRC;
char buffer[200];
char status[3];
char error[5];

/*//Prototypes of the private functions: */

int Wait_answer();
void Wait();
char Calc_xor(char *pArray, int size);
int Check_LRC(int size);
/*
//####################################################################
//								     #
//                       Private Functions    			     #
//								     #
//####################################################################
//#         Functions to wait answer from printer        	     #
//####################################################################
*/

int Wait_answer()
{
	int ret;
	double wait;
	time_t start,end;

	ret = 0;
	wait = 5;
	time(&start);

	do
	{
		ret=readPort(buffer);
		time(&end);
	}while(ret<1 && difftime(end,start) < wait);

	return ret;
}

void Wait()
{
	double wait;
	time_t start,end;

	wait = 1.5;
	time(&start);
	time(&end);

	while(difftime(end,start) < wait)
	{
		time(&end);
	}

}
/*
//####################################################################
//#         Function to calculate the LRC	        	     #
//####################################################################
*/
char Calc_xor(char *pArray, int size)
{
	unsigned int i;
	unsigned int aux;

	aux=(int)*pArray;
	pArray++;
	for(i=1;i<size;i++)
	{
		aux = aux ^ (int)*pArray;
		pArray++;
	}

	return (char)aux;
}
/*
//####################################################################
//#         Function to check the LRC of the data received     	     #
//####################################################################
*/
int Check_LRC(int size)
{
	char aux1;
	char aux2;

	aux1 = buffer[size-1];
	aux2 = Calc_xor(&buffer[1],(size-2));

	if(aux2 == aux1)
	{
		return 1;
	}
	else
	{
		return 0;
	}

}
/*
//####################################################################################################

//####################################################################
//								     #
//                       Public Functions    			     #
//								     #
//####################################################################
//#         Function to open the port 		 	     	     #
//####################################################################
*/
int OpenFpctrl(char path_port[])
{
	int iRet;
	
	iRet= openPort(path_port);

	return(iRet);

}
/*
//####################################################################
//#         Function to close the port 		 	     	     #
//####################################################################
*/
int  CloseFpctrl(void)
{
	int iRet;
	
	iRet= closePort();

	return(iRet);
}

/*
//####################################################################
//#         Function to send a command to  printer        	     #
//####################################################################
*/
int SendCmd(char command[])
{
	int i, size, ret;
	char *dir_trama, *trama;
	
	size = strlen(command);
	trama = (char *) malloc(size + 3);
	dir_trama = trama;
	ret = 0;

	*trama = STX;
	for(i=0; i< size ; i++)
	{
		trama++;
		*trama = command[i];
	}
	trama++;
	*trama = ETX;
	trama++;
	*trama = Calc_xor((dir_trama + 1),(size + 1));

	for(i=0;i<2;i++)
	{
		ret=0;
		readPort(buffer); 	//Para limpiar el buffer
		if( (writePort(dir_trama,(size + 3)) ) != -1)
		{
			ret = Wait_answer();
			if(ret==1 && buffer[0]==ACK)
				i++;
			else
				ret=0;
		}
		else
		{
			ret = 0;
		}
	}
	return ret;

}
/*
//############################################################################################
//#       Function to send to the printer a list of commands  that are in a file             #
//############################################################################################
*/
int SendFileCmd(char *path_file)
{
	int i;
	int fd_fich;
	int num_com;
	int retorno;
	int aux_ret;
	

	char aux;
	char command[125];

	aux_ret=0;
	fd_fich = open(path_file, O_RDWR);
	if(fd_fich!=-1)
	{
		num_com = 0;
		retorno = read(fd_fich,&aux,1);
		
		while((aux != 0) && (aux != LF) && (retorno!=-1))
		{
			i=1;	
			command[0]=aux;
			while((aux != LF) && (retorno!=0))
			{
				retorno=read(fd_fich,&command[i],1);
				aux=command[i];
				i++;
				if(retorno==0)
					aux_ret=1;
			}
			command[i-1]=NUL;
			retorno = SendCmd(command);
			if(retorno == 1)
			{
				num_com++;
				if(aux_ret==1)
				{
					retorno=-1;
				}
			}
			else
			{
				retorno=-1;
			}

			read(fd_fich,&aux,1);			
			
		}
	}
	return num_com;
					
						
}

/*
//#######################################################################
//#        Function that checks wheter the printer is connected         #
//#######################################################################
*/

int CheckFprinter()
{
	int i;
	int ret;
	char data;
	

	data = ENQ;
	ret = 0;
	setConf();

	//Rutina que envia un ENQ a la impresora y espera la respuesta 
	//en caso de no obtener respuesta o de NACK vuelve a enviar ENQ

	for(i=0;i<2;i++)
	{
		readPort(buffer);
		writePort(&data,1);
		ret = Wait_answer();
		if(ret>0)
		{
			i++;
			ret = 1;
		}
		else
		{
			Wait();
			ret = 0;
		}
	}

	return ret;
}


/*
//####################################################################################
//#    Function that reads information from the state and error of the printer       #
//####################################################################################
*/


int ReadFpStatus(char *ptrsts,char *ptrerr, char *path_file)
{
	

	int ret = 0;
	int i;
	int STS1;
	int STS2;
	int fd_fich;
	char data;
	char trama[31];
	
	strcpy(status,"   ");	
	strcpy(error,"     ");	
	data = ENQ;
	setConf();

	//Rutina que envia un ENQ a la impresora y espera la respuesta 
	//en caso de no obtener respuesta o de NACK vuelve a enviar ENQ

	

	for(i=1;i<2;i++)
	{
		readPort(buffer);
		writePort(&data,1);
		ret = Wait_answer();
		if(ret>0)
			i++;
		else
			Wait();
	}

	//Se verifica la trama recibida y se extrae el bit de estado y el de error

	if(ret==5)
	{	
		if(Check_LRC(ret))
		{
			STS1 = (int)buffer[1];
			STS2 = (int)buffer[2];
				
			switch (STS1)
			{
				case 0X40:
					strcpy(status,"0 ");
					*ptrsts = 0X00;
					break;
				case 0X41:
					strcpy(status,"2 ");
					*ptrsts = 0X02;
					break;
				case 0X42:
					strcpy(status,"3 ");
					*ptrsts = 0X03;
					break;
				case 0X60:
					strcpy(status,"4 ");
					*ptrsts = 0X04;
					break;
				case 0X61:
					strcpy(status,"5 ");
					*ptrsts = 0X05;
					break;
				case 0X62:
					strcpy(status,"6 ");
					*ptrsts = 0X06;
					break;
				case 0X70:
					strcpy(status,"7 ");
					*ptrsts = 0X07;
					break; 
				case 0X71:
					strcpy(status,"8 ");
					*ptrsts = 0X08;
					break;
				case 0X72:
					strcpy(status,"9 ");
					*ptrsts = 0X09;
					break;
				case 0X68:
					strcpy(status,"10 ");
					*ptrsts = 0X0A;
					break;
				case 0x69:
					strcpy(status,"11 ");
					*ptrsts = 0X0B;
					break;
				case 0x6A:
					strcpy(status,"12 ");
					*ptrsts = 0X0C;
					break;
				default:
					strcpy(status,"0 ");
					*ptrsts = 0X00;
					break;				
				}
		
			switch(STS2)
			{

				case 0X40:
					strcpy(error,"0   ");
					*ptrerr = 0X00;
					break;
				case 0X41:
					strcpy(error,"1   ");
					*ptrerr = 0X01;
					break;
				case 0X42:
					strcpy(error,"2   ");
					*ptrerr = 0X02;
					break;
				case 0X43:
					strcpy(error,"3   ");
					*ptrerr = 0X03;
					break;
				case 0X50:
					strcpy(error,"80   ");
					*ptrerr = 0X50;
					break;
				case 0X54:
					strcpy(error,"84   ");
					*ptrerr = 0X54;
					break;
				case 0X58:
					strcpy(error,"88   ");
					*ptrerr = 0X58;
					break;
				case 0X5C:
					strcpy(error,"92   ");
					*ptrerr = 0X5C;
					break;
				case 0X60:
					strcpy(error,"96   ");
					*ptrerr = 0X60;
					break;
				case 0x64:
					strcpy(error,"100  ");
					*ptrerr = 0X64;
					break;
				case 0X6C:
					strcpy(error,"108  ");
					*ptrerr = 0X6C;
					break;
				case 0X70:
					strcpy(error,"112  ");
					*ptrerr = 0X70;
					break;
				case 0X80:
					strcpy(error,"128  ");
					*ptrerr = 0X80;
					break;
				case 0X89:
					strcpy(error,"137  ");
					*ptrerr = 0X89;
					break;
				case 0X91:
					strcpy(error,"144  ");
					*ptrerr = 0X90;
					break; 
				case 0X92:
					strcpy(error,"145  ");
					*ptrerr = 0X91;
					break;
				case 0X99:
					strcpy(error,"153  ");
					*ptrerr = 0X99;
					break;
				default:
					break;
			}
			//Se envia un ACK indicando la recepcion correcta del mensaje
			data = ACK;
			writePort(&data,1);

			//Se almacena la información sobre el estado fiscal y el error de la impresora
			//en un archivo de texto
			strcpy(trama,"Retorno: Status:");
			strncat(trama,status,strlen(trama));
			strncat(trama," Error:",strlen(trama));
			strncat(trama,error,strlen(trama));
			if((fd_fich = open(path_file,O_RDWR | O_CREAT | O_TRUNC ,0777))!=-1)
			{
				write(fd_fich,trama,strlen(trama));
				close(fd_fich);
			}
			else
			{
				printf("Imposible crear el archivo de salida\n");
			}
			////////////////////////////////////////////////////////////////////


			return 1;

		}
		else
		{
			//Error:LRC incorrecta
			//Se envia un NACK indicando la recepcion erronea del mensaje
			data=NAK;
			writePort(&data,1);
			return 0;
			
		}
	}
	else
	{
		//Error en la trama
		return 0;
	}
	//Retorna 0 en caso de error de lectura o error en la trama recibida
	//Retorna 1 en caso de recepcion correcta del mensaje

}


int UploadStatusCmd(char command[],char *path_file)
{
	char aux;
	char *trama, *dir_trama;
	char bufferAux[500];
	int size,ret,i,j,ret2;
	int fd_fich;


	size=1;
	setConf();

	if(command[0]!='S')
	{
		//No se encuentra el indicador de comando S
		return 0;
	}
	else
	{
		size = strlen(command);
		//Asignaci�n memoria dinamica
		trama = malloc(size + 3);
		dir_trama = trama;

		//Construcci�n la trama 
		*trama = STX;					//Inicio del mensaje

		for(i=0; i< size ; i++)				//Comando
		{
			trama++;
			*trama = command[i];
		}
		trama++;
		*trama = ETX;				//Fin del mensaje
		trama++;
		*trama = Calc_xor((dir_trama + 1),(size + 1));	//CRC

		//Rutina que envia la trama a la impresora y espera la respuesta 
		//en caso de no obtener respuesta o de NACK vuelve a enviar la trama
		for(i=0;i<2;i++)
		{
			ret=0;
			readPort(buffer);
			writePort(dir_trama,(size + 3));
			ret = Wait_answer();
			if(ret>0)
			{	
				i++;
			}
			else
			{
				Wait();
			}
		}

		if((ret>1) && (buffer[0]!=NAK))
		{
			if((ret2 = Check_LRC(ret))==1)
			{
				fd_fich=open(path_file,O_RDWR | O_CREAT | O_TRUNC ,0777);
				j=0;
					
				for(i=0;i<=ret;i++)
				{
					if((buffer[i]!=LF)  && (buffer[i]!= STX) && (buffer[i]!= ETX) && (buffer[i]!= NUL) && (buffer[i-1]!=ETX))
					{
						bufferAux[j]=buffer[i];
						j++;						
					}
					
				}
				
				write(fd_fich,&bufferAux[0],j);				
				close(fd_fich);
				
				//Se envia ACK para indicar recepci�n correcta				
				aux=ACK;
				writePort(&aux,1);
				return 1;
			}
			else
			{
				//Se envia NACK para indicar recepci�n erronea
				aux=NAK;
				writePort(&aux,1);
				return 0;
			}

		}
		else
		{	
			//Se envia NACK para indicar recepci�n erronea
			aux=NAK;
			writePort(&aux,1);
			return 0;
		} 
	}

	//Retorna 0 para error en la descarga del reporte de estado
	//Retorna 1 para descarga exitosa del reporte de estado
}

/* ################################################################################################################# */	
int UploadReportCmd(char command[],char *path_file)	
{	
	char aux;	
	char *trama, *dir_trama;	
	int size;	
	char bufferAux[500];
	int i,j;	
	int bytes_read;	
	int fd_fich;	
	int ret;
	int retorno=0;

	trama=&command[0];	
	setConf();

	if(command[0]=='U')	//Se encuentra el indicador de comando U	
	{
		//Asignaci�n de memoria para almacenar la trama
		size = strlen(command);	
		trama = malloc(size + 3);	
		dir_trama = trama;	
		ret = 0;

		//Construcci�n de la trama

		*trama = STX;	
		for(i=0; i< size ; i++)	
		{	
			trama++;	
			*trama = command[i];	
		}	
		trama++;	
		*trama = ETX;	
		trama++;	
		*trama = Calc_xor((dir_trama + 1),(size + 1));	
	
		/* //Env�o de la trama */

		for(i=0;i<2;i++)	
		{	
			bytes_read=0;	
			readPort(buffer);		/* //Limpieza  del buffer	*/
			if( (writePort(dir_trama,(size + 3)) ) != -1)	
			{	
				bytes_read = Wait_answer();	
				if(bytes_read==1 && buffer[0]==ENQ)	
					i++;	
				else	
					bytes_read=0;	
			}	
			else	
			{	
				bytes_read = 0;	
			}	
		}	

		/* //Chequeo de la respuesta recibida */
	
		if(bytes_read>0)	
		{	
			fd_fich=open(path_file,O_RDWR | O_CREAT | O_TRUNC ,0777);
			while(aux!=EOT)	
			{	
				aux=ACK;	
				writePort(&aux,1);	
				bytes_read = Wait_answer();	
	
				if(bytes_read>0)	
				{	
					aux=buffer[0];	
					if(aux!=EOT)	
					{	
						ret=Check_LRC(bytes_read);	
						if(ret==1)	
						{	
							j=0;
							for(i=0;i<=bytes_read;i++)
							{
								if((buffer[i]!=LF)  && (buffer[i]!= STX) && (buffer[i]!= ETX) && (buffer[i]!= NUL) && (buffer[i-1]!=ETX))
								{
									bufferAux[j]=buffer[i];
									j++;						
								}
									
							}
						
							write(fd_fich,&bufferAux[0],j);
							retorno=1;
						}	
						else	
						{	
							aux=NAK;	
							writePort(&aux,1);	
							aux=EOT;	
						}	
					}
					else
					{
						write(fd_fich,&aux,1);
					}	
				}	
				else	
				{		
					aux=EOT;	
				}	
			}
			close(fd_fich);	
		}
	
	}


	return retorno;	
}	

