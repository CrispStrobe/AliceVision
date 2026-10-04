# SPDX-License-Identifier: MPL-2.0
"""Compile the actual patched getters and header guard with tiny stub camera data."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess

p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--build',type=Path,required=True);a=p.parse_args()
h=(a.source/'src/aliceVision/mvsUtils/MultiViewParams.hpp').read_text();s=(a.source/'src/aliceVision/mvsUtils/MultiViewParams.cpp').read_text()
getters='\n'.join(re.findall(r'inline int get(?:Width|Height)\(int index\) const\s*\{[^}]*\}',h))
if len(re.findall(r'inline int get',getters))!=2:raise ValueError('Cannot extract actual getters')
start=s.index('        if (fileExists && (fileType == mvsUtils::EFileType::depthMap || fileType == mvsUtils::EFileType::normalMap))')
end=s.index('\n    }\n\n    ALICEVISION_LOG_INFO',start);block=s[start:end]
code='''#include <vector>
#include <cassert>
#include <string>
#include <stdexcept>
#include <algorithm>
namespace mvsUtils {enum class EFileType{depthMap,normalMap,other};}
namespace image {int w=125,h=83;void readImageSize(std::string,int&a,int&b){a=w;b=h;}}
struct Raster {struct Image{int width,height;};std::vector<Image> _imagesParams{{1749,1155}};
std::vector<int> _imagesScale{1},_mapRasterWidths{0},_mapRasterHeights{0};int _processDownscale=7;
int getDownscaleFactor(int i)const{return _imagesScale.at(i)*_processDownscale;}
'''+getters+'''};
void guard(){bool fileExists=true;auto fileType=mvsUtils::EFileType::depthMap;
struct{int width=1749,height=1155;std::string path="map";}imgParams;
int i=0,_maxImageWidth=0,_maxImageHeight=0;
std::vector<int>_imagesScale{14},_mapRasterWidths{0},_mapRasterHeights{0};
'''+block+'''
assert(_maxImageWidth==125&&_maxImageHeight==83);}
int main(){Raster a;assert(a.getWidth(0)==249&&a.getHeight(0)==165);
a._imagesScale[0]=14;a._processDownscale=1;a._mapRasterWidths[0]=125;a._mapRasterHeights[0]=83;
assert(a.getWidth(0)==125&&a.getHeight(0)==83&&a.getDownscaleFactor(0)==14);
assert(a._imagesParams[0].width==1749&&a._imagesParams[0].height==1155);
a._imagesParams[0]={1792,1152};a._imagesScale[0]=16;a._mapRasterWidths[0]=112;a._mapRasterHeights[0]=72;
assert(a.getWidth(0)==112&&a.getHeight(0)==72);guard();
for(int w:{0,123,126}){image::w=w;bool rejected=false;try{guard();}catch(const std::runtime_error&){rejected=true;}assert(rejected);}}
'''
a.build.mkdir(parents=True,exist_ok=True);cpp=a.build/'raster.cpp';exe=a.build/'raster';cpp.write_text(code)
subprocess.run([shutil.which('clang++')or'c++','-std=c++17',str(cpp),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True);print('actual map getters and extent guard passed')
