import React from "react";

const stateLabels={
  cardiovascular_load:"Cardiovascular load",
  autonomic_instability:"Autonomic instability",
  recovery_debt:"Recovery debt",
  trajectory_instability:"Trajectory instability",
};

function InfoCard({title,children}) {
  return <section className="contextCard">
    <div className="contextTitle">{title}</div>
    {children}
  </section>;
}

export default function RightContext({twin}) {
  if(!twin) return null;
  const profile=twin.profile;
  const current=twin.current_state;
  const estimate=twin.estimated_state;
  const forecast=twin.forecast;

  return <aside className="contextRail">
    <InfoCard title="Patient baseline">
      <div className="contextRows">
        <div><span>Baseline HR</span><b>{current.baseline_hr} bpm</b></div>
        <div><span>Baseline SBP</span><b>{current.baseline_systolic_bp} mmHg</b></div>
        <div><span>BMI</span><b>{Number(profile.bmi).toFixed(1)}</b></div>
        <div><span>Hypertension history</span><b>{profile.hypertension_history ? "Yes":"No"}</b></div>
        <div><span>Diabetes</span><b>{profile.diabetes_status ? "Yes":"No"}</b></div>
        <div><span>Smoking</span><b>{profile.smoking_status}</b></div>
      </div>
    </InfoCard>

    <InfoCard title="Estimated twin state">
      <div className="stateList">
        {Object.entries(stateLabels).map(([key,label])=><div className="stateItem" key={key}>
          <div><span>{label}</span><b>{estimate[key].toFixed(2)}</b></div>
          <div className="stateBar"><i style={{width:(estimate[key]*100)+"%"}}/></div>
        </div>)}
        <div className="stateItem emphasized">
          <div><span>Composite strain</span><b>{estimate.physiologic_strain.toFixed(2)}</b></div>
          <div className="stateBar"><i style={{width:(estimate.physiologic_strain*100)+"%"}}/></div>
        </div>
      </div>
    </InfoCard>

    <InfoCard title="Model context">
      <div className="contextRows">
        <div><span>Forecast (60 min)</span><b>{(forecast.event_probability*100).toFixed(1)}%</b></div>
        <div><span>Alert threshold</span><b>{(forecast.threshold*100).toFixed(1)}%</b></div>
        <div><span>State confidence</span><b>{Math.round(estimate.confidence*100)}%</b></div>
        <div><span>Signal quality</span><b className="goodText">{forecast.data_quality.status}</b></div>
        <div><span>Model</span><b>{forecast.model_version.replace("cardiotwin-","")}</b></div>
      </div>
    </InfoCard>
  </aside>;
}
