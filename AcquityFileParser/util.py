from pydantic import BaseModel
from typing import Any


def cast_to_float(value: Any) -> float | None:
    try:
        return float(value)

    except Exception:

        return None


def cast_to_str(value: Any) -> str | None:
    try:
        return str(value)

    except Exception:

        return None


def cast_to_int(value: Any) -> int | None:
    try:
        return int(value)

    except Exception:

        return None


class ChromatogramMetadata(BaseModel):
    min_time: float = None
    max_time: float = None
    num_data_points: int = None
    detector: str = None
    generating_data_system: str = None
    exporting_data_system: str = None
    operator: str = None
    signal_quantity: str = None
    signal_unit: str = None
    signal_min: float = None
    signal_max: float = None
    channel: str = None
    driver_name: str = None
    channel_type: str = None
    min_step: float = None
    max_step: float = None
    avg_step: float = None


chromatogram_metadata_map = {
    "Time Min. (min)": ("min_time", cast_to_float),
    "Time Max. (min)": ("max_time", cast_to_float),
    "Data Points": ("num_data_points", cast_to_int),
    "Detector": ("detector", cast_to_str),
    "Generating Data System": ("generating_data_system", cast_to_str),
    "Exporting Data System": ("exporting_data_system", cast_to_str),
    "Operator": ("operator", cast_to_str),
    "Signal Quantity": ("signal_quantity", cast_to_str),
    "Signal Unit": ("signal_unit", cast_to_str),
    "Signal Min.": ("signal_min", cast_to_float),
    "Signal Max.": ("signal_max", cast_to_float),
    "Channel": ("channel", cast_to_str),
    "Driver Name": ("driver_name", cast_to_str),
    "Channel Type": ("channel_type", cast_to_str),
    "Min. Step (s)": ("min_step", cast_to_float),
    "Max. Step (s)": ("max_step", cast_to_float),
    "Average Step (s)": ("avg_step", cast_to_float),
}


class InjectionMetadata(BaseModel):
    data_vault: str = None
    injection: str = None
    injection_number: int = None
    position: str = None
    comment: str = None
    processing_method: str = None
    instrument_method: str = None
    injection_type: str = None
    injection_status: str = None
    injection_date: str = None
    injection_time: str = None
    injection_volume: float = None
    dilution_factor: float = None
    weight: float = None


injection_metadata_map = {
    "Data Vault": ("data_vault", cast_to_str),
    "Injection": ("injection", cast_to_str),
    "Injection Number": ("injection_number", cast_to_int),
    "Position": ("position", cast_to_str),
    "Comment": ("comment", cast_to_str),
    "Processing Method": ("processing_method", cast_to_str),
    "Instrument Method": ("instrument_method", cast_to_str),
    "Injection Type": ("injection_type", cast_to_str),
    "Status": ("injection_status", cast_to_str),
    "Injection Date": ("injection_date", cast_to_str),
    "Injection Time": ("injection_time", cast_to_str),
    "Injection Volume (µL)": ("injection_volume", cast_to_float),
    "Dilution Factor": ("dilution_factor", cast_to_float),
    "Weight": ("weight", cast_to_float),
}

signal_metadata_map = {"Signal Info": ("signal_info", cast_to_str)}


class SignalParameterMetadata(BaseModel):
    signal_info: str = None
