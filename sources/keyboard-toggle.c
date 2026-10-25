#include <X11/Xlib.h>
#include <X11/Xutil.h>
#include <X11/cursorfont.h>
#include <poll.h>
#include <stdio.h>
#include <unistd.h>
#include <signal.h>
#include <stdlib.h>
#include <string.h>
static int ignore_stale_window(Display*d,XErrorEvent*e){(void)d;(void)e;return 0;}
static Window find_window(Display*d,Window root,int keyboard){
 Window rr,parent,*children=NULL,found=None;unsigned n=0;long best=0;
 if(!XQueryTree(d,root,&rr,&parent,&children,&n))return None;
 for(unsigned i=0;i<n;i++){
  XWindowAttributes a;if(!XGetWindowAttributes(d,children[i],&a))continue;
  if(keyboard){char*name=NULL;if(XFetchName(d,children[i],&name)&&name){if(!strcmp(name,"Keyboard"))found=children[i];XFree(name);}}
  else if(a.map_state==IsViewable&&a.width>100&&a.height>50){
   XClassHint h={0};if(XGetClassHint(d,children[i],&h)){long area=(long)a.width*a.height;
    if(h.res_class&&h.res_name&&!strcmp(h.res_class,"firefox-esr")&&!strcmp(h.res_name,"Firefox")&&area>best){found=children[i];best=area;}
    if(h.res_name)XFree(h.res_name);if(h.res_class)XFree(h.res_class);
   }
  }
 }
 if(children)XFree(children);return found;
}
static Window wifi_window(Display*d,Window root){
 Window rr,parent,*children=NULL,found=None;unsigned n=0;
 if(!XQueryTree(d,root,&rr,&parent,&children,&n))return None;
 for(unsigned i=0;i<n;i++){XWindowAttributes a;XClassHint h={0};
  if(!XGetWindowAttributes(d,children[i],&a)||a.map_state!=IsViewable)continue;
  if(XGetClassHint(d,children[i],&h)){
   if((h.res_class&&strstr(h.res_class,"wpa_gui"))||(h.res_name&&strstr(h.res_name,"wpa_gui")))found=children[i];
   if(h.res_name)XFree(h.res_name);if(h.res_class)XFree(h.res_class);
  }
 }
 if(children)XFree(children);return found;
}
static void focus_wifi(Display*d,Window w){
 XClassHint h={0};XWindowAttributes a;
 if(XGetClassHint(d,w,&h)){
  if(((h.res_class&&strstr(h.res_class,"wpa_gui"))||(h.res_name&&strstr(h.res_name,"wpa_gui")))&&XGetWindowAttributes(d,w,&a)&&a.map_state==IsViewable)XSetInputFocus(d,w,RevertToParent,CurrentTime);
  if(h.res_name)XFree(h.res_name);if(h.res_class)XFree(h.res_class);
 }
}
static void fit_wifi_dialog(Display*d,Window w){
 char*name=NULL;XWindowAttributes a;
 if(XFetchName(d,w,&name)&&name){
  if((!strcmp(name,"NetworkConfig")||!strcmp(name,"ScanResults"))&&XGetWindowAttributes(d,w,&a)&&a.y!=0&&a.y+a.height>508)XMoveWindow(d,w,a.x<0?0:a.x,0);
  XFree(name);
 }
}
static void wifi_action(int close){
 if(fork()==0){execl("/usr/local/sbin/naso-wifi-open","naso-wifi-open",close?"--close":NULL,(char*)NULL);_exit(127);}
}
int main(void){
 signal(SIGCHLD,SIG_IGN);Display*d=XOpenDisplay(NULL);if(!d)return 3;XSetErrorHandler(ignore_stale_window);Window root=DefaultRootWindow(d),browser=None,keyboard=None;
 XSetScreenSaver(d,0,0,DontPreferBlanking,DontAllowExposures);XForceScreenSaver(d,ScreenSaverReset);
 XColor color,exact;unsigned long bg=BlackPixel(d,DefaultScreen(d));if(XAllocNamedColor(d,DefaultColormap(d,DefaultScreen(d)),"#006070",&color,&exact))bg=color.pixel;
 XSetWindowAttributes s={.override_redirect=True,.background_pixel=bg};Window w=XCreateWindow(d,root,940,708,72,48,0,CopyFromParent,InputOutput,CopyFromParent,CWOverrideRedirect|CWBackPixel,&s);
 XStoreName(d,w,"Naso Keyboard Toggle");XDefineCursor(d,w,XCreateFontCursor(d,XC_hand2));XSelectInput(d,w,ExposureMask|ButtonPressMask);XSelectInput(d,root,SubstructureNotifyMask);
 GC gc=XCreateGC(d,w,0,NULL);XSetForeground(d,gc,WhitePixel(d,DefaultScreen(d)));XFontStruct*f=XLoadQueryFont(d,"9x15bold");if(!f)f=XLoadQueryFont(d,"fixed");if(f)XSetFont(d,gc,f->fid);
 Window wifi=XCreateWindow(d,root,856,708,72,48,0,CopyFromParent,InputOutput,CopyFromParent,CWOverrideRedirect|CWBackPixel,&s);
 XStoreName(d,wifi,"Naso WiFi");XDefineCursor(d,wifi,XCreateFontCursor(d,XC_hand2));XSelectInput(d,wifi,ExposureMask|ButtonPressMask);
 XMapRaised(d,w);XFlush(d);
 for(;;){
  Window next=find_window(d,root,1);if(next!=keyboard){keyboard=next;if(keyboard){XMoveResizeWindow(d,keyboard,0,508,1024,260);XUnmapWindow(d,keyboard);}}
  browser=find_window(d,root,0);Window app=wifi_window(d,root);int redraw=0;
  XWindowAttributes ka;int shown=keyboard&&XGetWindowAttributes(d,keyboard,&ka)&&ka.map_state==IsViewable;
  if(shown||app)XMapWindow(d,wifi);else XUnmapWindow(d,wifi);
  while(XPending(d)){
   XEvent e;XNextEvent(d,&e);
   if(e.type==MapNotify)focus_wifi(d,e.xmap.window);
   if(e.type==DestroyNotify||e.type==UnmapNotify){Window current=wifi_window(d,root);if(current)focus_wifi(d,current);else if(browser)XSetInputFocus(d,browser,RevertToParent,CurrentTime);}
   if((e.type==MapNotify&&e.xmap.window!=w&&e.xmap.window!=wifi)||(e.type==ConfigureNotify&&e.xconfigure.window!=w&&e.xconfigure.window!=wifi&&e.xconfigure.window!=keyboard)){fit_wifi_dialog(d,e.type==MapNotify?e.xmap.window:e.xconfigure.window);if(shown&&keyboard)XRaiseWindow(d,keyboard);XRaiseWindow(d,w);if(shown||app)XRaiseWindow(d,wifi);}
   if(e.type==ButtonPress&&e.xbutton.window==wifi){wifi_action(app!=None);redraw=1;}
   if(e.type==ButtonPress&&e.xbutton.window==w&&keyboard&&browser){XWindowAttributes a;if(XGetWindowAttributes(d,keyboard,&a)){
    Window focus;int revert;XGetInputFocus(d,&focus,&revert);
    if(a.map_state==IsViewable)XUnmapWindow(d,keyboard);else XMapRaised(d,keyboard);XRaiseWindow(d,w);
    Window target=app?((focus!=None&&focus!=PointerRoot&&focus!=root)?focus:app):browser;
    XSetInputFocus(d,target,RevertToParent,CurrentTime);redraw=1;}}
   if(e.type==Expose&&(e.xexpose.window==w||e.xexpose.window==wifi))redraw=1;
  }
  if(redraw){XWindowAttributes a;int shown=keyboard&&XGetWindowAttributes(d,keyboard,&a)&&a.map_state==IsViewable;const char*t=shown?"Hide":"ABC";XClearWindow(d,w);XDrawString(d,w,gc,shown?18:22,30,t,strlen(t));}
  if(shown||app){XClearWindow(d,wifi);const char*t=app?"HA":"Wi-Fi";XDrawString(d,wifi,gc,app?26:14,30,t,strlen(t));}
  XFlush(d);struct pollfd p={ConnectionNumber(d),POLLIN,0};poll(&p,1,200);
 }
}
