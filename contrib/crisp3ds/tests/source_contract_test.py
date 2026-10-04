# SPDX-License-Identifier: MPL-2.0
"""Fail closed if production callsites lose one of the tested fixes."""
import argparse
from pathlib import Path
import re
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);a=p.parse_args()
def read(rel):return (a.source/'src/aliceVision/depthMap_sycl'/rel).read_text()
def require(condition,message):
 if not condition:raise RuntimeError(message)
sgm=read('sycl/planeSweeping/deviceSimilarityVolume.cpp');compact=re.sub(r'\s+','',sgm)
require('volume_xyz=TSim((float(volume_xyz)*float(filteringIndex)+pathCost)/float(filteringIndex+1));'in compact,'SGM conversion no longer follows float averaging')
patch=read('sycl/Patch.hpp');calls=re.findall(r'sst\.update\((.*?)\);',patch,re.S);centered='rcPatchCoordColor.x()-rcCenterColor.x(),tcPatchCoordColor.x()-tcCenterColor.x(),w'
require(sum(re.sub(r'\s+','',call)==centered for call in calls)==3,'All three weighted NCC callsites must center both luminance samples')
opt=read('sycl/planeSweeping/deviceDepthSimilarityMap.cpp');require('getCellSmoothStepEnergy(camParams, depthSnapshot_acc, rCoords, roiBegin)'in opt,'Optimizer neighbor stencil must read snapshot')
require('getCellSmoothStepEnergy(camParams, out_optimizeDepthSimMap_acc'not in opt,'Optimizer still reads concurrently written output neighbors')
require(re.search(r'for\(int iter.*?\{.*?prerequisite = inout_depthSnapshot_dmp\.copyFrom\(out_optimizeDepthSimMap_dmp, queue, prerequisite\);\s*//[^\n]*\n\s*prerequisite = queue\.submit\(.*?h\.depends_on\(prerequisite\)',opt,re.S)is not None,'Every optimizer iteration must copy previous output, then depend on that copy')
require('const SyclDevicePitchedAccess depthSnapshot_acc{inout_depthSnapshot_dmp}'in opt,'Snapshot read accessor missing')
refine=read('Refine.hpp');require('_optDepthSnapshot_dmp'in refine,'Scratch snapshot must have persistent Refine lifetime')
print('production SGM, 3 NCC callsites, ordered immutable snapshot contracts passed')
