#!/usr/bin/env python3
"""Unit-safe engineering calculations for the OAM evaluation dataset."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _number(inputs: dict[str, Any], key: str, default: float | None = None) -> float:
    value = inputs.get(key, default)
    if value is None:
        raise KeyError(f"Missing required input: {key}")
    return float(value)


def kmh_to_ms(speed_kmh: float) -> float:
    return speed_kmh / 3.6


def brake_energy_mj(mass_kg: float, speed_kmh: float = 100.0) -> float:
    speed_m_s = kmh_to_ms(speed_kmh)
    return 0.5 * mass_kg * speed_m_s * speed_m_s / 1_000_000.0


def added_drag_force_n(
    delta_cd: float,
    frontal_area_m2: float,
    speed_kmh: float = 100.0,
    rho: float = 1.225,
) -> float:
    speed_m_s = kmh_to_ms(speed_kmh)
    return 0.5 * rho * delta_cd * frontal_area_m2 * speed_m_s * speed_m_s


def road_load_power_kw(force_n: float, speed_kmh: float = 100.0) -> float:
    return force_n * kmh_to_ms(speed_kmh) / 1000.0


def gross_battery_energy_kwh(
    series_cells: float,
    parallel_cells: float,
    cell_nominal_voltage_v: float,
    cell_capacity_ah: float,
) -> float:
    return series_cells * parallel_cells * cell_nominal_voltage_v * cell_capacity_ah / 1000.0


def usable_capacity_kwh(capacity_kwh: float, usable_ratio: float) -> float:
    return capacity_kwh * usable_ratio


def range_at_unchanged_consumption_km(
    current_range_km: float,
    current_usable_kwh: float,
    new_usable_kwh: float,
) -> float:
    return current_range_km * new_usable_kwh / current_usable_kwh


def gcwr_reserve_kg(
    gcwr_kg: float,
    curb_mass_kg: float,
    max_payload_kg: float,
    braked_trailer_rating_kg: float,
) -> float:
    return gcwr_kg - curb_mass_kg - max_payload_kg - braked_trailer_rating_kg


def power_from_torque_rpm_kw(torque_nm: float, rpm: float) -> float:
    return torque_nm * rpm / 9549.0


def rpm_from_power_torque(peak_power_kw: float, peak_torque_nm: float) -> float:
    return peak_power_kw * 9549.0 / peak_torque_nm


def scale_by_percent(value: float, percent_change: float) -> float:
    return value * (1.0 + percent_change / 100.0)


def calculate(op: str, inputs: dict[str, Any]) -> dict[str, Any]:
    if op == "kmh_to_ms":
        speed_kmh = _number(inputs, "speed_kmh")
        return {"op": op, "speed_kmh": speed_kmh, "result": kmh_to_ms(speed_kmh), "unit": "m/s"}
    if op == "brake_energy_mj":
        mass_kg = _number(inputs, "mass_kg")
        speed_kmh = _number(inputs, "speed_kmh", 100.0)
        return {
            "op": op,
            "mass_kg": mass_kg,
            "speed_kmh": speed_kmh,
            "speed_m_s": kmh_to_ms(speed_kmh),
            "result": brake_energy_mj(mass_kg, speed_kmh),
            "unit": "MJ",
            "formula": "0.5 * mass_kg * (speed_kmh / 3.6)^2 / 1e6",
        }
    if op == "added_drag_force_n":
        delta_cd = _number(inputs, "delta_cd")
        area = _number(inputs, "frontal_area_m2")
        speed_kmh = _number(inputs, "speed_kmh", 100.0)
        rho = _number(inputs, "rho", 1.225)
        return {
            "op": op,
            "delta_cd": delta_cd,
            "frontal_area_m2": area,
            "rho": rho,
            "speed_kmh": speed_kmh,
            "speed_m_s": kmh_to_ms(speed_kmh),
            "result": added_drag_force_n(delta_cd, area, speed_kmh, rho),
            "unit": "N",
        }
    if op == "road_load_power_kw":
        force_n = _number(inputs, "force_n")
        speed_kmh = _number(inputs, "speed_kmh", 100.0)
        return {"op": op, "force_n": force_n, "speed_kmh": speed_kmh, "result": road_load_power_kw(force_n, speed_kmh), "unit": "kW"}
    if op == "gross_battery_energy_kwh":
        result = gross_battery_energy_kwh(
            _number(inputs, "series_cells"),
            _number(inputs, "parallel_cells"),
            _number(inputs, "cell_nominal_voltage_v"),
            _number(inputs, "cell_capacity_ah"),
        )
        return {"op": op, "result": result, "unit": "kWh"}
    if op == "usable_capacity_kwh":
        result = usable_capacity_kwh(_number(inputs, "capacity_kwh"), _number(inputs, "usable_ratio"))
        return {"op": op, "result": result, "unit": "kWh"}
    if op == "range_at_unchanged_consumption_km":
        result = range_at_unchanged_consumption_km(
            _number(inputs, "current_range_km"),
            _number(inputs, "current_usable_kwh"),
            _number(inputs, "new_usable_kwh"),
        )
        return {"op": op, "result": result, "unit": "km"}
    if op == "gcwr_reserve_kg":
        result = gcwr_reserve_kg(
            _number(inputs, "gcwr_kg"),
            _number(inputs, "curb_mass_kg"),
            _number(inputs, "max_payload_kg"),
            _number(inputs, "braked_trailer_rating_kg"),
        )
        return {"op": op, "result": result, "unit": "kg"}
    if op == "power_from_torque_rpm_kw":
        result = power_from_torque_rpm_kw(_number(inputs, "torque_nm"), _number(inputs, "rpm"))
        return {"op": op, "result": result, "unit": "kW"}
    if op == "rpm_from_power_torque":
        result = rpm_from_power_torque(_number(inputs, "peak_power_kw"), _number(inputs, "peak_torque_nm"))
        return {"op": op, "result": result, "unit": "rpm"}
    if op == "scale_by_percent":
        result = scale_by_percent(_number(inputs, "value"), _number(inputs, "percent_change"))
        return {"op": op, "result": result}
    raise ValueError(f"Unknown engineering math operation: {op}")


def parse_inputs(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = {}
        body = value.strip().strip("{}")
        if body:
            for item in body.split(","):
                key, raw = item.split(":", 1)
                key = key.strip().strip("\"'")
                raw = raw.strip().strip("\"'")
                try:
                    parsed[key] = float(raw)
                except ValueError:
                    parsed[key] = raw
    if not isinstance(parsed, dict):
        raise ValueError("--inputs must describe an object")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("op")
    parser.add_argument("--inputs", required=True, help="JSON object of operation inputs")
    parser.add_argument("--round", type=int, default=None)
    args = parser.parse_args()

    payload = calculate(args.op, parse_inputs(args.inputs))
    if args.round is not None and isinstance(payload.get("result"), (int, float)):
        payload["rounded"] = round(float(payload["result"]), args.round)
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

