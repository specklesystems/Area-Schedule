"""Run integration tests with a speckle server."""

from pydantic import SecretStr

from speckle_automate import (
    AutomationContext,
    AutomationRunData,
    AutomationStatus,
    run_function
)

from main import FunctionInputs, automate_function

from speckle_automate.fixtures import *


def test_function_run(test_automation_run_data: AutomationRunData, test_automation_token: str):
    """Run an integration test for the automate function."""
    automation_context = AutomationContext.initialize(
        test_automation_run_data, test_automation_token
    )
    automate_sdk = run_function(
        automation_context,
        automate_function,
        FunctionInputs(
            file_name="TestNameABC",
            inlcude_areas= True,
            inlcude_rooms= True,
            nua_list = "Elevator E1, Level 5 Gross, Live/Work Unit, Machine RM",
            nia_list = "",
            nla_list = "Café, Café Kitchen, Corridor, Common, Elevator E1, Level 5 Gross, Live/Work Unit, Machine RM",
            gia_list = "Café, Café Kitchen, Mezzanine Dining, Common, Elevator E1, Level 5 Gross, Live/Work Unit",
            gea_list = "Café, Café Kitchen, Common, Elevator E1, Level 5 Gross, Live/Work Unit, Corridor, Commercial/Retail",
            gla_list = "Residential Lobby, Live/Work Unit, Pocket Park, Outdoor Covered Dining, Elevator",
            gba_list = "Elevator E2, Café, Café Kitchen, Common, Elevator E1, Level 5 Gross, Live/Work Unit, Outdoor Covered Dining, Elevator"
        ),
    )

    assert automate_sdk.run_status == AutomationStatus.SUCCEEDED
