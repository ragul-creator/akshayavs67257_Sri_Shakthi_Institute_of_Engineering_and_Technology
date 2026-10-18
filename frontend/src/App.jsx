import React,{useEffect,useState} from "react";
import {LineChart,Line,ResponsiveContainer,XAxis,YAxis,Tooltip,Legend,CartesianGrid} from "recharts";
import AblationTable from "./AblationTable.jsx";
const API="http://localhost:8000";

function Metric({label,value,sub}){
  return <div className="metric"><span>{label}</span><strong>{value}</strong>{sub&&<small>{sub}</small>}</div>
}
export default function App(){
  const [patients,setPatients]=useState([]),[pid,setPid]=useState(""),[twin,setTwin]=useState(null);
  const [obs,setObs]=useState([]),[evaluation,setEvaluation]=useState(null),[scenario,setScenario]=useState(null);
  const [error,setError]=useState("");
  const load=async(id)=>{
    try{
      setError("");
      const t=await fetch(API+"/patients/"+id+"/twin").then(r=>r.json());
      const o=await fetch(API+"/patients/"+id+"/observations").then(r=>r.json());
      setTwin(t);setObs(o);
    }catch(e){setError(String(e))}
  };
  useEffect(()=>{
    fetch(API+"/patients").then(r=>r.json()).then(x=>{setPatients(x);if(x[0])setPid(x[0].patient_id)});
    fetch(API+"/evaluation").then(r=>r.json()).then(setEvaluation);
  },[]);
  useEffect(()=>{if(pid)load(pid)},[pid]);
  const step=async()=>{
    const r=await fetch(API+"/simulation/step",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({patient_id:pid,steps:1})});
    setTwin(await r.json());
    setObs(await fetch(API+"/patients/"+pid+"/observations").then(x=>x.json()));
  };
  const reset=async()=>{
    await fetch(API+"/simulation/reset",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({patient_id:pid})});
    setScenario(null);load(pid);
  };
  const runScenario=async(name)=>{
    const r=await fetch(API+"/patients/"+pid+"/scenarios",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({scenario:name})});
    setScenario(await r.json());
  };
  const metric=evaluation?.ablations?.personalized;
  return <div className="app">
    <aside>
      <h1>Cardio<span>Twin</span></h1>
      <p className="tag">Understand the present. Anticipate the next. Explore what could change.</p>
      <label>Synthetic patient</label>
      <select value={pid} onChange={e=>setPid(e.target.value)}>{patients.map(p=><option key={p.patient_id}>{p.patient_id}</option>)}</select>
      <nav><a href="#overview">Twin Overview</a><a href="#explain">Explainability</a><a href="#scenario">What-if Simulator</a><a href="#evaluation">Model Evaluation</a></nav>
      <div className="notice">SYNTHETIC DATA ONLY<br/>Research prototype â€” not clinical decision-making.</div>
    </aside>
    <main>
      {error&&<div className="error">{error}</div>}
      {!twin?<div>Loading twinâ€¦</div>:<>
        <header>
          <div><p className="eyebrow">CARDIOVASCULAR DIGITAL TWIN</p><h2>{pid}</h2><p>Observation {new Date(twin.current_state.timestamp).toLocaleString()}</p></div>
          <div className="controls"><button onClick={reset}>Reset</button><button className="primary" onClick={step}>Advance +5 min</button></div>
        </header>
        <section id="overview">
          <div className="grid metrics">
            <Metric label="Heart rate" value={twin.current_state.heart_rate_bpm+" bpm"} sub={"Baseline "+twin.current_state.baseline_hr}/>
            <Metric label="Blood pressure" value={twin.current_state.systolic_bp+"/"+twin.current_state.diastolic_bp} sub="Simulated 5-min cadence"/>
            <Metric label="60-min event probability" value={(twin.forecast.event_probability*100).toFixed(1)+"%"} sub={twin.forecast.risk_category}/>
            <Metric label="Data quality" value={twin.forecast.data_quality.status} sub={"Sensor "+(twin.forecast.data_quality.sensor_quality*100).toFixed(0)+"%"}/>
          </div>
          <div className="panel">
            <div className="panelTitle"><h3>Recent physiological trajectory</h3><span>Observed/simulated history only</span></div>
            <ResponsiveContainer width="100%" height={290}><LineChart data={obs}>
              <CartesianGrid strokeDasharray="3 3" opacity={.15}/><XAxis dataKey="timestamp" tick={false}/>
              <YAxis yAxisId="hr"/><YAxis yAxisId="bp" orientation="right"/><Tooltip/><Legend/>
              <Line yAxisId="hr" type="monotone" dataKey="heart_rate_bpm" name="Heart rate" dot={false}/>
              <Line yAxisId="bp" type="monotone" dataKey="systolic_bp" name="Systolic BP" dot={false}/>
            </LineChart></ResponsiveContainer>
          </div>
        </section>
        <section id="explain" className="panel">
          <div className="panelTitle"><h3>Model explanation</h3><span>Influence proxies, not causal medical evidence</span></div>
          <div className="explain">{twin.forecast.explanation.map((x,i)=><div key={x.feature}><b>{i+1}. {x.label}</b><span>Current value: {x.value}</span><small>{x.note}</small></div>)}</div>
        </section>
        <section id="scenario" className="panel">
          <div className="panelTitle"><h3>What-if simulator</h3><span>Hypothetical trajectories only</span></div>
          <div className="scenarioButtons"><button onClick={()=>runScenario("return_toward_baseline")}>Return toward baseline</button><button onClick={()=>runScenario("increased_activity")}>Increased activity</button></div>
          {scenario&&<div className="scenarioResult"><strong>{(scenario.baseline_probability*100).toFixed(1)}% to {(scenario.scenario_probability*100).toFixed(1)}%</strong><p>{scenario.assumptions.join(" ")}</p><small>{scenario.warning}</small></div>}
        </section>
        <section id="evaluation" className="panel">
          <div className="panelTitle"><h3>Held-out synthetic-patient evaluation</h3><span>Actual saved evaluation output</span></div>
          {metric?<div className="grid eval"><Metric label="Precision" value={metric.precision.toFixed(3)}/><Metric label="Recall" value={metric.recall.toFixed(3)}/><Metric label="F1" value={metric.f1.toFixed(3)}/><Metric label="ROC-AUC" value={metric.roc_auc.toFixed(3)}/><Metric label="PR-AUC" value={metric.pr_auc.toFixed(3)}/><Metric label="Brier" value={metric.brier.toFixed(3)}/></div>:<p>Evaluation unavailable.</p>}<AblationTable data={evaluation?.ablations}/>
        </section>
      </>}
    </main>
  </div>
}

