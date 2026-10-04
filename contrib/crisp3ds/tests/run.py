# SPDX-License-Identifier: MPL-2.0
"""Portable synthetic regression runner; explicit devices, bounded subprocesses."""
import argparse
from pathlib import Path
import subprocess,os,time,signal,json,hashlib
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--acpp-prefix',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--devices',choices=['cpu','metal','cpu,metal'],default='cpu');a=p.parse_args();r=Path(__file__).absolute().parent;a.build.mkdir(parents=True,exist_ok=True);env=dict(os.environ,ACPP_VISIBILITY_MASK='metal;omp',OMP_NUM_THREADS='2',XDG_DATA_HOME=str((a.build/'cache').absolute()));env['DYLD_LIBRARY_PATH']=str((a.acpp_prefix/'lib').absolute())+(':'+env['DYLD_LIBRARY_PATH']if env.get('DYLD_LIBRARY_PATH')else'');rows=[]
def run(name,cmd):
 t=time.monotonic()
 with (a.build/(name+'.log')).open('wb')as f:
  proc=subprocess.Popen(cmd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  try:proc.wait(timeout=120)
  except subprocess.TimeoutExpired:
   os.killpg(proc.pid,signal.SIGKILL);proc.wait();raise
 rows.append({'name':name,'command':cmd,'seconds':time.monotonic()-t,'exit_code':proc.returncode});print(name,proc.returncode,flush=True)
 if proc.returncode:raise RuntimeError(name+' failed; see log')
files=[r/n for n in ['sgm_average_test.cpp','snapshot_jacobi_test.cpp','centered_ncc_test.cpp','raster_contract_test.py','source_contract_test.py','run.py']]+[a.source/'src/aliceVision/depthMap_sycl/sycl/SimStat.hpp',a.source/'src/aliceVision/mvsUtils/MultiViewParams.hpp',a.source/'src/aliceVision/mvsUtils/MultiViewParams.cpp'];sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest();before={str(x):sha(x)for x in files};(a.build/'frozen.json').write_text(json.dumps({'inputs_sha256':before,'devices':a.devices},indent=2)+'\n')
try:
 run('source-contract',['python3',str(r/'source_contract_test.py'),'--source',str(a.source)])
 for name in ['sgm_average','snapshot_jacobi','centered_ncc']:
  binary=(a.build/name).absolute();run(name+'-compile',[str((a.acpp_prefix/'bin/acpp').absolute()),'--acpp-targets=generic','-O2','-std=c++20','-I'+str((a.source/'src').absolute()),str(r/(name+'_test.cpp')),'-o',str(binary)])
  for device in a.devices.split(','):run(name+'-'+device,[str(binary)]+(['metal']if device=='metal'else[]))
 run('raster',['python3',str(r/'raster_contract_test.py'),'--source',str(a.source),'--build',str(a.build/'raster')]);status='passed'
except BaseException as e:status='failed';rows.append({'error':repr(e)})
unchanged=before=={str(x):sha(x)for x in files};(a.build/'result.json').write_text(json.dumps({'status':status,'stages':rows,'inputs_unchanged':unchanged,'no_imagery_or_reconstruction':True},indent=2)+'\n')
if status!='passed' or not unchanged:raise SystemExit(1)
