#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <errno.h>
#include <arpa/inet.h>
 
int main(int argc, char** argv)
{
  int sockfd = 0,n = 0;
  char recvBuff[1024];
  struct sockaddr_in serv_addr;

  if(argc==1)
	return 0;

  char* msg = argv[1];
 
  memset(recvBuff, '0' ,sizeof(recvBuff));
  if((sockfd = socket(AF_INET, SOCK_STREAM, 0))< 0)
    {
      printf("\n Error : Could not create socket \n");
      return 1;
    }
 
  serv_addr.sin_family = AF_INET;
  serv_addr.sin_port = htons(5000);
  struct hostent *hen;
  if((hen = gethostbyname("server.jerry.cs164")) == NULL) {
	perror("aaa");
  }
  //serv_addr.sin_addr.s_addr = inet_addr("127.0.0.1");
  bcopy((char *)hen->h_addr,(char *)&serv_addr.sin_addr.s_addr,hen->h_length);
  
  //printf("%s\n", hen->h_addr);
  if(connect(sockfd, (struct sockaddr *)&serv_addr, sizeof(serv_addr))<0)
    {
      printf("\n Error : Connect Failed \n");
      return 1;
    }
 
      n = read(sockfd, recvBuff, sizeof(recvBuff)-1);
      recvBuff[n] = 0;
      if(fputs(recvBuff, stdout) == EOF)
    {
      printf("\n Error : Fputs error");
    }
      printf("\n");
  
  send(sockfd, msg, strlen(msg), 0);
  if( n < 0)
    {
      printf("\n Read Error \n");
    }
 
 
  return 0;
}
