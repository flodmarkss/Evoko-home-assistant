#define _GNU_SOURCE
#ifndef HA_IPV4
#error Build with HA_IPV4 set to your own Home Assistant IPv4 address
#endif
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <poll.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
static int all(int fd,const char *p,size_t n){while(n){ssize_t k=send(fd,p,n,MSG_NOSIGNAL);if(k<=0)return -1;p+=k;n-=k;}return 0;}
static void relay(int c){
 int s=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC,0);if(s<0)return;
 struct timeval t={20,0};setsockopt(s,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));setsockopt(c,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));
 struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(8123)};inet_pton(AF_INET,HA_IPV4,&a.sin_addr);
 if(connect(s,(void*)&a,sizeof(a))){close(s);return;}
 struct pollfd p[2]={{c,POLLIN,0},{s,POLLIN,0}};char b[16384];
 for(;;){int r=poll(p,2,300000);if(r<=0)break;
  for(int i=0;i<2;i++)if(p[i].fd>=0&&(p[i].revents&(POLLIN|POLLHUP|POLLERR))){int other=i?c:s;ssize_t n=recv(p[i].fd,b,sizeof(b),0);
   if(n>0){if(all(other,b,n))goto done;}else{shutdown(other,SHUT_WR);p[i].fd=-1;}
  }
  if(p[0].fd<0&&p[1].fd<0)break;
 }
 done:close(s);
}

static int listen_on(int port){
 int s=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC,0),one=1;if(s<0)return -1;setsockopt(s,SOL_SOCKET,SO_REUSEADDR,&one,sizeof(one));
 struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(port)};inet_pton(AF_INET,"127.0.0.1",&a.sin_addr);
 if(bind(s,(void*)&a,sizeof(a))||listen(s,32)){close(s);return -1;}return s;
}
static void deny(int c){
 struct timeval t={2,0};setsockopt(c,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));char h[4096];recv(c,h,sizeof(h),0);
 const char *r="HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n";all(c,r,strlen(r));
}
int main(void){
 signal(SIGCHLD,SIG_IGN);signal(SIGPIPE,SIG_IGN);int ha=listen_on(8123),block=listen_on(8124);if(ha<0||block<0){perror("loopback listeners");return 2;}
 puts("NASO_HA_PROXY listening on loopback; backend configured at build time");fflush(stdout);
 struct pollfd p[2]={{ha,POLLIN,0},{block,POLLIN,0}};
 for(;;){if(poll(p,2,-1)<=0)continue;for(int i=0;i<2;i++)if(p[i].revents&POLLIN){int c=accept4(p[i].fd,NULL,NULL,SOCK_CLOEXEC);if(c<0)continue;pid_t child=fork();if(child==0){close(ha);close(block);if(i==0)relay(c);else deny(c);close(c);_exit(0);}close(c);}}
}
