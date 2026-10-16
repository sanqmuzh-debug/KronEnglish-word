import json,glob,re,sys,collections,os
sys.path.insert(0,'/home/claude/KronEnglish-word/scripts'); import syllabify
CMU=set(k.lower() for k in syllabify.cmu())
SHELF=set()
for f in glob.glob('/home/claude/KronEnglish-word/demo/books/*.json'):
  for u in json.load(open(f))['units']:
    for w in u['w']: SHELF.add(w['w'].lower())
VOC=set()
for l in open('word.csv',encoding='utf-8'):
  p=l.split('>')
  if len(p)>1: VOC.add(p[1].strip().lower())
CPS={}
for f in glob.glob('cpslists/*.json'):
  for u in json.load(open(f)):
    for w in u['words']: CPS[w['w'].lower().strip(' (')]=w
PHR={x for x in VOC|SHELF|set(CPS) if ' ' in x}
WORDS={x for x in CMU|VOC|SHELF|set(CPS) if ' ' not in x}
POS=re.compile(r"^(n|v|vt|vi|adj|adi|adji|ad|add|adv|prep|conj|pron|num|abbr|phr|int|interj|aux|pl|art)\.|^(adi|adji|vt|vi|number)$|^(n|v|adj|adv)\.\S")
DEF={'a','an','the','to','used','someone','somebody','something','etc','very','not','when','if','one','of','that','which','who','person','people','being','having','in','on','at','with','for','or','and','by','from','your','you','its','their'}
JUNK={'phrases','words','etc','expressions','vt.','n.','v.'}
def tok_ok(t):
  t=t.lower().strip(".,;:!?()'\"…")
  return not t or t in WORDS or t in ('sb','sth','sb.','sth.','...','…') or re.fullmatch(r"[\d.…/-]+|sb's|one's|[a-z]+'s|[a-z]+(-[a-z]+)+",t) and all(x in WORDS or len(x)<3 for x in t.split('-')) is not None
PUN='，。？！《》／/、：；“”‘’（）()⋯…·・•+=|「」【】?!,;:"'
def norm_tok(t): return re.sub(r'[^a-z0-9]','',t.lower())
def head_of(w,pub,stage,raw=''):
  w=re.sub(r'\s+',' ',w).strip(' ,;')
  toks=[t.strip(PUN) if not re.fullmatch(r'\.{2,}|…+',t) else t for t in w.split(' ')]
  toks=[t for t in toks if re.search('[A-Za-z]',t) or re.fullmatch(r'\.{2,}|…+',t)]
  pre=re.split('[/／]',raw)[0] if re.search('[/／]',raw) else ''
  pt=[norm_tok(t) for t in pre.split() if norm_tok(t)]
  if pt and len(pt)<len(toks) and [norm_tok(t) for t in toks[:len(pt)]]==pt: toks=toks[:len(pt)]
  for i,t in enumerate(toks):
    if i>=1 and POS.match(t.lower()): toks=toks[:i]; break
  # IPA residue: token with ' or : that is not a word
  for i,t in enumerate(toks):
    if i>=1 and re.search(r"[':ː/]",t) and not tok_ok(t) and not re.search(r"'s$",t): toks=toks[:i]; break
  return ' '.join(toks).strip(' ,;')
def resolve(h):
  """长条：取词典里最长的短语前缀"""
  toks=h.split(' ')
  low=h.lower()
  if low in PHR or low in WORDS: return h,'ok'
  for n in range(min(7,len(toks)),1,-1):
    p=' '.join(toks[:n]).lower()
    if p in PHR: return ' '.join(toks[:n]),'prefix'
  return h,None
PRI={x for x in set(CPS)|SHELF|VOC if ' ' not in x}
SEG={x for x in PRI if len(x)>=2 and x.isalpha()}|{'a','i'}
def segment(t):
  t0=t.lower()
  if not t0.isalpha() or len(t0)<5: return None
  best={0:[]}
  for i in range(1,len(t0)+1):
    for j in range(max(0,i-20),i):
      if j in best and t0[j:i] in SEG:
        c=best[j]+[t0[j:i]]
        if i not in best or len(c)<len(best[i]): best[i]=c
  r=best.get(len(t0))
  FW={'of','to','a','in','on','at','it','up','is','or','and','if','so','i','am','the','for','with','away','out','sb','one'}
  return r if r and 2<=len(r)<=4 and any(x in FW for x in r) and all(x in SHELF or x in FW for x in r) else None
SUBS=[('a','d'),('T','l'),('I','l'),('D','b'),('t','l'),('aa','dd'),('c','e'),('o','b'),('i','l')]
def fix_tok(t):
  core=t.strip(PUN)
  low=core.lower()
  if tok_ok(core): return t
  cands=set()
  if len(core)>3 and core[0] in 'DTICO口' and core[1:].lower() in PRI: cands.add(core[1:])
  for a,b in SUBS:
    for k in range(len(core)):
      if core[k:k+len(a)]==a:
        x=core[:k]+b+core[k+len(a):]
        if x.lower() in PRI: cands.add(x)
  # 多处 a->d
  x=core.replace('a','d')
  for y in {x, core.replace('aa','dd')}:
    if y.lower() in PRI: cands.add(y)
  import itertools
  idx=[k for k,ch in enumerate(core) if ch=='a']
  if len(idx)<=4:
    for r in range(1,len(idx)+1):
      for comb in itertools.combinations(idx,r):
        y=''.join('d' if k in comb else ch for k,ch in enumerate(core))
        if y.lower() in PRI: cands.add(y)
  cands={c.lower() for c in cands}
  if len(cands)==1:
    c=cands.pop()
    return c[0].upper()+c[1:] if core[0].isupper() and core[0].lower()==c[0] else c
  sg=segment(core)
  if sg: return ' '.join(sg)
  return t
from manual import FIX,KEEP,HJ_KEEP,HJ_FIX
FIXLOG=[]
out={};log=collections.Counter();review=[]
for f in sorted(glob.glob('../tl/lists/*.json')):
  d=json.load(open(f)); bid=f[-8:-5]
  for u in d['units']:
    nw=[]
    ex=[]
    for w in u['words']:
      parts=re.split(r'\s*\|?\s*口\s*(?=[A-Za-z])',w['raw'])
      if len(parts)>1:
        w=dict(w,zh=re.split('口',w['zh'])[0].strip())
        ex.append(w)
        for p in parts[1:]:
          hd=re.split('[/／]',p)[0].strip()
          zh=''.join(re.findall(r'[\u4e00-\u9fff，；（）、…]+',re.sub(r'^[^/]*/[^/]*/','',p) if p.count('/')>=2 else p))
          if re.search('[A-Za-z]',hd): ex.append({'w':hd,'zh':zh,'raw':p,'page':w.get('page')})
      else: ex.append(w)
    for w in ex:
      w=dict(w,w=re.sub(r'^(D|口|o|O|□)\s+(?=[a-z])','',w['w']))
      h=head_of(w['w'],d['pub'],d['stage'],w['raw'])
      if POS.match(h.split(' ')[0].lower()) or h.split(' ')[0].lower() in ('vt','vi','adji','adi'): log['posline']+=1; continue
      toks=h.split(' ')
      if not h or h.lower() in JUNK or not re.search('[A-Za-z]{2}',h) and h.lower() not in ('a','i'): log['junk']+=1; continue
      kk=next((v for k,v in KEEP.items() if h.startswith(k)),None)
      if kk: h=kk; toks=h.split(' ')
      elif toks[0].lower() in DEF and len(toks)>=4 and h.lower() not in PHR: log['defline']+=1; continue
      if len(toks)>=4:
        h2,how=resolve(h)
        if how: h=h2; log['long_'+how]+=1
        elif any(h.startswith(k) for k in KEEP): h=next(v for k,v in KEEP.items() if h.startswith(k)); log['keep']+=1
        elif len(toks)>=6: log['long_drop']+=1; review.append((bid,'DROP',h,w['raw'])); continue
      fixed=' '.join(fix_tok(t) for t in h.split(' '))
      if fixed!=h: log['fixed']+=1; FIXLOG.append((h,fixed)); h=fixed
      if h in FIX:
        if FIX[h] is None: log['mandrop']+=1; continue
        h=FIX[h]; log['manfix']+=1
      tt=h.split(' ')
      if len(tt)>=2 and re.search('[/／]',w['raw']):
        k=len(tt)
        while k>1 and not tok_ok(tt[k-1]): k-=1
        if k<len(tt) and all(tok_ok(x) for x in tt[:k]): h=' '.join(tt[:k]); log['ipacut']+=1
      if d['pub']=='沪教' and d['stage']=='高中' and not re.search('[/／]',w['raw']):
        if h in HJ_KEEP: h=HJ_FIX.get(h,h)
        elif ' ' not in h or h.lower() not in PHR: log['hj_cont']+=1; continue
      bad=[t for t in h.split(' ') if not tok_ok(t)]
      nw.append(dict(w,w=h,bad=bad) if bad else {k:v for k,v in dict(w,w=h).items() if k not in('bad',)})
      if bad: review.append((bid,'BAD',h,w['raw']))
    u['words']=nw
  out[bid]=d
os.makedirs('stage1',exist_ok=True)
for k,d in out.items(): json.dump(d,open(f'stage1/{k}.json','w'),ensure_ascii=False)
json.dump(review,open('review1.json','w'),ensure_ascii=False,indent=0)
json.dump(FIXLOG,open('fixlog.json','w'),ensure_ascii=False,indent=0)
print(log, len(review), collections.Counter(r[1] for r in review))
