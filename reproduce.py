"""Offline verification from saved outcomes and requests; no model or simulator calls."""
from pathlib import Path
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import permutations
from math import comb, isclose
import argparse
import hashlib
import importlib.util
import json
import random
import zipfile
import sys
import numpy as np
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parent
MODELS={'gpt54mini':'GPT54_main','gpt41mini':'GPT41_main','gemini36flash':'Gemini_main','qwen35_9b':'Qwen_recovery'}
def read(name): return json.loads((ROOT/'data'/name).read_text(encoding='utf-8'))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def close(a,b): assert isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-8),(a,b)
def signflip(values):
    sums=np.array([0],dtype=np.int64)
    for v in values:sums=np.concatenate((sums+v,sums-v))
    return np.count_nonzero(abs(sums)>=abs(sum(values)))/len(sums)
def holm(values):
    order=sorted(range(len(values)),key=lambda i:values[i]); out=[0.]*len(values); prev=0.
    for rank,i in enumerate(order): prev=max(prev,min(1.,(len(values)-rank)*values[i]));out[i]=prev
    return out
def draws(seed):
    rng=random.Random(seed)
    return np.array([[rng.randrange(16) for _ in range(16)] for _ in range(50000)],dtype=np.int8)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--correlations',action='store_true');args=parser.parse_args()
    outcomes=read('outcomes.json'); pairs=read('paired_review.json'); resources=read('resources.json');gate=read('static_gate.json')
    assert len(outcomes)==7600 and len({(r['dataset'],r['condition'],r['case']) for r in outcomes})==7600
    by={(r['dataset'],r['condition'],r['case']):r for r in outcomes}
    contract=read('contract_reference.json')
    contract_tasks=sorted({r['task'] for r in outcomes if r['dataset']=='GPT54_C0'})
    delta=[sum(r['success'] for r in outcomes if r['dataset']=='GPT54_main' and r['condition']=='c1_direct' and r['task']==t)-sum(r['success'] for r in outcomes if r['dataset']=='GPT54_C0' and r['task']==t) for t in contract_tasks]
    close(signflip(delta),contract['exact_task_cluster_signflip_p'])
    a_only=sum(r['success'] and not by['GPT54_main','c1_direct',r['case']]['success'] for r in outcomes if r['dataset']=='GPT54_C0')
    b_only=sum(not r['success'] and by['GPT54_main','c1_direct',r['case']]['success'] for r in outcomes if r['dataset']=='GPT54_C0')
    mcnemar=min(1.,2*sum(Fraction(comb(a_only+b_only,i),2**(a_only+b_only)) for i in range(min(a_only,b_only)+1)))
    close(mcnemar,contract['exact_mcnemar_p'])
    counts=defaultdict(lambda:[0,0])
    for r in outcomes:
        counts[r['dataset'],r['condition']][0]+=1;counts[r['dataset'],r['condition']][1]+=r['success']
        assert r['success']==int(r['official_all_states_pass'] and not r['specification_failure'])
    for r in pairs:
        a=by[r['dataset'],r['base'],r['case']];b=by[r['dataset'],r['reviewed'],r['case']]
        assert a['success']==r['initial_success'] and b['success']==r['final_success']
    for s in read('review_summary.json'):
        rows=[r for r in pairs if (r['dataset'],r['pair'])==(s['dataset'],s['pair'])]
        assert len(rows)==400
        assert sum(r['transition']=='FS' for r in rows)==s['repairs'] and sum(r['transition']=='SF' for r in rows)==s['regressions']
    fallback=read('fallback_reference.json')['summary']
    for s in fallback:
        rows=[r for r in pairs if (r['dataset'],r['pair'])==(s['dataset'],s['pair'])]
        actual=sum(r['initial_success'] if r['terminal_review_failure'] else r['final_success'] for r in rows)
        assert actual==s['initial_fallback_successes']
    for s in read('resource_summary.json'):
        rows=[r for r in resources if (r['dataset'],r['condition'])==(s['dataset'],s['condition'])]
        for key in ['input_tokens','cached_input_tokens','output_tokens','reasoning_tokens','total_tokens','api_calls','logical_calls','recorded_seconds']:
            close(sum(r[key] for r in rows),s[key])
        if s['dataset']!='Qwen_recovery':
            ri,rc,ro={'GPT54_main':(.75,.075,4.50),'GPT41_main':(.40,.10,1.60),'Gemini_main':(.75,.075,3.75)}[s['dataset']]
            cost=((s['input_tokens']-s['cached_input_tokens'])*ri+s['cached_input_tokens']*rc+s['output_tokens']*ro)/1e6
            close(cost,s['standard_equivalent_cost_usd'])
    for r in gate:
        assert r['gated_success']==(r['always_success'] if r['routed_to_reviewer'] else r['base_success'])
        assert r['routed_to_reviewer']==bool(r['review_eligible'] and not r['initial_static_valid'])
        source=r['always_resources'] if r['routed_to_reviewer'] else r['base_resources']
        for key in ['input_tokens','output_tokens','total_tokens']:close(r['resources'][key],source[key])
    for s in read('gate_summary.json'):
        rows=[r for r in gate if (r['dataset'],r['pair'])==(s['dataset'],s['pair'])]
        for key,target in [('routed_to_reviewer','routed'),('base_success','base_successes'),('always_success','always_successes'),('gated_success','gated_successes')]:
            assert sum(r[key] for r in rows)==s[target]
    statistics=read('main_statistics.json')['tests']; plan=read('main_statistics_plan.json')
    samples=[draws(seed) for seed in plan['confidence_intervals']['seed_by_contrast']]
    rawps=[]
    tasks=sorted({r['task'] for r in outcomes if r['dataset']=='GPT54_main'})
    for i,s in enumerate(statistics):
        dataset=MODELS[s['model_key']];ca=next(r['condition'] for r in outcomes if r['condition'].startswith(s['a'].lower()));cb=next(r['condition'] for r in outcomes if r['condition'].startswith(s['b'].lower()))
        delta=[sum(r['success'] for r in outcomes if r['dataset']==dataset and r['condition']==cb and r['task']==t)-sum(r['success'] for r in outcomes if r['dataset']==dataset and r['condition']==ca and r['task']==t) for t in tasks]
        assert delta==s['task_differences_success_counts'];p=signflip(delta);close(p,s['cluster_signflip_p']);rawps.append(p)
        lo,hi=np.percentile(np.asarray(delta)[samples[i%4]].sum(axis=1)/4,[2.5,97.5],method='linear')
        close(lo,s['task_bootstrap_95_low_pp']);close(hi,s['task_bootstrap_95_high_pp'])
    for i,p in enumerate(holm(rawps)):close(p,statistics[i]['holm_p_all_16'])
    for k in range(0,16,4):
        for i,p in enumerate(holm(rawps[k:k+4])):close(p,statistics[k+i]['holm_p_within_model_4'])
    gate_stats=read('gate_statistics.json');gate_draws={s['bootstrap_seed']:draws(s['bootstrap_seed']) for s in gate_stats}
    for s in gate_stats:
        rows=[r for r in gate if (r['dataset'],r['pair'])==(s['dataset'],s['pair'])]
        source='base_success' if s['reference']=='base' else 'always_success'
        delta=[sum(int(r['gated_success'])-int(r[source]) for r in rows if r['task']==t) for t in tasks]
        assert delta==s['task_differences'];close(signflip(delta),s['cluster_signflip_p'])
        lo,hi=np.percentile(np.asarray(delta)[gate_draws[s['bootstrap_seed']]].sum(axis=1)/4,[2.5,97.5],method='linear')
        close(lo,s['bootstrap_95_low_pp']);close(hi,s['bootstrap_95_high_pp'])
    for i,p in enumerate(holm([s['cluster_signflip_p'] for s in gate_stats])):close(p,gate_stats[i]['holm_p_all16'])
    for dataset in sorted({s['dataset'] for s in gate_stats}):
        family=[s for s in gate_stats if s['dataset']==dataset]
        for s,p in zip(family,holm([s['cluster_signflip_p'] for s in family])):close(p,s['holm_p_within_model4'])
    inventory=read('candidate_inventory.json');pools=defaultdict(list)
    for r in inventory:pools[r['instruction']].append(r)
    assert len(pools)==80 and all(len(p)==5 for p in pools.values())
    detail=[];curves=[]
    for cap in range(1,6):
        ss=[];tt=[];gg=[];oo=[]
        for name,pool in sorted(pools.items()):
            chosen=[];cost=[];consumed=[]
            for order in permutations(sorted(pool,key=lambda r:r['repetition'])):
                prefix=[]
                for candidate in order[:cap]:
                    prefix.append(candidate)
                    if candidate['static_valid']:break
                chosen.append(prefix[-1]['success']);cost.append(sum(r['total_tokens'] for r in prefix));consumed.append(len(prefix))
            s=sum(chosen)/120;t=sum(cost)/120;ss.append(s);tt.append(t);gg.append(sum(consumed)/120)
            successes=sum(r['success'] for r in pool)
            oo.append(1-(comb(5-successes,cap) if 5-successes>=cap else 0)/comb(5,cap))
            if cap==5:detail.append({'instruction':name,'task':pool[0]['task'],'success':s})
        cur={'cap':cap,'success_pct':100*np.mean(ss),'mean_tokens':np.mean(tt),'mean_generations':np.mean(gg),'oracle_pass_at_k_pct':100*np.mean(oo)}
        for key,value in cur.items():close(value,read('sequential_summary.json')['curve'][cap-1][key])
        curves.append(cur)
    seq=read('sequential_summary.json');draw=np.random.default_rng(20261015).integers(0,16,size=(50000,16))
    qgate={r['case']:r for r in gate if r['dataset']=='Qwen_recovery' and r['base']=='c1_direct'}
    for key in ['c3','gated']:
        deltas=[]
        for task in tasks:
            vals=[]
            for d in detail:
                if d['task']!=task:continue
                pool=pools[d['instruction']]
                reference=sum(r['c3_success'] if key=='c3' else qgate[r['case']]['gated_success'] for r in pool)/5
                vals.append(reference-d['success'])
            deltas.append(100*np.mean(vals))
        expected=seq['contrasts'][key+'_minus_sequential_cap5'];close(np.mean(deltas),expected['difference_pp'])
        lo,hi=np.percentile(np.asarray(deltas)[draw].mean(axis=1),[2.5,97.5],method='linear')
        close(lo,expected['ci95_pp'][0]);close(hi,expected['ci95_pp'][1])
    raw_index=json.loads((ROOT/'provenance/case_records.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(ROOT/'saved_records.zip') as z:
        assert len(raw_index)==7600 and z.testzip() is None
        for row in raw_index:
            raw=z.read(row['member']);assert sha(raw)==row['sha256']
            v=json.loads(raw);q=row['dataset']=='Qwen_recovery';code=v['final_code'] if q else v['result'].get('final_code','')
            assert sha((code or '').encode())==by[row['dataset'],row['condition'],row['case']]['code_sha256']
    correlation_count=0
    if args.correlations:
        source=ROOT/'reference/working/task_complexity_latest/analyze.py'
        spec=importlib.util.spec_from_file_location('saved_correlation_functions',source);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        metadata={r['task']:r for r in read('task_metadata.json')}
        conditions={'C1':'c1_direct','C2':'c2_spec','C3':'c3_direct_review','C4':'c4_spec_review'}
        for row in read('task_correlations.json'):
            x=[metadata[t][row['metric']] for t in tasks]
            if row['endpoint_type']=='success':
                y=[sum(r['success'] for r in outcomes if r['dataset']==row['dataset'] and r['condition']==row['endpoint'] and r['task']==t) for t in tasks]
            else:
                a,b=row['endpoint'].split('→')
                y=[sum(r['success'] for r in outcomes if r['dataset']==row['dataset'] and r['condition']==conditions[b] and r['task']==t)-sum(r['success'] for r in outcomes if r['dataset']==row['dataset'] and r['condition']==conditions[a] and r['task']==t) for t in tasks]
            actual=mod.infer(x,y,row['seed'])
            for key in ['spearman_rho','permutation_p','bootstrap_95_low','bootstrap_95_high']:
                if row[key] is None:assert actual[key] is None
                else:close(actual[key],row[key])
            correlation_count+=1
        correlations=read('task_correlations.json')
        for row,p in zip(correlations,holm([r['permutation_p'] for r in correlations])):close(p,row['holm_p_all64'])
        for endpoint in ['success','contrast']:
            for metric in ['property_count','number_of_world_states']:
                family=[r for r in correlations if r['endpoint_type']==endpoint and r['metric']==metric]
                for row,p in zip(family,holm([r['permutation_p'] for r in family])):close(p,row['holm_p_family16'])
    report={'status':'PASSED','saved_outcomes':len(outcomes),'condition_counts':{':'.join(k):v for k,v in counts.items()},'paired_paths':len(pairs),'resource_paths':len(resources),'gate_paths':len(gate),'contract_signflip_and_mcnemar_reproduced':True,'initial_code_fallback_reproduced':True,'main_contrasts_reproduced':len(statistics),'gate_contrasts_reproduced':len(gate_stats),'sequential_curve':curves,'saved_final_records_hash_checked':len(raw_index),'correlations_reproduced':correlation_count,'new_model_calls':0,'new_simulator_runs':0}
    (ROOT/'verification_result.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['condition_counts','sequential_curve']}))

if __name__=='__main__':main()
