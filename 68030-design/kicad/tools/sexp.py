"""Minimal S-expression reader/writer for KiCad files."""
import re
class Sym(str):
    """bare atom (unquoted)"""
    pass
_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)
def parse(text):
    pos=0; stack=[[]]
    n=len(text)
    while pos<n:
        m=_tok.match(text,pos)
        if not m:
            if text[pos:].strip()=="" : break
            raise ValueError("parse error at %d: %r"%(pos,text[pos:pos+40]))
        pos=m.end()
        if m.group(1): stack.append([])
        elif m.group(2):
            l=stack.pop(); stack[-1].append(l)
        elif m.group(3) is not None:
            stack[-1].append(m.group(3).replace('\\"','"').replace('\\\\','\\'))
        elif m.group(4) is not None:
            stack[-1].append(Sym(m.group(4)))
    return stack[0][0] if len(stack[0])==1 else stack[0]
def q(s):
    s = str(s).replace("\\n", "\n")          # literal backslash-n in source -> newline
    s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return '"' + s + '"'
def dump(e, ind=0):
    if isinstance(e,list):
        if not e: return "()"
        simple = all(not isinstance(x,list) for x in e)
        if simple:
            return "("+" ".join(dump(x) for x in e)+")"
        parts=[]; head=[]
        i=0
        while i<len(e) and not isinstance(e[i],list):
            head.append(dump(e[i])); i+=1
        s="\t"*ind+"("+" ".join(head)
        for x in e[i:]:
            if isinstance(x,list):
                s+="\n"+("\t"*(ind+1)+dump(x,ind+1).lstrip("\t") if True else "")
            else:
                s+=" "+dump(x)
        s+="\n"+"\t"*ind+")"
        return s
    if isinstance(e,Sym): return str(e)
    if isinstance(e,bool): return "yes" if e else "no"
    if isinstance(e,(int,)): return str(e)
    if isinstance(e,float):
        r=("%.4f"%e).rstrip('0').rstrip('.')
        return "0" if r in ("-0","") else r
    return q(e)
def find(e, key):
    for x in e:
        if isinstance(x,list) and x and x[0]==key: return x
    return None
def findall(e, key):
    return [x for x in e if isinstance(x,list) and x and x[0]==key]
