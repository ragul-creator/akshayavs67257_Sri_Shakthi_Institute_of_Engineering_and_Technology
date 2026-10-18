import React from "react";
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,Tooltip,CartesianGrid} from "recharts";

const names={ehr_only:"EHR only",wearable_only:"Wearable only",fusion:"EHR + wearable",personalized:"Personalized fusion"};

function ciText(ci){
  if(!ci) return "—";
  return ci.low_95.toFixed(3)+"–"+ci.high_95.toFixed(3);
}

export default function EvaluationView({evaluation}) {
  if(!evaluation) return <div className="loadingState">Loading evaluation...</div>;
  const selected=evaluation.ablations.personalized;
  const ci=evaluation.bootstrap_95_ci || {};
  const event=evaluation.selected_event_metrics;

  return <div className="evaluationWorkspace">
    <section className="evaluationLead">
      <div>
        <span className="sectionKicker">HELD-OUT SYNTHETIC PATIENTS</span>
        <h1>Model evaluation</h1>
        <p>Patient-level split. Active event periods are excluded from the early-warning classifier. Confidence intervals bootstrap patients, not rows.</p>
      </div>
      <div className="datasetStamp">
        <span>{evaluation.dataset.test_patients} test patients</span>
        <span>{evaluation.dataset.eligible_rows.toLocaleString()} eligible rows</span>
        <span>{(evaluation.dataset.eligible_positive_rate*100).toFixed(1)}% positive</span>
      </div>
    </section>

    <section className="workPanel">
      <div className="panelHeading"><div><h2>Selected operating point</h2><p>Threshold selected on validation patients; values below are held-out.</p></div></div>
      <table className="metricsTable">
        <thead><tr><th>Metric</th><th>Estimate</th><th>Patient bootstrap 95% CI</th></tr></thead>
        <tbody>
          <tr><td>ROC-AUC</td><td>{selected.roc_auc.toFixed(3)}</td><td>{ciText(ci.roc_auc)}</td></tr>
          <tr><td>PR-AUC</td><td>{selected.pr_auc.toFixed(3)}</td><td>{ciText(ci.pr_auc)}</td></tr>
          <tr><td>F1</td><td>{selected.f1.toFixed(3)}</td><td>{ciText(ci.f1)}</td></tr>
          <tr><td>Precision</td><td>{selected.precision.toFixed(3)}</td><td>{ciText(ci.precision)}</td></tr>
          <tr><td>Recall</td><td>{selected.recall.toFixed(3)}</td><td>{ciText(ci.recall)}</td></tr>
          <tr><td>Brier</td><td>{selected.brier.toFixed(3)}</td><td>{ciText(ci.brier)}</td></tr>
        </tbody>
      </table>
      <div className="eventLine">
        <span>{event.detected_events}/{event.test_events} events detected</span>
        <span>{event.median_early_warning_minutes.toFixed(1)} min median lead time</span>
        <span>{event.false_alerts_per_patient_day.toFixed(2)} false alert episodes / patient-day</span>
      </div>
    </section>

    <div className="evalGrid">
      <section className="workPanel">
        <div className="panelHeading"><div><h2>Ablation study</h2><p>Does personalization add signal?</p></div></div>
        <table className="metricsTable">
          <thead><tr><th>Input</th><th>ROC</th><th>PR</th><th>F1</th></tr></thead>
          <tbody>{Object.entries(evaluation.ablations).map(([key,m])=><tr key={key}>
            <td>{names[key]||key}</td><td>{m.roc_auc.toFixed(3)}</td><td>{m.pr_auc.toFixed(3)}</td><td>{m.f1.toFixed(3)}</td>
          </tr>)}</tbody>
        </table>
      </section>

      <section className="workPanel">
        <div className="panelHeading"><div><h2>Operating curve</h2><p>Event detection versus false-alert burden.</p></div></div>
        <ResponsiveContainer width="100%" height={270}>
          <LineChart data={evaluation.operating_curve} margin={{top:8,right:10,left:-12,bottom:0}}>
            <CartesianGrid vertical={false} stroke="#1f2b37"/>
            <XAxis dataKey="false_alerts_per_patient_day" stroke="#647281" tick={{fontSize:10}}/>
            <YAxis domain={[0,1]} stroke="#647281" tick={{fontSize:10}}/>
            <Tooltip/>
            <Line type="monotone" dataKey="event_detection_rate" name="Event detection" stroke="#63b3ff" dot={false}/>
            <Line type="monotone" dataKey="precision" name="Precision" stroke="#d9a441" dot={false}/>
          </LineChart>
        </ResponsiveContainer>
      </section>
    </div>

    <div className="evalGrid evidenceGrid">
      <section className="workPanel">
        <div className="panelHeading">
          <div><h2>Out-of-seed stress test</h2><p>Three newly generated cohorts; this is still synthetic, not external clinical validation.</p></div>
        </div>
        {evaluation.multiseed ? <table className="metricsTable">
          <thead><tr><th>Metric</th><th>Mean</th><th>Seed-to-seed SD</th></tr></thead>
          <tbody>
            <tr><td>ROC-AUC</td><td>{evaluation.multiseed.summary.roc_auc.mean.toFixed(3)}</td><td>{evaluation.multiseed.summary.roc_auc.std.toFixed(3)}</td></tr>
            <tr><td>PR-AUC</td><td>{evaluation.multiseed.summary.pr_auc.mean.toFixed(3)}</td><td>{evaluation.multiseed.summary.pr_auc.std.toFixed(3)}</td></tr>
            <tr><td>F1</td><td>{evaluation.multiseed.summary.f1.mean.toFixed(3)}</td><td>{evaluation.multiseed.summary.f1.std.toFixed(3)}</td></tr>
            <tr><td>Event detection</td><td>{evaluation.multiseed.summary.event_detection_rate.mean.toFixed(3)}</td><td>{evaluation.multiseed.summary.event_detection_rate.std.toFixed(3)}</td></tr>
            <tr><td>False alerts / patient-day</td><td>{evaluation.multiseed.summary.false_alerts_per_patient_day.mean.toFixed(2)}</td><td>{evaluation.multiseed.summary.false_alerts_per_patient_day.std.toFixed(2)}</td></tr>
          </tbody>
        </table> : <p className="mutedText">Out-of-seed evaluation has not been run.</p>}
      </section>

      <section className="workPanel">
        <div className="panelHeading">
          <div><h2>Measurement robustness</h2><p>Same held-out patients under controlled degradation of observable inputs.</p></div>
        </div>
        {evaluation.robustness ? <table className="metricsTable">
          <thead><tr><th>Condition</th><th>ROC</th><th>PR</th><th>F1</th></tr></thead>
          <tbody>{Object.entries(evaluation.robustness).map(([key,m])=><tr key={key}>
            <td>{key.replaceAll("_"," ")}</td><td>{m.roc_auc.toFixed(3)}</td><td>{m.pr_auc.toFixed(3)}</td><td>{m.f1.toFixed(3)}</td>
          </tr>)}</tbody>
        </table> : <p className="mutedText">Robustness evaluation has not been run.</p>}
      </section>
    </div>
  </div>;
}
