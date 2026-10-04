// SPDX-License-Identifier: MPL-2.0
// Tests the actual AliceVision weighted-statistics implementation against host FP64.
#include <sycl/sycl.hpp>
#include <aliceVision/depthMap_sycl/sycl/SimStat.hpp>
#include <cmath>
#include <iostream>
#include <vector>
int main(int argc,char**) {
    bool metal=argc>1;
    sycl::queue q=metal?sycl::queue{sycl::gpu_selector_v}:sycl::queue{sycl::cpu_selector_v};
    if(metal&&q.get_device().get_backend()!=sycl::backend::metal)return 2;
    constexpr int cases=32,pixels=81;
    auto x=sycl::malloc_shared<float>(cases*pixels,q);
    auto y=sycl::malloc_shared<float>(cases*pixels,q);
    auto w=sycl::malloc_shared<float>(cases*pixels,q);
    auto result=sycl::malloc_shared<float>(cases,q);
    if(!x||!y||!w||!result)return 3;
    std::vector<double> expected(cases);
    for(int c=0;c<cases;c++) {
        for(int i=0;i<pixels;i++) {
            int j=c*pixels+i;
            x[j]=80.f+float(((i*17+c*11)%41)-20)*(.01f+float(c%4)*.02f);
            y[j]=95.f+float(((i*17+c*11)%41)-20)*(.009f+float(c%4)*.018f)+float((i*7)%9-4)*.001f;
            w[j]=float(1+(i*13+c)%17)/17.f;
        }
        double sum=0,mx=0,my=0,vx=0,vy=0,cov=0;
        for(int i=0;i<pixels;i++){int j=c*pixels+i;sum+=w[j];mx+=double(w[j])*x[j];my+=double(w[j])*y[j];}
        mx/=sum;my/=sum;
        for(int i=0;i<pixels;i++){int j=c*pixels+i;double a=x[j]-mx,b=y[j]-my;vx+=w[j]*a*a;vy+=w[j]*b*b;cov+=w[j]*a*b;}
        expected[c]=-cov/std::sqrt(vx*vy);
    }
    q.parallel_for(sycl::range<1>(cases),[=](sycl::id<1> id){
        int c=id[0],base=c*pixels;
        aliceVision::depthMap_sycl::simStat statistics;
        float centerX=x[base+40],centerY=y[base+40];
        for(int i=0;i<pixels;i++) statistics.update(x[base+i]-centerX,y[base+i]-centerY,w[base+i]);
        result[c]=statistics.computeWSim();
    }).wait_and_throw();
    int wrong=0;double maximum=0;
    for(int c=0;c<cases;c++){double e=std::abs(result[c]-expected[c]);maximum=std::max(maximum,e);if(!std::isfinite(result[c])||std::abs(result[c])>1.00001||e>.001)++wrong;}
    std::cout<<q.get_device().get_info<sycl::info::device::name>()<<" cases="<<cases<<" maximum_FP64_error="<<maximum<<" wrong="<<wrong<<'\n';
    sycl::free(x,q);sycl::free(y,q);sycl::free(w,q);sycl::free(result,q);
    return wrong?4:0;
}
