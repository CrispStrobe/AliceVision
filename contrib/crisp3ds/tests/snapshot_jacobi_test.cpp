// SPDX-License-Identifier: MPL-2.0
#include <sycl/sycl.hpp>
#include <vector>
#include <iostream>
#include <cmath>
int main(int argc,char**argv){bool gpu=argc>1;sycl::queue q=gpu?sycl::queue{sycl::gpu_selector_v}:sycl::queue{sycl::cpu_selector_v};if(gpu&&q.get_device().get_backend()!=sycl::backend::metal)return 2;constexpr int w=37,h=29,n=w*h;auto out=sycl::malloc_shared<float>(n,q);auto snapshot=sycl::malloc_shared<float>(n,q);std::vector<float> expected(n),temp(n);float maxerror=0;int bad=0;
for(int repeat=0;repeat<3;repeat++){for(int i=0;i<n;i++)out[i]=expected[i]=float((i*37)%101)/16.f;
for(int iter=0;iter<20;iter++){for(int y=0;y<h;y++)for(int x=0;x<w;x++){int i=y*w+x;temp[i]=(expected[i]*4.f+expected[y*w+(x?x-1:x)]+expected[y*w+(x+1<w?x+1:x)]+expected[(y?y-1:y)*w+x]+expected[(y+1<h?y+1:y)*w+x])/8.f;}expected.swap(temp);
auto copied=q.copy(out,snapshot,n);q.submit([&](sycl::handler& hh){hh.depends_on(copied);hh.parallel_for(sycl::range<2>(w,h),[=](sycl::id<2> id){int x=id[0],y=id[1],i=y*w+x;out[i]=(snapshot[i]*4.f+snapshot[y*w+(x?x-1:x)]+snapshot[y*w+(x+1<w?x+1:x)]+snapshot[(y?y-1:y)*w+x]+snapshot[(y+1<h?y+1:y)*w+x])/8.f;});}).wait_and_throw();}
float e=0;for(int i=0;i<n;i++){float d=std::abs(out[i]-expected[i]);if(d!=0)bad++;e=std::max(e,d);}maxerror=std::max(maxerror,e);std::cout<<"repeat="<<repeat<<" maximum_error="<<e<<"\n";}
std::cout<<"device="<<q.get_device().get_info<sycl::info::device::name>()<<" bad="<<bad<<" maximum_error="<<maxerror<<"\n";sycl::free(out,q);sycl::free(snapshot,q);return bad?3:0;}
