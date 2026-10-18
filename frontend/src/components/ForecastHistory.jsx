import React from "react";

export default function ForecastHistory({history,threshold}) {
  const rows=[...(history||[])].slice(-6).reverse();
  return <section className="cardSection forecastHistory">
    <div className="sectionHeader">
      <div><h2>Forecast history</h2><p>Predictions recorded while the replay clock advances.</p></div>
    </div>
    {rows.length ? <div className="tableScroll">
      <table className="historyTable">
        <thead><tr><th>Time</th><th>Probability</th><th>Status</th><th>State confidence</th></tr></thead>
        <tbody>{rows.map((row,index)=><tr key={row.timestamp+"-"+index}>
          <td>{new Date(row.timestamp).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}</td>
          <td><strong>{(row.event_probability*100).toFixed(1)}%</strong></td>
          <td><span className={row.event_probability>=threshold ? "statusPill alert":"statusPill"}>{row.event_probability>=threshold ? "prototype alert" : "below threshold"}</span></td>
          <td>{row.confidence!=null ? Math.round(row.confidence*100)+"%" : "—"}</td>
        </tr>)}</tbody>
      </table>
    </div> : <div className="emptyHistory">Advance the replay clock to build forecast history.</div>}
  </section>;
}
