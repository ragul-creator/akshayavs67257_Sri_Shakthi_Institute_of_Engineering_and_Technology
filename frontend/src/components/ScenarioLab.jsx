import React,{useState} from "react";
import {
  ResponsiveContainer,LineChart,Line,XAxis,YAxis,Tooltip,CartesianGrid,ReferenceLine
} from "recharts";

export default function ScenarioLab({patientId,runScenario,busy}) {
  const [result,setResult]=useState(null);

  const execute=async name=>{
    const data=await runScenario(name);
    setResult(data);
  };

  return <section className="cardSection scenarioPanel">
    <div className="sectionHeader">
      <div>
        <h2>Trajectory scenarios</h2>
        <p>Generate hypothetical future observations, recompute causal features, and pass them through the same saved model.</p>
      </div>
    </div>

    <div className="scenarioToolbar">
      <button onClick={()=>execute("recovery")} disabled={busy||!patientId}>Recovery trajectory</button>
      <button onClick={()=>execute("sustained_activity")} disabled={busy||!patientId}>Sustained activity</button>
    </div>

    {!result&&<div className="emptyScenario">
      <strong>No scenario running</strong>
      <p>Choose one of the two implemented trajectories above. The patient replay state will not be modified.</p>
    </div>}

    {result&&<>
      <div className="scenarioSummary">
        <div><span>Current</span><b>{(result.baseline_probability*100).toFixed(1)}%</b></div>
        <div><span>At +60 min</span><b>{(result.end_probability*100).toFixed(1)}%</b></div>
        <div><span>Maximum</span><b>{(result.max_probability*100).toFixed(1)}%</b></div>
      </div>

      <div className="scenarioChart">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={result.trajectory} margin={{top:16,right:10,left:-10,bottom:0}}>
            <CartesianGrid vertical={false} stroke="#e8edf1"/>
            <XAxis dataKey="minute" tickFormatter={v=>"+"+v+"m"} axisLine={{stroke:"#d9e1e7"}} tickLine={false} tick={{fontSize:11,fill:"#7a8792"}}/>
            <YAxis domain={[0,1]} tickFormatter={v=>Math.round(v*100)+"%"} axisLine={false} tickLine={false} tick={{fontSize:11,fill:"#7a8792"}}/>
            <Tooltip formatter={v=>(v*100).toFixed(1)+"%"} labelFormatter={v=>"+"+v+" minutes"} contentStyle={{background:"#fff",border:"1px solid #dfe7ec",borderRadius:10}}/>
            <ReferenceLine y={result.baseline_probability} stroke="#95a3ad" strokeDasharray="5 5"/>
            <Line dataKey="event_probability" name="Model probability" stroke="#20b9a9" strokeWidth={2.4} dot={false} isAnimationActive={false}/>
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="scenarioAssumptions">
        <strong>{result.label}</strong>
        {result.assumptions.map(x=><p key={x}>{x}</p>)}
        <small>{result.warning}</small>
      </div>
    </>}
  </section>;
}
