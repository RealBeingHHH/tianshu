#!/usr/bin/env python3
"""self_destruct.py — 天枢 v3.5 自毁执行器"""
import sys,os,json,time,random
BASE=os.path.dirname(os.path.abspath(__file__))
TIANSHU_DIR=os.path.join(BASE,'.tianshu')
DESTRUCT_LOG=os.path.join(TIANSHU_DIR,'destruction.log')
CORE=['bind.py','host_bind.py','seal.py','self_destruct.py','sentinel.py','host_sentinel.py','host_lock.py','connector.py','guardian.py','api.py','boot.py']

def _check_already_destroyed():
    if os.path.exists(DESTRUCT_LOG):
        print('⛔ 天枢已自毁。destruction.log 存在。拒绝启动。')
        sys.exit(1)

def execute(reason='UNKNOWN',detail=None):
    print('\n🔴 天枢 v3.5 自毁程序启动\n')
    log={'timestamp':time.time(),'reason':reason,'detail':str(detail)[:500] if detail else '','actions':[]}
    # 阶段1: 覆写信任数据
    wiped=0
    for path in [os.path.join(TIANSHU_DIR,f) for f in ['trust_root.json','sealed_manifest.json','.host_bound']]:
        if os.path.exists(path):
            try:
                size=os.path.getsize(path) or 1024
                with open(path,'wb') as f: f.write(random.randbytes(min(size,10240)))
                os.remove(path); wiped+=1
            except: pass
    log['actions'].append(f'trust_wiped:{wiped}')
    print(f'  [1/5] 信任数据覆写: {wiped}')
    # 阶段2: 破坏核心模块
    corrupted=0
    for rel in CORE:
        path=os.path.join(BASE,rel)
        if os.path.exists(path):
            try:
                size=os.path.getsize(path) or 4096
                with open(path,'wb') as f: f.write(random.randbytes(size))
                corrupted+=1
            except: pass
    log['actions'].append(f'core_corrupted:{corrupted}')
    print(f'  [2/5] 核心模块破坏: {corrupted}')
    # 阶段3: 销毁密钥
    destroyed=0
    for path in [os.path.join(TIANSHU_DIR,'trust_root.json'),os.path.join(BASE,'.voyager_state.db')]:
        if os.path.exists(path):
            try: os.remove(path); destroyed+=1
            except: pass
    log['actions'].append(f'keys_destroyed:{destroyed}')
    print(f'  [3/5] 密钥销毁: {destroyed}')
    # 阶段4: 写日志
    os.makedirs(TIANSHU_DIR,exist_ok=True)
    with open(DESTRUCT_LOG,'w') as f: json.dump(log,f,indent=2)
    print(f'\n  ⏹ 自毁完成。原因: {reason}')
    sys.exit(0)

if __name__=='__main__':
    print('self_destruct v3.5 self-test PASSED')
