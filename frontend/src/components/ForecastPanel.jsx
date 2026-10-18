import React from "react";

export default function ForecastPanel({forecast}) {
  if(!forecast) return null;
  const pct=forecast.event_probability*100;
  const threshold=forecast.threshold*100;
  const above=forecast.event_probability>=forecast.threshold;

  return <section className="cardSection forecastCard">
    <div className="sectionHeader">
      <div><h2>60-minute deterioration forecast</h2><p>Calibrated probability of the simulator-defined hidden-state onset.</p></div>
    </div>
    <div className="forecastBody">
      <div className="riskSummary">
        <div className="riskRing" style={{"--risk":Math.min(100,Math.max(0,pct))+"%"}}>
          <div><strong>{pct.toFixed(1)}%</strong><span>within 60 min</span></div>
        </div>
      </div>
      <div className="forecastStatus">
        <div className={"forecastBanner"+(above?" alert":"")}>
          <span className="statusDot"/>
          <div><strong>{above ? "Prototype alert" : "Below prototype alert threshold"}</strong><p>{above ? "Current probability is at or above the prototype alert threshold." : "Current probability is below the prototype alert threshold."}</p></div>
        </div>
        <div className="forecastFacts">
          <div><span>Threshold</span><b>{threshold.toFixed(1)}%</b></div>
          <div><span>Forecast horizon</span><b>{forecast.forecast_horizon_minutes} min</b></div>
          <div><span>Data quality</span><b className="goodText">{forecast.data_quality.status}</b></div>
          <div><span>Last valid gap</span><b>{forecast.data_quality.time_since_valid_minutes} min</b></div>
        </div>
      </div>
    </div>
  </section>;
}
