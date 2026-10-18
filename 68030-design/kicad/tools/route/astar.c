#include <stdlib.h>
#include <string.h>
#include <math.h>
typedef struct {float f; int s;} H;
static H* heap; static int hn, hcap;
static void push(float f,int s){ if(hn>=hcap){hcap=hcap?hcap*2:1<<20; heap=realloc(heap,hcap*sizeof(H));}
 int i=hn++; while(i>0){int p=(i-1)/2; if(heap[p].f<=f)break; heap[i]=heap[p]; i=p;} heap[i].f=f; heap[i].s=s;}
static H pop(void){ H r=heap[0]; H x=heap[--hn]; int i=0; for(;;){int c=2*i+1; if(c>=hn)break; if(c+1<hn&&heap[c+1].f<heap[c].f)c++; if(heap[c].f>=x.f)break; heap[i]=heap[c]; i=c;} heap[i]=x; return r;}
static float* g; static int* prv; static int gcap;
/* returns path length (cells, as L*N+c), or -1. path written reversed from target to source */
int route(int nx,int ny,const float* cost,const float* vcost,const unsigned char* src,const unsigned char* tgt,
          float bend,const float* dm,int bx1,int by1,int bx2,int by2,float hw,int* path,int maxlen,long maxexp){
  int N=nx*ny; int S=2*N*4;
  if(gcap<S){ g=realloc(g,S*sizeof(float)); prv=realloc(prv,S*sizeof(int)); gcap=S;}
  for(int i=0;i<S;i++) g[i]=INFINITY;
  hn=0;
  int dx[4]={1,-1,0,0}, dy[4]={0,0,1,-1};
  for(int L=0;L<2;L++) for(int c=0;c<N;c++) if(src[L*N+c]){
    int x=c%nx,y=c/nx; int ddx = x<bx1?bx1-x:(x>bx2?x-bx2:0); int ddy= y<by1?by1-y:(y>by2?y-by2:0);
    for(int d=0;d<4;d++){int s=((L*N+c)<<2)|d; g[s]=0; prv[s]=-1; push(hw*(ddx+ddy),s);} }
  long exp=0; int goal=-1;
  while(hn>0){
    H h=pop(); int s=h.s; int d=s&3; int lc=s>>2; int L=lc/N; int c=lc%N; float gs=g[s];
    int x=c%nx,y=c/nx;
    { int ddx = x<bx1?bx1-x:(x>bx2?x-bx2:0); int ddy= y<by1?by1-y:(y>by2?y-by2:0); if(h.f>gs+hw*(ddx+ddy)+1e-4) continue; }
    if(tgt[lc]){goal=s;break;}
    if(++exp>maxexp) break;
    for(int k=0;k<4;k++){ int x2=x+dx[k], y2=y+dy[k]; if(x2<0||y2<0||x2>=nx||y2>=ny) continue;
      int c2=y2*nx+x2; float cc=cost[L*N+c2]; if(!(cc<1e29f)) continue;
      float ng=gs+cc*dm[L*2+(k>>1)]+(k!=d?bend:0); int s2=((L*N+c2)<<2)|k;
      if(ng<g[s2]){ g[s2]=ng; prv[s2]=s; int ddx = x2<bx1?bx1-x2:(x2>bx2?x2-bx2:0); int ddy= y2<by1?by1-y2:(y2>by2?y2-by2:0); push(ng+hw*(ddx+ddy),s2);} }
    { float vc=vcost[c]; if(vc<1e29f){ int L2=1-L; float cc=cost[L2*N+c]; if(cc<1e29f){ float ng=gs+vc; int s2=((L2*N+c)<<2)|d;
      if(ng<g[s2]){ g[s2]=ng; prv[s2]=s; int ddx = x<bx1?bx1-x:(x>bx2?x-bx2:0); int ddy= y<by1?by1-y:(y>by2?y-by2:0); push(ng+hw*(ddx+ddy),s2);} } } }
  }
  if(goal<0) return -1;
  int n=0; int s=goal; int last=-1;
  while(s>=0){ int lc=s>>2; if(lc!=last){ if(n>=maxlen) return -2; path[n++]=lc; last=lc;} s=prv[s]; }
  return n;
}
