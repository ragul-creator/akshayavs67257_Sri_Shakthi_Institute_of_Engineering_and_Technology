import React from "react";

export default function ForecastPanel({forecast, current}) {
  if (!forecast) return null;
  const pct = forecast.event_probability * 100;
  const threshold = forecast.threshold * 100;
  return <section className="forecastPanel">
    <div className="forecastMain">
      <span className="sectionKicker">NEXT 60 MINUTES</span>
      <div className="probability">{pct.toFixed(1)}<em>%</em></div>
      <p>calibrated probability of the simulator-defined latent deterioration onset</p>
    </div>
    <div className="forecastDetail">
      <div className="thresholdScale">
        <div className="thresholdTrack">
          <i className="probMarker" style={{left: Math.min(pct,100) + "%"}} />
          <i className="thresholdMarker" style={{left: Math.min(threshold,100) + "%"}} />
        </div>
        <div className="scaleLabels"><span>0%</span><span>prototype alert threshold {threshold.toFixed(1)}%</span><span>100%</span></div>
      </div>
      <dl>
        <div><dt>Status</dt><dd>{forecast.risk_category}</dd></div>
        <div><dt>Signal quality</dt><dd>{forecast.data_quality.status}</dd></div>
        <div><dt>Last valid gap</dt><dd>{forecast.data_quality.time_since_valid_minutes} min</dd></div>
        <div><dt>HR vs baseline</dt><dd>{current.hr_deviation >= 0 ? "+" : ""}{current.hr_deviation} bpm</dd></div>
        <div><dt>SBP vs baseline</dt><dd>{current.systolic_deviation >= 0 ? "+" : ""}{current.systolic_deviation} mmHg</dd></div>
      </dl>
    </div>
  </section>;
}
