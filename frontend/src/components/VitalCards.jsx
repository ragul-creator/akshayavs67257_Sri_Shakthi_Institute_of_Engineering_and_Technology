import React from "react";

function VitalCard({code,label,value,unit,delta,tone="teal"}) {
  return <div className="vitalCard">
    <div className={"vitalIcon " + tone}>{code}</div>
    <div className="vitalCopy">
      <span>{label}</span>
      <div><strong>{value}</strong>{unit && <small>{unit}</small>}</div>
      {delta && <em>{delta}</em>}
    </div>
  </div>;
}

export default function VitalCards({twin}) {
  const state=twin.current_state;
  const quality=twin.forecast.data_quality;
  const hrDelta=state.hr_deviation;
  const sbpDelta=state.systolic_deviation;
  return <div className="vitalGrid">
    <VitalCard code="HR" label="Heart rate" value={state.heart_rate_bpm} unit="bpm"
      delta={(hrDelta>=0?"+":"")+hrDelta+" vs baseline"} tone="coral"/>
    <VitalCard code="BP" label="Blood pressure" value={state.systolic_bp+"/"+state.diastolic_bp} unit="mmHg"
      delta={(sbpDelta>=0?"+":"")+sbpDelta+" systolic"} tone="amber"/>
    <VitalCard code="HRV" label="HRV" value={state.hrv_ms} unit="ms" tone="blue"/>
    <VitalCard code="Q" label="Data quality" value={Math.round(quality.quality_mean_60*100)} unit="%"
      delta={quality.status} tone="teal"/>
  </div>;
}
