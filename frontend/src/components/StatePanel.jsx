import React from "react";

const labels = {
  cardiovascular_load: "Cardiovascular load",
  autonomic_instability: "Autonomic instability",
  recovery_debt: "Recovery debt",
  trajectory_instability: "Trajectory instability",
};

export default function StatePanel({state}) {
  if (!state) return null;
  return <section className="workPanel statePanel">
    <div className="panelHeading compact">
      <div><h2>Estimated state</h2><p>Filtered from observed physiology; hidden simulator state is inaccessible.</p></div>
    </div>
    <div className="strainIndex">
      <span>Composite strain</span>
      <b>{Math.round(state.physiologic_strain * 100)}</b>
      <small>/ 100</small>
    </div>
    <div className="stateRows">
      {Object.entries(labels).map(([key,label]) => <div className="stateRow" key={key}>
        <div><span>{label}</span><b>{Math.round(state[key] * 100)}</b></div>
        <div className="stateTrack"><i style={{width:(state[key] * 100) + "%"}} /></div>
      </div>)}
    </div>
    <div className="confidenceLine">
      <span>Estimate confidence</span>
      <b>{Math.round(state.confidence * 100)}%</b>
    </div>
  </section>;
}
