import json,glob,re,collections,os
exec(open('clean.py').read().split('FIXLOG=[]')[0].replace('from manual import FIX,KEEP,HJ_KEEP,HJ_FIX',''))
SHZ={}
for f in glob.glob('/home/claude/KronEnglish-word/demo/books/*.json'):
  for u in json.load(open(f))['units']:
    for w in u['w']: SHZ.setdefault(w['w'].lower(),w.get('zh',''))
NAMEZH=re.compile(r'男名|女名|人名|姓|城市|国家|首都|省|州|岛|湖|河|山脉|山口|海滩|公园|博物馆|大学|学院|宫|教堂|广场|花园|街|区|镇|村|港|洲|[《》“”]|[•・·]|（.*(画家|作家|诗人|科学家|宇航员|总统|物理学家|天文学家|小说|歌曲|电影|书名|乐队|组织|公司|品牌).*）')
def clean_zh(z):
  z=re.sub(r'p\.\s*\d+|（\d+）|\(\d+\)|\d+','',z or '')
  z=re.sub(r'\s*\|\s*','',z)
  z=re.sub(r'[A-Za-z][A-Za-z .,&/]*$','',z)  # 尾巴上的英文残片
  z=re.sub(r'^[A-Za-z .,&/]+(?=[一-鿿（(])','',z)  # 开头的词性残片
  z=re.sub(r'\s+',' ',z).strip(' ；;，,、.')
  return z
def is_proper(h,zh):
  t=h.split()
  low=h.lower()
  if low in SHELF or low in CPS and CPS[low]['w'][0].islower(): return False
  rest=[x for x in t[1:] if x[0].isupper() and x not in ('I',"I'm","I'd","I'll")]
  if len(t)>1 and not rest and t[0].lower() in (SHELF|VOC) and not t[0].isupper(): return False
  if re.match(r"^(the )?[A-Z]",h) and NAMEZH.search(zh or ''): return True
  caps=[x for x in t if x[0].isupper() and x.lower() not in ('i',"i'm","i'd","i'll","i've")]
  if caps and all(x.lower() not in PRI or x[0].isupper() for x in caps) and low not in VOC and low not in SHELF: return True
  return False
from manual import KEEP_CAP,CAP_FIX,DROP_HEAD
props=collections.Counter(); keep=0; out={}
for f in sorted(glob.glob('stage1/*.json')):
  d=json.load(open(f)); seen=set(); units=[]
  for u in d['units']:
    ws=[]
    for w in u['words']:
      h=re.sub(r'\s+',' ',w['w']).strip()
      h=re.sub(r'\s*\.\.\.\s*|\s*…+\s*','... ',h).strip()
      zh=clean_zh(w.get('zh',''))
      h=re.sub(r'\s+[A-Z][a-z]?$','',h) if len(h.split())>=2 and h.split()[-1] not in ('I','A','B','C','D','TV','OK','DIY','UK','US','USA') and h.split()[-2][0].islower() else h
      h=re.sub(r'\b(Sb|So)\b','sb',h); h=re.sub(r'\bSth\b','sth',h)
      h=re.sub(r'(\.\.\. )([A-Z])([a-z]+)$',lambda m:m[1]+m[2].lower()+m[3],h)
      if h in DROP_HEAD: continue
      h=CAP_FIX.get(h,h)
      if h not in KEEP_CAP and is_proper(h,zh): props[(h,zh)]+=1; continue
      # 句首大写还原
      if h[0].isupper() and (h[0].lower()+h[1:]).lower() in (SHELF|VOC|set(CPS)|CMU) and not h.split()[0].isupper() and not h.startswith("I "):
        if h.lower() in SHELF or h.split()[0].lower() in PRI: h=h[0].lower()+h[1:]
      k=h.lower()
      if k in seen: continue
      seen.add(k)
      if not zh: zh=clean_zh(SHZ.get(k) or (CPS.get(k) or {}).get('zh','')) 
      ws.append({'w':h,'zh':zh,'page':w.get('page')})
    if ws: units.append({'unit':u['unit'],'words':ws})
  d['units']=units; out[f[-8:-5]]=d
os.makedirs('final',exist_ok=True)
for k,d in out.items(): json.dump(d,open(f'final/{k}.json','w'),ensure_ascii=False,indent=0)
with open('proper.txt','w') as fp:
  for (h,z),n in sorted(props.items()): fp.write(f'{h} | {z}\n')
n=sum(len(u['words']) for d in out.values() for u in d['units'])
print('entries',n,'proper',len(props),'nozh',sum(1 for d in out.values() for u in d['units'] for w in u['words'] if not w['zh']))
