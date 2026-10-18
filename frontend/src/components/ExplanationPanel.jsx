import React from "react";

export default function ExplanationPanel({items}) {
  if (!items?.length) return null;
  const magnitude = item => Math.abs(item.shap_value ?? item.importance_proxy ?? 0);
  const max = Math.max(...items.map(magnitude), 1e-6);
  return <section className="workPanel explanationPanel">
    <div className="panelHeading">
      <div><h2>Why this model score?</h2><p>{items[0]?.method || "Model contribution analysis"}. Contribution is not causality.</p></div>
    </div>
    <div className="contributionRows">
      {items.map(item => {
        const value = item.shap_value ?? item.importance_proxy ?? 0;
        return <div className="contribution" key={item.feature}>
          <div className="contributionText"><b>{item.label}</b><span>{item.value}</span></div>
          <div className="contributionTrack">
            <i className={value >= 0 ? "positive" : "negative"} style={{width: ((Math.abs(value)/max)*100) + "%"}} />
          </div>
          <small>{item.direction || "relative influence"}</small>
        </div>;
      })}
    </div>
  </section>;
}
