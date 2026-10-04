# Experimental macOS SYCL reconstruction branch

This branch starts at AliceVision `5d73fa0d23636d3d126f670ab21f8936e1dd7eda`.
Separate commits preserve build compatibility fixes, an opt-in Metal float
profile, and four numerical/raster corrections. The default device scalar
remains double. `AV_SYCL_METAL_FLOAT=1` selects float device geometry and
requires a Metal GPU; it does not silently use the CPU.

The four corrections divide SGM costs before byte conversion, center weighted
NCC samples before second-moment accumulation, snapshot neighbor depths for
each parallel optimization iteration, and retain the actual saved depth-map
raster dimensions for odd image sizes. The snapshot semantics match the
pinned CUDA implementation. Raster dimensions do not change original image
dimensions, intrinsic calibration or projection metadata.

## Build

The verified environment was Apple M1, macOS 26, Xcode 26.2 and Homebrew LLVM
20.1.8. The Metal runtime used AdaptiveCpp
`a215fbcd89087d638769c0a0449bc2abb9350f8e` and Apple metal-cpp
`27c4382b7151d55a51692cdcb27aaa98752240de`. Metal support remains experimental.
The CPU runtime was AdaptiveCpp v25.10.0 with the separate Darwin host linker
backport in `CrispStrobe/AdaptiveCpp`, branch `crisp3ds/darwin-host-jit`.

Install the usual AliceVision dependencies first. `DEPENDENCIES` below is a
prefix containing the other AliceVision dependencies; supply the independently
installed Eigen and Ceres prefixes explicitly. This helper reproduces the
recorded configuration flags, without machine-specific source/install paths.
It does not download dependencies or install Homebrew packages.

```sh
python3 contrib/crisp3ds/configure_m1.py \
  --build "$PWD/build-m1" --install "$PWD/install-m1" \
  --adaptivecpp "$ADAPTIVECPP" --dependencies "$DEPENDENCIES" \
  --eigen "$EIGEN" --ceres "$CERES" --metal
cmake --build build-m1 --parallel 2 --target \
  aliceVision_depthMapEstimation_exe aliceVision_depthMapFiltering_exe
```

Omit `--metal` and use the CPU AdaptiveCpp prefix for the default-double
profile. Set `--homebrew`, `--llvm` or `--sdk` to override detected/toolchain
locations. Use `--print-only` to review the command. Build in a fresh directory;
the snapshot and raster patches change class layouts and require rebuilding
all dependent objects. Never swap one patched shared library into an older
installation.

The local controlled installations were staged with their transitive libraries
and resources. This fork packages source, not those installations. Follow the
normal AliceVision installation/resource layout and ensure the AdaptiveCpp
Metal runtime and dependency dylibs are available to the executables. Use the
CPU `prepareDenseScene` tool for undistortion and EXR preparation. Native depth
estimation uses `--backend 1 --nbGPUs 1`; verify `Using device Apple M1` in the
log. Default-double CPU execution is a separate path.

## Verification and limits

Portable synthetic contract tests are in `tests/`. With the pinned newer
AdaptiveCpp headers/runtime and the required CPU/Metal backends, run them from
the repository root:

```sh
python3 contrib/crisp3ds/tests/run.py --source "$PWD" \
  --acpp-prefix "$ADAPTIVECPP" --build "$PWD/regression-build" \
  --devices cpu,metal
```

Use `--devices cpu` to skip GPU execution. These test assets require the newer
headers that define the Metal backend; they are separate from the older
v25.10.0 CPU build profile. The tests compile the actual
weighted-statistics implementation, verify arithmetic and repeated Jacobi
contracts, compile the actual raster getters/extent validation with stub data,
and check that the production callsites retain the fixes. Synthetic NCC inputs
are independent of the earlier 16 sampled-patch diagnostic. They contain no
private images or binary fixtures and do not measure reconstruction accuracy.

The committed production code matches the tested isolated source profiles.
Three isolated diagnostic files used alternate include spellings; this branch
keeps repository-relative includes to the same headers. Build/test evidence is
recorded in [crisp3ds](https://github.com/CrispStrobe/crisp3ds), under
`tests/evidence/alicevision-native-{sgm-average,centered-ncc,snapshot-optimization,map-raster-fix,dragon-snapshot-control}.json`.
Some supporting artifacts are local and those files are not all published yet.

A fresh complete build from this fork also passed on the M1 GPU: all 155
C++ units and the engine dependency graph were rebuilt, and both tools used
one coherent installation. All twelve depth/confidence arrays matched the
earlier corrected runs exactly. Its source base and the AdaptiveCpp/metal-cpp
commits above were checked against current upstream heads on 2026-10-04.
See `tests/evidence/alicevision-native-current-fork-control.json` in crisp3ds.

The repeated CPU/Metal Jacobi regression matched the serial float32 reference
exactly. CPU/Metal depth agreement improved, but Metal's synthetic median
relative radial error remained 4.51%; corrected CPU float was 4.33%.
A three-view dragon probe completed native GPU depth estimation and filtering
in 2.02 and 0.35 seconds. It retained about 90% of sampled foreground pixels
and 58% of background pixels. These are execution/coverage observations, not
a full-model benchmark or ground-truth reconstruction accuracy. Object masks
must exclude background before object-only fusion. No improved final dragon
STL is claimed by these patches.
