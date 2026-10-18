import React,{useEffect,useState} from "react";
import {api} from "./services/api.js";
import PatientSidebar from "./components/PatientSidebar.jsx";
import Timeline from "./components/Timeline.jsx";
import ForecastPanel from "./components/ForecastPanel.jsx";
import StatePanel from "./components/StatePanel.jsx";
import ExplanationPanel from "./components/ExplanationPanel.jsx";
import ScenarioLab from "./components/ScenarioLab.jsx";
import EvaluationView from "./components/EvaluationView.jsx";
import "./styles.css";

export default function App(){
  const [patients,setPatients]=useState([]);
  const [patientId,setPatientId]=useState("");
  const [twin,setTwin]=useState(null);
  const [observations,setObservations]=useState([]);
  const [evaluation,setEvaluation]=useState(null);
  const [view,setView]=useState("twin");
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState("");

  const loadPatient=async id=>{
    if(!id) return;
    setBusy(true);
    setError("");
    try{
      const [t,o]=await Promise.all([api.twin(id),api.observations(id,96)]);
      setTwin(t);
      setObservations(o);
    }catch(err){
      setError(err.message || String(err));
    }finally{
      setBusy(false);
    }
  };

  useEffect(()=>{
    Promise.all([api.patients(),api.evaluation()])
      .then(([p,e])=>{
        setPatients(p);
        setEvaluation(e);
        if(p[0]) setPatientId(p[0].patient_id);
      })
      .catch(err=>setError(err.message || String(err)));
  },[]);

  useEffect(()=>{loadPatient(patientId)},[patientId]);

  const step=async steps=>{
    setBusy(true);setError("");
    try{
      const next=await api.step(patientId,steps);
      setTwin(next);
      setObservations(await api.observations(patientId,96));
    }catch(err){setError(err.message || String(err))}
    finally{setBusy(false)}
  };

  const reset=async()=>{
    setBusy(true);setError("");
    try{
      await api.reset(patientId);
      await loadPatient(patientId);
    }catch(err){setError(err.message || String(err))}
    finally{setBusy(false)}
  };

  const runScenario=async name=>{
    setBusy(true);setError("");
    try{return await api.scenario(patientId,name)}
    catch(err){setError(err.message || String(err));throw err}
    finally{setBusy(false)}
  };

  return <div className="shell">
    <PatientSidebar
      patients={patients}
      patientId={patientId}
      twin={twin}
      onSelect={setPatientId}
      onStep={step}
      onReset={reset}
      busy={busy}
    />

    <main className="workspace">
      <div className="topBar">
        <div className="viewTabs">
          <button className={view==="twin"?"active":""} onClick={()=>setView("twin")}>Twin workspace</button>
          <button className={view==="evaluation"?"active":""} onClick={()=>setView("evaluation")}>Evaluation</button>
        </div>
        <div className="modelStamp">
          <span>{twin?.forecast?.model_version || "model loading"}</span>
          <b>{busy?"working":"ready"}</b>
        </div>
      </div>

      {error&&<div className="errorBanner">{error}</div>}

      {view==="evaluation"
        ? <EvaluationView evaluation={evaluation}/>
        : !twin
          ? <div className="loadingState">Loading patient twin...</div>
          : <div className="twinWorkspace">
              <header className="patientHeader">
                <div>
                  <span className="sectionKicker">LIVE REPLAY / OBSERVABLE STATE ONLY</span>
                  <h1>{twin.patient_id}</h1>
                  <p>{new Date(twin.current_state.timestamp).toLocaleString()} · {twin.current_state.activity_state}</p>
                </div>
                <div className="vitalReadout">
                  <div><span>HR</span><b>{twin.current_state.heart_rate_bpm}</b><small>bpm</small></div>
                  <div><span>BP</span><b>{twin.current_state.systolic_bp}/{twin.current_state.diastolic_bp}</b><small>mmHg</small></div>
                  <div><span>HRV</span><b>{twin.current_state.hrv_ms}</b><small>ms</small></div>
                </div>
              </header>

              <ForecastPanel forecast={twin.forecast} current={twin.current_state}/>

              <div className="primaryGrid">
                <Timeline observations={observations}/>
                <StatePanel state={twin.estimated_state}/>
              </div>

              <div className="secondaryGrid">
                <ExplanationPanel items={twin.forecast.explanation}/>
                <ScenarioLab patientId={patientId} runScenario={runScenario} busy={busy}/>
              </div>

              <footer className="workspaceFoot">
                Synthetic physiology and hidden-state events. Retrospective event truth is kept separate from this live workspace.
              </footer>
            </div>}
    </main>
  </div>;
}
