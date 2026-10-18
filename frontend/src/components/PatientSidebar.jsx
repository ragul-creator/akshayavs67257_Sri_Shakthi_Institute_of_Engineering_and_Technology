import React from "react";

export default function PatientSidebar({patients, patientId, onSelect, busy}) {
  return <aside className="patientPanel">
    <div className="brandLockup">
      <div className="brandMark">CT</div>
      <div><strong>CardioTwin</strong><span>Synthetic cardiovascular research</span></div>
    </div>

    <div className="patientPanelHeader">
      <div>
        <span className="eyebrow">SYNTHETIC COHORT</span>
        <h2>Patients</h2>
      </div>
      <span className="patientCount">{patients.length}</span>
    </div>

    <div className="patientList">
      {patients.map(patient => {
        const active = patient.patient_id === patientId;
        return <button
          key={patient.patient_id}
          className={"patientRow" + (active ? " active" : "")}
          onClick={() => onSelect(patient.patient_id)}
          disabled={busy}
        >
          <span className="patientAvatar">{patient.patient_id.replace("P","").slice(-2)}</span>
          <span className="patientIdentity">
            <strong>{patient.patient_id}</strong>
            <small>{patient.age} yrs · {patient.sex}</small>
          </span>
          <span className="rowChevron">›</span>
        </button>;
      })}
    </div>

    <div className="syntheticNotice">
      <strong>Synthetic research data</strong>
      <p>Not for diagnosis, triage, or treatment decisions.</p>
    </div>
  </aside>;
}
