/* ###################################################################

                    The Factory HKA C.A.
           Departamento de Integracion y aplicaciones
                    www.thefactory.com.ve
                     Caracas - Venezuela

   tfinulxc.c : Modulo de prueba comunicación y envio de comandos
               a impresoras de The Factory HKA

   Fecha: 10/12/2008
   Version: 1.2

###################################################################*/

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "tfFnULX.c"
#include "tfSerULX.c"


int main(int argc, char *argv[])
{

   char path_file []="./Puerto.txt";
   char *argFuncion;
   char *argComOrArch;
   char *argRutArch;
   char sts;
   char err;
   char iRet_cadena[3]="   ";
   int iRet;
   FILE *fileDesc;
	


   iRet=OpenFpctrl(path_file);
   
   if(iRet!=-1)
   {


	switch(argc)
	{
		case 2:
			argFuncion = argv[1];
			if((strcmp(argFuncion,"CheckFprinter")==0))
			{
				iRet=0;
				iRet = CheckFprinter();

				if(iRet)
					printf("Impresora en línea\n");	
				else
					printf("No se recibio respuesta de la impresora\n");
			}
			else 
			{
				printf("Funcion: no Valida");
				iRet=-1;
			}
			
			break;

		case 3:
			
   			argFuncion= argv[1];
        		argComOrArch= argv[2];
	
			if((strcmp(argFuncion,"SendCmd")==0))
			{
				iRet=0;
				iRet = SendCmd(argComOrArch);

				if(iRet==1)
					printf("Comando enviado correctamente\n");		
				else
					printf("Error en el envío del comando\n");
			}
			else if(strcmp(argFuncion,"SendFileCmd")==0)
			{
				iRet=0;
				iRet = SendFileCmd(argComOrArch);
				printf("Enviados %d comandos del archivo\n",iRet);
			}
			else if(strcmp(argFuncion,"ReadFpStatus")==0)
			{

				iRet=0;
				iRet = ReadFpStatus(&sts,&err,argComOrArch);
				if(iRet==0)
					printf("Error en la data recibida\n");
				else
					printf("Reporte de estado fiscal y error guardado en %s\n",argComOrArch);
			}	
			else 
			{
				printf("Funcion: no Valida\n");
				iRet=-1;
			}
			
			break;

		case 4:
			argFuncion= argv[1];
        		argComOrArch= argv[2];
			argRutArch= argv[3];

			if(strcmp(argFuncion,"UploadStatusCmd")==0)
			{
				iRet=0;
				iRet = UploadStatusCmd(argComOrArch,argRutArch);
				if(iRet==1)
					printf("Estatus guardado en %s:\n",argRutArch);
				else
					printf("Error al cargar status\n");
			}
			else if(strcmp(argFuncion,"UploadReportCmd")==0)
			{
				iRet=0;
				iRet = UploadReportCmd(argComOrArch,argRutArch);
				if(iRet==1)
					printf("Reporte guardado en %s:\n",argRutArch);
				else
					printf("Error al cargar reporte\n");
			}		
			else 
			{
				printf("Funcion: no Valida\n");
				iRet=-1;
			}
			break;

		default:
			printf("Revisar Argumentos\n");
			iRet=-1;
			break;
	} 

	CloseFpctrl();


   } 
   else
   {
	printf("Error de comunicación: por favor verificar puerto\n");
   }

   if((fileDesc=fopen("./Retorno.txt","w"))!=NUL)
   {
	fprintf(fileDesc,"Retorno: %d",iRet);
	fclose(fileDesc);
   }

   return iRet;
     
}
