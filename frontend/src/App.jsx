import React,{useEffect,useState} from "react";
import {api} from "./services/api.js";
import PatientSidebar from "./components/PatientSidebar.jsx";
import VitalCards from "./components/VitalCards.jsx";
import Timeline from "./components/Timeline.jsx";
import ForecastPanel from "./components/ForecastPanel.jsx";
import ForecastHistory from "./components/ForecastHistory.jsx";
import ExplanationPanel from "./components/ExplanationPanel.jsx";
import ScenarioLab from "./components/ScenarioLab.jsx";
import EvaluationView from "./components/EvaluationView.jsx";
import RightContext from "./components/RightContext.jsx";
import "./styles.css";

export default function App(){
  const [patients,setPatients]=useState([]);
  const [patientId,setPatientId]=useState("");
  const [twin,setTwin]=useState(null);
  const [observations,setObservations]=useState([]);
  const [evaluation,setEvaluation]=useState(null);
  const [view,setView]=useState("overview");
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
    setBusy(true);
    setError("");
    try{
      const next=await api.step(patientId,steps);
      setTwin(next);
      setObservations(await api.observations(patientId,96));
    }catch(err){
      setError(err.message || String(err));
    }finally{
      setBusy(false);
    }
  };

  const reset=async()=>{
    setBusy(true);
    setError("");
    try{
      await api.reset(patientId);
      await loadPatient(patientId);
    }catch(err){
      setError(err.message || String(err));
    }finally{
      setBusy(false);
    }
  };

  const runScenario=async name=>{
    setBusy(true);
    setError("");
    try{
      return await api.scenario(patientId,name);
    }catch(err){
      setError(err.message || String(err));
      throw err;
    }finally{
      setBusy(false);
    }
  };

  const profile=twin?.profile;
  const current=twin?.current_state;

  return <div className="appFrame">
    <PatientSidebar
      patients={patients}
      patientId={patientId}
      onSelect={setPatientId}
      busy={busy}
    />

    <main className="mainColumn">
      {error&&<div className="errorBanner">{error}</div>}

      {!twin
        ? <div className="loadingState">Loading patient twin...</div>
        : <div className={"workspaceLayout"+(view==="evaluation"?" evaluationMode":"")}>
            <section className="centerWorkspace">
              <header className="workspaceHeader">
                {view==="evaluation" ? <div className="workspaceIdentity">
                  <div className="titleRow"><h1>Model Evaluation</h1></div>
                  <p>Held-out synthetic-patient performance, operating points, and robustness checks.</p>
                </div> : <>
                  <div className="workspaceIdentity">
                    <div className="titleRow">
                      <h1>Digital Twin</h1>
                      <span>{twin.patient_id}</span>
                      {profile&&<small>{profile.age} years · {profile.sex}</small>}
                    </div>
                    <p>Observable-state replay for synthetic cardiovascular research.</p>
                  </div>
                  <div className="observationStamp">
                    <span>Last observation</span>
                    <strong>{new Date(current.timestamp).toLocaleString()}</strong>
                  </div>
                </>}
              </header>

              <nav className="workspaceTabs" aria-label="CardioTwin views">
                <button className={view==="overview"?"active":""} onClick={()=>setView("overview")}>Overview</button>
                <button className={view==="scenarios"?"active":""} onClick={()=>setView("scenarios")}>Scenarios</button>
                <button className={view==="evaluation"?"active":""} onClick={()=>setView("evaluation")}>Evaluation</button>
              </nav>

              {view!=="evaluation"&&<div className="replayStrip">
                <div className="replayInfo">
                  <span>Replay clock</span>
                  <strong>{current.activity_state}</strong>
                  <div className="replayProgress"><i style={{width:(twin.simulation.progress*100)+"%"}}/></div>
                  <small>{Math.round(twin.simulation.progress*100)}%</small>
                </div>
                <div className="replayActions">
                  <button onClick={()=>step(1)} disabled={busy}>+ 5 min</button>
                  <button onClick={()=>step(6)} disabled={busy}>+ 30 min</button>
                  <button className="secondaryButton" onClick={reset} disabled={busy}>Reset</button>
                </div>
              </div>}

              {view==="overview"&&<>
                <VitalCards twin={twin}/>
                <Timeline
                  observations={observations}
                  baselineHr={current.baseline_hr}
                  baselineSbp={current.baseline_systolic_bp}
                />
                <ForecastPanel forecast={twin.forecast}/>
                <ForecastHistory history={twin.forecast_history} threshold={twin.forecast.threshold}/>
                <ExplanationPanel items={twin.forecast.explanation}/>
              </>}

              {view==="scenarios"&&
                <ScenarioLab patientId={patientId} runScenario={runScenario} busy={busy}/>
              }

              {view==="evaluation"&&
                <EvaluationView evaluation={evaluation}/>
              }
            </section>

            {view!=="evaluation"&&<RightContext twin={twin}/>}
          </div>}
    </main>
  </div>;
}
