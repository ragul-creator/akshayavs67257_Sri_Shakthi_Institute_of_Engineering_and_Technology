import React from "react";

export default function PatientSidebar({patients, patientId, twin, onSelect, onStep, onReset, busy}) {
  const profile = twin?.profile;
  const state = twin?.current_state;
  return <aside className="patientRail">
    <div className="brand">
      <div className="brandMark">CT</div>
      <div><strong>CardioTwin</strong><span>research simulator</span></div>
    </div>

    <div className="railSection">
      <label className="fieldLabel">Synthetic patient</label>
      <select value={patientId} onChange={e => onSelect(e.target.value)} disabled={busy}>
        {patients.map(p => <option key={p.patient_id} value={p.patient_id}>{p.patient_id}</option>)}
      </select>
    </div>

    {profile && <div className="profileTable">
      <div><span>Age</span><b>{profile.age}</b></div>
      <div><span>Sex</span><b>{profile.sex}</b></div>
      <div><span>BMI</span><b>{Number(profile.bmi).toFixed(1)}</b></div>
      <div><span>Hypertension hx</span><b>{profile.hypertension_history ? "yes" : "no"}</b></div>
      <div><span>Diabetes</span><b>{profile.diabetes_status ? "yes" : "no"}</b></div>
      <div><span>Smoking</span><b>{profile.smoking_status}</b></div>
    </div>}

    {state && <div className="baselineBlock">
      <div className="fieldLabel">Reference baseline</div>
      <p><span>Heart rate</span><b>{state.baseline_hr} bpm</b></p>
      <p><span>Systolic BP</span><b>{state.baseline_systolic_bp} mmHg</b></p>
    </div>}

    <div className="railSection replayControls">
      <div className="fieldLabel">Replay clock</div>
      <button onClick={() => onStep(1)} disabled={busy}>+ 5 min</button>
      <button onClick={() => onStep(6)} disabled={busy}>+ 30 min</button>
      <button className="quietButton" onClick={onReset} disabled={busy}>Reset</button>
    </div>

    {twin && <div className="progressBlock">
      <div><span>Replay position</span><b>{Math.round(twin.simulation.progress * 100)}%</b></div>
      <div className="progressTrack"><i style={{width: (twin.simulation.progress * 100) + "%"}} /></div>
    </div>}

    <div className="railDisclaimer">
      <strong>SYNTHETIC RESEARCH DATA</strong>
      <p>Not a diagnosis, triage system, or treatment recommendation.</p>
    </div>
  </aside>;
}
