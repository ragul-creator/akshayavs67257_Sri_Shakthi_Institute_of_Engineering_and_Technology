import React from "react";

export default function AblationTable({data}){
  if(!data) return null;
  const labels={ehr_only:"EHR only",wearable_only:"Wearable only",fusion:"EHR + wearable",personalized:"Fusion + personal baseline"};
  return <div className="tableWrap">
    <table>
      <thead><tr><th>Configuration</th><th>F1</th><th>ROC-AUC</th><th>PR-AUC</th><th>Threshold</th></tr></thead>
      <tbody>{Object.entries(data).map(([name,m])=><tr key={name}>
        <td>{labels[name]||name}</td><td>{m.f1.toFixed(3)}</td><td>{m.roc_auc.toFixed(3)}</td>
        <td>{m.pr_auc.toFixed(3)}</td><td>{m.threshold.toFixed(2)}</td>
      </tr>)}</tbody>
    </table>
  </div>
}
