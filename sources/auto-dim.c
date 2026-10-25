#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <signal.h>
#include <time.h>
#include <stdint.h>

/* Inside the chroot, /sys is read-only. The outer root's sysfs is writable. */
#define LIGHT "/proc/1/root/sys/class/backlight/backlight-lcd/"
#define SENSOR "/sys/bus/iio/devices/iio:device0/in_proximity_raw"
static volatile sig_atomic_t stop;
static void stopping(int sig){(void)sig;stop=1;}
static double mono(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static int number(const char*p){FILE*f=fopen(p,"r");int v=-1;if(f){if(fscanf(f,"%d",&v)!=1)v=-1;fclose(f);}return v;}
static int put(const char*p,int v){FILE*f=fopen(p,"w");if(!f)return -1;int r=fprintf(f,"%d\n",v);int c=fclose(f);return r>0&&c==0?0:-1;}
static int bounded(const char*s,int lo,int hi){char*end;long v=strtol(s,&end,10);if(*end||v<lo||v>hi)return -1;return (int)v;}
struct event32{int32_t sec,usec;uint16_t type,code;int32_t value;};
_Static_assert(sizeof(struct event32)==16,"ARM32 evdev size");
int main(int argc,char**argv){
 int idle=180,dim=20,bright=100,near=14,far=11;
 const char*config="/etc/naso-dim.conf";const char*state="/run/naso/dim-state.json";
 for(int i=1;i<argc;i++){
  if(!strcmp(argv[i],"--config")&&i+1<argc)config=argv[++i];
  else if(!strcmp(argv[i],"--state")&&i+1<argc)state=argv[++i];
  else if(!strcmp(argv[i],"--idle-seconds")&&i+1<argc){idle=bounded(argv[++i],3,86400);if(idle<0)return 2;}
  else{fprintf(stderr,"Usage: %s [--config FILE] [--state FILE] [--idle-seconds N]\n",argv[0]);return 2;}
 }
 FILE*f=fopen(config,"r");if(f){char key[64],value[64],line[200];while(fgets(line,sizeof line,f)){
  if(sscanf(line,"%63[^=]=%63s",key,value)!=2)continue;
  int v=bounded(value,1,86400);if(v<0)return 2;
  if(!strcmp(key,"idle_seconds"))idle=v;
  else if(!strcmp(key,"dim_percent"))dim=v;
  else if(!strcmp(key,"bright_percent"))bright=v;
  else if(!strcmp(key,"near_threshold"))near=v;
  else if(!strcmp(key,"far_threshold"))far=v;
 }fclose(f);}
 /* Command-line timeout deliberately overrides the file for a short hardware test. */
 for(int i=1;i+1<argc;i++)if(!strcmp(argv[i],"--idle-seconds"))idle=bounded(argv[i+1],3,86400);
 if(dim<1||dim>100||bright<dim||bright>100||near<=far||near>65535||far<0)return 2;
 int max=number(LIGHT"max_brightness");if(max<1)return 3;
 int full=(max*bright+99)/100,low=(max*dim+99)/100;if(low<1)low=1;
 int current=number(LIGHT"brightness");if(current<1)current=full;
 struct pollfd inputs[2]={{open("/dev/input/event0",O_RDONLY|O_NONBLOCK|O_CLOEXEC),POLLIN,0},{open("/dev/input/event1",O_RDONLY|O_NONBLOCK|O_CLOEXEC),POLLIN,0}};
 signal(SIGTERM,stopping);signal(SIGINT,stopping);
 double last=mono(),next_sample=0,next_state=0;int present=0,hits=0,misses=0,raw=-1,ok=0,old_target=-1;
 char tmp[512];if(snprintf(tmp,sizeof tmp,"%s.new",state)>=(int)sizeof tmp)return 2;
 put(LIGHT"bl_power",0);
 printf("DIM_START idle=%d dim_percent=%d near=%d far=%d\n",idle,dim,near,far);fflush(stdout);
 while(!stop){
  poll(inputs,2,100);double now=mono();
  for(int j=0;j<2;j++)if(inputs[j].fd>=0&&(inputs[j].revents&POLLIN)){
   struct event32 e[64];ssize_t n;
   while((n=read(inputs[j].fd,e,sizeof e))>0)for(size_t k=0;k<(size_t)n/sizeof e[0];k++)if(e[k].type==1||e[k].type==3)last=now;
  }
  if(now>=next_sample){
   raw=number(SENSOR);ok=raw>=0;next_sample=now+0.5;
   if(ok){
    if(!present){hits=raw>=near?hits+1:0;if(hits>=2){present=1;misses=0;}}
    else{misses=raw<=far?misses+1:0;if(misses>=2){present=0;hits=0;}}
   }
  }
  /* A failed sensor must not strand the user with a dim screen. */
  if(present||!ok)last=now;
  int target=now-last>=idle?low:full;
  if(target!=old_target){printf("DIM_TARGET %d raw=%d present=%d age=%.1f\n",target,raw,present,now-last);fflush(stdout);old_target=target;put(LIGHT"bl_power",0);}
  if(current!=target){int step=(max+9)/10;int value=current+(target>current?step:-step);if((target>current&&value>target)||(target<current&&value<target))value=target;
   if(put(LIGHT"brightness",value)==0)current=value;
  }
  if(now>=next_state){FILE*s=fopen(tmp,"w");if(s){fprintf(s,"{\"raw\":%d,\"sensor_ok\":%s,\"present\":%s,\"idle_seconds\":%d,\"inactive_seconds\":%.2f,\"brightness\":%d,\"target\":%d,\"maximum\":%d}\n",raw,ok?"true":"false",present?"true":"false",idle,now-last,current,target,max);fclose(s);rename(tmp,state);}next_state=now+1;}
 }
 put(LIGHT"brightness",full);put(LIGHT"bl_power",0);
 for(int j=0;j<2;j++)if(inputs[j].fd>=0)close(inputs[j].fd);
 return 0;
}
