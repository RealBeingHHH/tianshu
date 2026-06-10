#!/usr/bin/env python3
# SPDX-License-Identifier: CC-BY-NC-SA-4.0
# Copyright (c) 2026 天枢 Tianshu · 定倾 Dingqing（玄鉴 Xuanjian）
"""seal.py — 天枢 v3.5 封印引擎"""
import sys,os,json,time,hashlib,hmac
BASE=os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH=os.path.join(BASE,'.tianshu','sealed_manifest.json')
TRUST_ROOT=os.path.join(BASE,'.tianshu','trust_root.json')
DESTRUCT_LOG=os.path.join(BASE,'.tianshu','destruction.log')
FT={'.py':'CODE','.sh':'CODE','.yaml':'CONFIG','.yml':'CONFIG','.json':'CONFIG','.html':'CONFIG','.md':'CONFIG','.db':'DATA','.sqlite':'DATA','.log':'DATA','.txt':'DATA'}
PE=set(FT.keys()); ED={'.tianshu','.dna','.archive','.logs','__pycache__','build','.git','data'}
class SealEngine:
    def _lk(self):
        if os.path.exists(TRUST_ROOT):
            with open(TRUST_ROOT) as f: trust=json.load(f)
            fp=trust.get('fingerprint',hashlib.sha256(BASE.encode()).hexdigest())
            return hashlib.pbkdf2_hmac('sha256',fp.encode(),b'TIANSHU_SEAL_V1',100000,dklen=32)
        return hashlib.sha256(BASE.encode()).digest()
    def scan(self):
        files={}
        for root,dirs,fns in os.walk(BASE):
            dirs[:]=[d for d in dirs if not d.startswith('.') and d not in ED]
            for f in fns:
                ext=os.path.splitext(f)[1]
                if ext not in PE: continue
                fp=os.path.join(root,f); rel=os.path.relpath(fp,BASE)
                try:
                    with open(fp,'rb') as fh: c=fh.read()
                    files[rel]={'sha256':hashlib.sha256(c).hexdigest(),'size':len(c),'type':FT.get(ext,'DATA')}
                except: pass
        return files
    def seal(self,reason=''):
        print(f'🔐 封印...')
        files=self.scan(); sk=self._lk()
        m={'pv':'1.0','v':2,'sealed_at':time.time(),'fc':len(files),'files':files,'tc':{t:sum(1 for f in files.values() if f['type']==t) for t in ['CODE','CONFIG','DATA']}}
        mb=json.dumps(m,sort_keys=True,ensure_ascii=False).encode()
        sig=hmac.new(sk,mb,hashlib.sha256).hexdigest()
        sealed={'manifest':m,'signature':sig,'algo':'HMAC-SHA256'}
        os.makedirs(os.path.dirname(MANIFEST_PATH),exist_ok=True)
        if os.path.exists(MANIFEST_PATH): os.rename(MANIFEST_PATH,MANIFEST_PATH+f'.{int(time.time())}.bak')
        with open(MANIFEST_PATH,'w') as f: json.dump(sealed,f,indent=2,ensure_ascii=False)
        tc=m['tc']; print(f'  ✅ {len(files)}文件 CODE={tc.get("CODE",0)} CONFIG={tc.get("CONFIG",0)} DATA={tc.get("DATA",0)}')
        return {'fc':len(files)}
    def verify(self):
        if os.path.exists(DESTRUCT_LOG): return False,['自毁日志存在']
        if not os.path.exists(MANIFEST_PATH): return False,['封印缺失']
        try:
            with open(MANIFEST_PATH) as f: sealed=json.load(f)
        except: return False,['封印损坏']
        sk=self._lk(); mb=json.dumps(sealed['manifest'],sort_keys=True,ensure_ascii=False).encode()
        if not hmac.compare_digest(hmac.new(sk,mb,hashlib.sha256).hexdigest(),sealed.get('signature','')): return False,['HMAC不匹配']
        stored=sealed['manifest']['files']; current=self.scan(); diffs=[]
        for p in set(stored)-set(current): diffs.append(f'MISSING:{p}')
        for p in set(current)-set(stored): diffs.append(f'ADDED:{p}')
        for p in stored.keys()&current.keys():
            if stored[p]['sha256']!=current[p]['sha256']: diffs.append(f'MODIFIED:{p}')
        return len(diffs)==0,diffs
if __name__=='__main__':
    import argparse; p=argparse.ArgumentParser()
    p.add_argument('action',nargs='?',default='seal',choices=['seal','verify']); a=p.parse_args(); se=SealEngine()
    if a.action=='seal': se.seal(); ok,d=se.verify(); print('✅' if ok else f'❌{len(d)}处')
    elif a.action=='verify': ok,d=se.verify(); print('✅' if ok else f'❌{len(d)}处')
