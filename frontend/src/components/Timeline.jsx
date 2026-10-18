import React from "react";
import {ResponsiveContainer, LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, Legend} from "recharts";

const tickTime = value => {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"});
};

export default function Timeline({observations}) {
  return <section className="workPanel timelinePanel">
    <div className="panelHeading">
      <div><h2>Physiology timeline</h2><p>Only observations available up to the replay clock are shown.</p></div>
      <div className="legendNote">5-minute simulated cadence</div>
    </div>
    <div className="chartFrame">
      <ResponsiveContainer width="100%" height={330}>
        <LineChart data={observations} margin={{top:8,right:12,left:-16,bottom:4}}>
          <CartesianGrid vertical={false} stroke="#1f2b37" />
          <XAxis dataKey="timestamp" tickFormatter={tickTime} minTickGap={42} stroke="#647281" tick={{fontSize:11}} />
          <YAxis yAxisId="hr" domain={["dataMin - 8","dataMax + 8"]} stroke="#647281" tick={{fontSize:11}} />
          <YAxis yAxisId="bp" orientation="right" domain={["dataMin - 10","dataMax + 10"]} stroke="#647281" tick={{fontSize:11}} />
          <Tooltip labelFormatter={tickTime} contentStyle={{background:"#0c131a",border:"1px solid #26323e",borderRadius:2}} />
          <Legend wrapperStyle={{fontSize:11}} />
          <Line yAxisId="hr" type="monotone" dataKey="heart_rate_bpm" name="Heart rate" stroke="#63b3ff" strokeWidth={2} dot={false} isAnimationActive={false}/>
          <Line yAxisId="bp" type="monotone" dataKey="systolic_bp" name="Systolic BP" stroke="#d9a441" strokeWidth={1.5} dot={false} isAnimationActive={false}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
  </section>;
}
