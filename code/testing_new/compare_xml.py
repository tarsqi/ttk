from docmodel.xml_parser import *
"""
"""
# Updated 11/08/08   -kt


def comp(expected,observed):
    """
    Calls the 
    """
    exp_elem=Parser().parse_string(expected).elements
    obs_elem=Parser().parse_string(observed).elements
    exp=[]
    obs=[]
    for i in exp_elem:
        exp.append(i.content)
    for i in obs_elem:
        obs.append(i.content)
    eerr=[]
    oerr=[]

# This may need to be swapped out:        
    ec=oc=0
    while ec<len(exp) and oc<len(obs):
        try:
            if exp[ec]==obs[oc]:
                ec+=1
                oc+=1
                continue
            elif exp[ec+1]==obs[oc]:
                eerr.append(ec)
                ec+=1
                continue
            elif exp[ec]==obs[oc+1]:
                oerr.append(oc)
                oc+=1
                continue
            else:
                eerr.append(ec)
                oerr.append(oc)
                ec+=1
                oc+=1
                continue
        except IndexError:
            break
    if ec < len(exp):
        for i in range(ec,len(exp)):
            eerr.append(i)
    if oc < len(obs):
        for i in range(oc,len(obs)):
            oerr.append(i)
# /Through here
            
    return (exp_elem,eerr,obs_elem,oerr)

    
    

