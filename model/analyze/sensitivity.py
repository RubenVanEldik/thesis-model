import pandas as pd
import streamlit as st

import lcoe
import utils
import validate


def sensitivity(run_name):
    """
    Analyze the sensitivity
    """
    assert validate.is_string(run_name)

    st.title("Sensitivity analysis")

    sensitivity_config = utils.read_yaml(f"../output/{run_name}/sensitivity.yaml")
    output_variable_options = ["LCOE"]
    output_variables = st.multiselect("Output variable", output_variable_options)
    if output_variables:
        sensitivity_steps = sensitivity_config["steps"]
        output_values = pd.DataFrame(index=sensitivity_steps.values(), columns=output_variable_options)

        # Loop over each step in the sensitivity analysis
        for step_key, step_value in sensitivity_steps.items():
            production_capacity = utils.get_production_capacity(f"{run_name}/{step_key}")
            storage_capacity = utils.get_storage_capacity(f"{run_name}/{step_key}")
            hourly_results = utils.get_hourly_results(f"{run_name}/{step_key}")
            config = utils.read_yaml(f"../output/{run_name}/{step_key}/config.yaml")

            hourly_demand = utils.merge_dataframes_on_column(hourly_results, "demand_MWh")
            firm_lcoe = lcoe.calculate(production_capacity, storage_capacity, hourly_demand, technologies=config["technologies"])
            output_values.loc[step_value, "LCOE"] = firm_lcoe

        # Show a line chart with the selected output variables
        st.line_chart(output_values[output_variables])
