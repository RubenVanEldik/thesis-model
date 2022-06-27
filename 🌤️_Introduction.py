import streamlit as st


st.image("./images/logo.png")

st.markdown(
    """
    ## Welcome!

    This is an optimization model for a fully intermittent renewable Pan-European electricity grid. The model aims to find the least-cost solution for the deployment of solar PV, wind energy and storage. By overbuilding generation capacity to some degree, significant less storage capacity is required, resulting in lower system costs.

    The demand and climate data used in this model are from ENTSO-E's 2021 European Resource Adequacy Assessment (ERAA) and can be downloaded [here](https://www.entsoe.eu/outlooks/eraa/2021/eraa-downloads/). The techno-economic data is from NREL's Annual Technology Baseline and can be found [here](https://atb.nrel.gov/).

    The source code of the model can be found on [Github](https://github.com/RubenVanEldik/thesis-model). It consists out of three parts, the preprocessing, optimization, and analysis.

    ### Preprocessing
    The preprocessor only needs to be run once. It will convert all the hourly ERAA data into a format that can be parsed more easily by the optimization.

    ### Optimization
    ...

    ### Analysis
    ...
"""
)


st.markdown(
    """
<style>
    .element-container button + div {
        justify-content: center;
        margin-bottom: 1rem;
    }

    .element-container img {
        width: 22rem;

    }
	.stMarkdown{
		text-align: center;
	}

    .stMarkdown h3 {
        margin-top: 1.5rem;
    }

    .stMarkdown p {
        width: 90%;
        margin-left: auto;
        margin-right: auto;
        font-size: 1.1rem;
    }
</style>
""",
    unsafe_allow_html=True,
)
