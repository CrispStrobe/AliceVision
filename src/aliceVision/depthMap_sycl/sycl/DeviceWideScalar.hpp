#pragma once
#include <limits>
#include <AdaptiveCpp/sycl/sycl.hpp>
namespace aliceVision { namespace depthMap_sycl {
#ifdef AV_SYCL_METAL_FLOAT
using DeviceWideScalar = float;
#else
using DeviceWideScalar = double;
#endif
using DeviceWideVec3 = acpp::sycl::vec<DeviceWideScalar, 3>;
}}
