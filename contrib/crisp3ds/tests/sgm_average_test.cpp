// SPDX-License-Identifier: MPL-2.0
// Synthetic numerical contract; no imagery, reconstruction, or device fallback.
#include <sycl/sycl.hpp>
#include <iostream>
int main(int argc, char**) {
    const bool metal = argc > 1;
    sycl::queue q = metal ? sycl::queue{sycl::gpu_selector_v} : sycl::queue{sycl::cpu_selector_v};
    if (metal && q.get_device().get_backend() != sycl::backend::metal) return 2;
    constexpr int n=1024;
    auto output=sycl::malloc_shared<unsigned char>(n,q);
    if (!output) return 3;
    q.parallel_for(sycl::range<1>(n),[=](sycl::id<1> id) {
        const int i=id[0], k=i/256;
        const float value=float(i%256);
        // Conversion must happen AFTER the float average; byte-first overflows.
        output[i]=static_cast<unsigned char>((value*float(k)+value)/float(k+1));
    }).wait_and_throw();
    int wrong=0;
    for(int i=0;i<n;i++) if(output[i] != i%256) ++wrong;
    std::cout << q.get_device().get_info<sycl::info::device::name>() << " cases=" << n << " wrong=" << wrong << '\n';
    sycl::free(output,q);
    return wrong ? 4 : 0;
}
