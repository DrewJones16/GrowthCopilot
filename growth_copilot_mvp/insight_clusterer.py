from typing import Any, Dict, List
SEVERITY_RANK = {"CRITICAL": 3, "WATCH": 2, "OPPORTUNITY": 1}
def cluster_title(insights):
    text = " ".join(i.summary.lower() for i in insights)
    if "tiktok" in text and ("funnel" in text or "dropped" in text or "complete" in text): return "TikTok activation failure"
    if "onboarding" in text: return "Onboarding conversion regression"
    if "installs" in text: return "Acquisition anomaly"
    return "Growth opportunity"
def cluster_severity(insights):
    types = [getattr(i, "type", "") for i in insights]
    if any(t == "funnel_drop" for t in types): return "CRITICAL"
    if any(t in ("cohort_divergence", "anomaly") for t in types): return "WATCH"
    return "OPPORTUNITY"
def cluster_recommendation(insights):
    text = " ".join(i.summary.lower() for i in insights)
    if "tiktok" in text: return "Inspect recent TikTok onboarding changes, campaign quality, and attribution integrity."
    if "onboarding" in text: return "Review onboarding funnel changes deployed within the last 7 days."
    if "installs" in text: return "Investigate acquisition channel performance and any recent campaign or store listing changes."
    return "Review underlying metrics for anomalies and compare against recent product changes."
def _sample_score(n):
    if n>=1000: return 1.00
    if n>=500: return 0.85
    if n>=300: return 0.70
    if n>=200: return 0.58
    if n>=100: return 0.42
    if n>=50: return 0.25
    if n>=20: return 0.12
    return 0.05
def _effect_score(es):
    if es>=0.30: return 1.00
    if es>=0.20: return 0.85
    if es>=0.15: return 0.70
    if es>=0.10: return 0.55
    if es>=0.07: return 0.42
    if es>=0.05: return 0.30
    if es>=0.03: return 0.18
    if es>=0.02: return 0.10
    return 0.03
def _stab_score(s):
    if s=="stable": return 1.00
    if s=="noisy": return 0.35
    return 0.15
def _novelty_score(n):
    if n=="new": return 1.00
    if n=="ongoing_worsening": return 0.70
    if n=="ongoing_improving": return 0.60
    if n=="ongoing_unchanged": return 0.20
    return 0.40
def _mad_ratio_bonus(insight):
    rm=getattr(insight,"raw_metrics",{})
    ratio=rm.get("mad_ratio") or rm.get("z_score") or 0
    if ratio is None: return 0.0
    if ratio>=10: return 0.08
    if ratio>=5: return 0.05
    if ratio>=3: return 0.02
    return 0.0
def _factors(insight):
    ci=getattr(insight,"confidence_inputs",None)
    if ci is None: return {"sample_size":0.20,"effect_size":0.20,"baseline_stability":0.20,"novelty":0.40}
    return {"sample_size":_sample_score(getattr(ci,"sample_size",0)),"effect_size":_effect_score(getattr(ci,"effect_size",0.0)),"baseline_stability":_stab_score(getattr(ci,"baseline_stability","unknown")),"novelty":_novelty_score(getattr(insight,"novelty_vs_prior",""))}
def _score(insight):
    f=_factors(insight)
    bonus=_mad_ratio_bonus(insight)
    raw=f["sample_size"]*32+f["effect_size"]*32+f["baseline_stability"]*22+f["novelty"]*14+bonus*100
    return min(int(round(raw)),100)
def cluster_confidence(insights):
    if not insights: return {"score":0,"label":"Low","factors":{},"detector_agreement":False}
    all_f=[_factors(i) for i in insights]
    avg={k:round(sum(f[k] for f in all_f)/len(all_f),2) for k in all_f[0]}
    types={getattr(i,"type","") for i in insights}
    agree=len(types)>=2
    agree_bonus=8 if len(types)>=3 else 4 if len(types)==2 else 0
    avg["detector_agreement"]=1.0 if agree else 0.0
    scores=[_score(i) for i in insights]
    base=sum(scores)/len(scores)
    base=min(base+agree_bonus,100)
    if len(insights)>=3: base=min(base+3,100)
    novelties=[getattr(i,"novelty_vs_prior","") for i in insights]
    if not agree and all(n=="ongoing_unchanged" for n in novelties): base=max(base-10,0)
    score=int(round(base))
    label="High" if score>=68 else "Medium" if score>=42 else "Low"
    return {"score":score,"label":label,"factors":avg,"detector_agreement":agree}
def _get_evidence(i): return list(getattr(i,"evidence",[]) or [])
def _get_affected_metrics(i): return list(getattr(i,"affected_metrics",[]) or [])
def _cluster_key(insight):
    t=getattr(insight,"type","other")
    s=getattr(insight,"summary","").lower()
    if "tiktok" in s: return "tiktok"
    if t in ("funnel_drop","cohort_divergence"): return "funnel"
    if t=="anomaly": return "anomaly"
    return "other"
def cluster_insights(ranked):
    if not ranked: return []
    buckets={}
    for insight in ranked:
        k=_cluster_key(insight)
        buckets.setdefault(k,[]).append(insight)
    clusters=[]
    for key,insights in buckets.items():
        ce,sm,cm,se=[],set(),[],set()
        for ins in insights:
            for ev in _get_evidence(ins):
                if ev not in sm: ce.append(ev); sm.add(ev)
            for m in _get_affected_metrics(ins):
                if m not in se: cm.append(m); se.add(m)
        sev=cluster_severity(insights)
        conf=cluster_confidence(insights)
        clusters.append({"title":cluster_title(insights),"severity":sev,"confidence":conf,"recommendation":cluster_recommendation(insights),"insights":insights,"combined_evidence":ce,"affected_metrics":cm})
    clusters.sort(key=lambda c:(SEVERITY_RANK.get(c["severity"],0),c["confidence"]["score"],len(c["insights"])),reverse=True)
    return clusters
