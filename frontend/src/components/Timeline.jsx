import React from "react";
import {
  ResponsiveContainer,LineChart,Line,CartesianGrid,XAxis,YAxis,Tooltip,Legend,ReferenceLine
} from "recharts";

const tickTime=value=>{
  const date=new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
};

export default function Timeline({observations,baselineHr,baselineSbp}) {
  const now=observations?.length ? observations[observations.length-1].timestamp : null;
  return <section className="cardSection timelinePanel">
    <div className="sectionHeader">
      <div><h2>Physiology timeline</h2><p>Recent observations available to the twin at the current replay time.</p></div>
      <span className="sectionMeta">5-minute cadence</span>
    </div>
    <div className="chartFrame">
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={observations} margin={{top:18,right:10,left:-10,bottom:2}}>
          <CartesianGrid stroke="#e8edf1" vertical={false}/>
          <XAxis dataKey="timestamp" tickFormatter={tickTime} minTickGap={44} axisLine={{stroke:"#d9e1e7"}} tickLine={false} tick={{fontSize:11,fill:"#7a8792"}}/>
          <YAxis yAxisId="hr" domain={["dataMin - 8","dataMax + 8"]} axisLine={false} tickLine={false} tick={{fontSize:11,fill:"#7a8792"}}/>
          <YAxis yAxisId="bp" orientation="right" domain={["dataMin - 10","dataMax + 10"]} axisLine={false} tickLine={false} tick={{fontSize:11,fill:"#7a8792"}}/>
          <Tooltip labelFormatter={tickTime} contentStyle={{background:"#fff",border:"1px solid #dfe7ec",borderRadius:10,boxShadow:"0 8px 24px rgba(41,55,70,.08)"}}/>
          <Legend wrapperStyle={{fontSize:11,color:"#667581",paddingTop:8}}/>
          {Number.isFinite(Number(baselineHr)) && <ReferenceLine yAxisId="hr" y={Number(baselineHr)} stroke="#37bfae" strokeDasharray="5 5" opacity={.65}/>}
          {Number.isFinite(Number(baselineSbp)) && <ReferenceLine yAxisId="bp" y={Number(baselineSbp)} stroke="#5b8def" strokeDasharray="5 5" opacity={.55}/>}
          {now && <ReferenceLine x={now} stroke="#1bb9a7" strokeDasharray="4 4" label={{value:"Now",position:"top",fill:"#159989",fontSize:10}}/>}
          <Line yAxisId="hr" type="monotone" dataKey="heart_rate_bpm" name="Heart rate" stroke="#27c3b2" strokeWidth={2.2} dot={false} isAnimationActive={false}/>
          <Line yAxisId="bp" type="monotone" dataKey="systolic_bp" name="Systolic BP" stroke="#5b8def" strokeWidth={2} dot={false} isAnimationActive={false}/>
        </LineChart>
      </ResponsiveContainer>
    </div>
  </section>;
}
