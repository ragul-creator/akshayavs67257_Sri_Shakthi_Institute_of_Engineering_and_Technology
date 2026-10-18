import React,{useState} from "react";
import {ResponsiveContainer,LineChart,Line,XAxis,YAxis,Tooltip,CartesianGrid,ReferenceLine} from "recharts";

export default function ScenarioLab({patientId, runScenario, busy}) {
  const [result,setResult] = useState(null);

  const execute = async name => {
    const data = await runScenario(name);
    setResult(data);
  };

  return <section className="workPanel scenarioPanel">
    <div className="panelHeading">
      <div>
        <h2>Trajectory laboratory</h2>
        <p>Generate future observations under explicit assumptions, then run the same feature/model pipeline.</p>
      </div>
    </div>

    <div className="scenarioToolbar">
      <button onClick={()=>execute("recovery")} disabled={busy || !patientId}>Recovery trajectory</button>
      <button onClick={()=>execute("sustained_activity")} disabled={busy || !patientId}>Sustained activity</button>
    </div>

    {!result && <div className="emptyLab">Choose a trajectory to simulate the next 60 minutes.</div>}

    {result && <>
      <div className="scenarioSummary">
        <div><span>Current</span><b>{(result.baseline_probability*100).toFixed(1)}%</b></div>
        <div><span>At +60 min</span><b>{(result.end_probability*100).toFixed(1)}%</b></div>
        <div><span>Maximum</span><b>{(result.max_probability*100).toFixed(1)}%</b></div>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={result.trajectory} margin={{top:10,right:12,left:-20,bottom:0}}>
          <CartesianGrid vertical={false} stroke="#1f2b37"/>
          <XAxis dataKey="minute" tickFormatter={v=>"+"+v+"m"} stroke="#647281" tick={{fontSize:11}}/>
          <YAxis domain={[0,1]} tickFormatter={v=>Math.round(v*100)+"%"} stroke="#647281" tick={{fontSize:11}}/>
          <Tooltip formatter={v=>(v*100).toFixed(1)+"%"} labelFormatter={v=>"+"+v+" minutes"}/>
          <ReferenceLine y={result.baseline_probability} stroke="#66717c" strokeDasharray="4 4"/>
          <Line dataKey="event_probability" name="Model probability" stroke="#63b3ff" strokeWidth={2} dot={false} isAnimationActive={false}/>
        </LineChart>
      </ResponsiveContainer>
      <div className="assumptions">
        <strong>{result.label}</strong>
        {result.assumptions.map(x=><p key={x}>{x}</p>)}
        <small>{result.warning}</small>
      </div>
    </>}
  </section>;
}
