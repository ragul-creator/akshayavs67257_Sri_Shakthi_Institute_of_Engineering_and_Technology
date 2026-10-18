from copy import deepcopy

SCENARIO_NAMES=("return_toward_baseline","increased_activity")

def apply_scenario(source_row, name: str):
    row=deepcopy(source_row)
    assumptions=[]
    if name=="return_toward_baseline":
        row["heart_rate_bpm"]=row["baseline_hr"]+(row["heart_rate_bpm"]-row["baseline_hr"])*.35
        row["hr_deviation"]=row["heart_rate_bpm"]-row["baseline_hr"]
        row["hr_relative"]=row["heart_rate_bpm"]/row["baseline_hr"]
        row["hr_mean_60"]=row["baseline_hr"]+(row["hr_mean_60"]-row["baseline_hr"])*.5
        row["systolic_bp"]=row["historical_systolic_bp"]+(row["systolic_bp"]-row["historical_systolic_bp"])*.4
        row["sys_deviation"]=row["systolic_bp"]-row["historical_systolic_bp"]
        row["sys_mean_60"]=row["historical_systolic_bp"]+(row["sys_mean_60"]-row["historical_systolic_bp"])*.5
        assumptions=["Hypothetical HR trajectory moves 65% toward baseline.",
                     "Hypothetical systolic BP trajectory moves 60% toward baseline."]
    elif name=="increased_activity":
        row["heart_rate_bpm"]+=10
        row["hr_deviation"]+=10
        row["hr_relative"]=row["heart_rate_bpm"]/row["baseline_hr"]
        row["hr_mean_60"]+=5
        row["steps"]+=60
        row["activity_code"]=2
        assumptions=["Hypothetical activity state set to active.",
                     "Heart rate increased by 10 bpm for simulation only."]
    else:
        raise ValueError("unknown scenario")
    return row,assumptions
