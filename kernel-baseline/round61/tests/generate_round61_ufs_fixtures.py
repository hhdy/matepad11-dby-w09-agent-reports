#!/usr/bin/env python3
"""Generate minimal DTS fixtures for ROUND61 Qualcomm UFS schema constraints."""
from __future__ import annotations

import argparse
from pathlib import Path

SM8250_NAMES = [
    "core_clk",
    "bus_aggr_clk",
    "iface_clk",
    "core_clk_unipro",
    "ref_clk",
    "tx_lane0_sync_clk",
    "rx_lane0_sync_clk",
    "rx_lane1_sync_clk",
]
SM8150_NAMES = SM8250_NAMES + ["ice_core_clk"]


def render(
    *,
    compatible: str = "qcom,sm8250-ufshc",
    clock_count: int = 8,
    domain_count: int = 1,
    vddp_supply: bool = True,
    vddp_load: int | None = 89900,
    vccq_supply: bool = True,
    vccq_load: int | None = 210000,
) -> str:
    names = SM8150_NAMES if compatible == "qcom,sm8150-ufshc" else SM8250_NAMES
    names = names[:clock_count]
    clocks = ", ".join(f"<&clk{i}>" for i in range(clock_count))
    clock_names = ", ".join(f'"{name}"' for name in names)
    domains = ", ".join(f"<&pd{i}>" for i in range(domain_count))
    if compatible == "qcom,sm8150-ufshc":
        regs = '<0x01d84000 0x2500>, <0x01d90000 0x8000>'
        reg_names = 'reg-names = "std", "ice";'
    else:
        regs = '<0x01d84000 0x2500>'
        reg_names = ""
    supplies = []
    if vddp_supply:
        supplies.append("qcom,vddp-ref-clk-supply = <&vddp_reg>;")
    if vddp_load is not None:
        supplies.append(f"qcom,vddp-ref-clk-max-microamp = <{vddp_load}>;")
    if vccq_supply:
        supplies.append("qcom,vccq-parent-supply = <&vccq_reg>;")
    if vccq_load is not None:
        supplies.append(f"qcom,vccq-parent-max-microamp = <{vccq_load}>;")
    return f"""/dts-v1/;

/ {{
    #address-cells = <1>;
    #size-cells = <1>;

    intc: interrupt-controller {{
        interrupt-controller;
        #interrupt-cells = <3>;
    }};
{''.join(f'    clk{i}: clock-controller-{i} {{ #clock-cells = <0>; }};\\n' for i in range(9))}
{''.join(f'    pd{i}: power-domain-{i} {{ #power-domain-cells = <0>; }};\\n' for i in range(3))}
    vddp_reg: vddp-regulator {{ }};
    vccq_reg: vccq-regulator {{ }};

    ufs@1d84000 {{
        compatible = "{compatible}", "qcom,ufshc", "jedec,ufs-2.0";
        reg = {regs};
        {reg_names}
        interrupt-parent = <&intc>;
        interrupts = <0 1 4>;
        clocks = {clocks};
        clock-names = {clock_names};
        power-domains = {domains};
{''.join(f'        {line}\\n' for line in supplies)}
    }};
}};
"""


CASES = {
    "ufs-sm8250-1-domain-valid": (dict(domain_count=1), True, None),
    "ufs-sm8250-2-domains-valid": (dict(domain_count=2), True, None),
    "ufs-sm8250-7-clock-names-invalid": (dict(clock_count=7), False, "clock-names"),
    "ufs-sm8250-9-clock-names-invalid": (dict(clock_count=9), False, "clock-names"),
    "ufs-sm8250-3-domains-invalid": (dict(domain_count=3), False, "power-domains"),
    "ufs-sm8150-2-domains-invalid": (
        dict(compatible="qcom,sm8150-ufshc", clock_count=9, domain_count=2),
        False,
        "power-domains",
    ),
    "ufs-sm8250-vddp-missing-load-invalid": (
        dict(vddp_supply=True, vddp_load=None),
        False,
        "qcom,vddp-ref-clk-max-microamp",
    ),
    "ufs-sm8250-vccq-parent-missing-load-invalid": (
        dict(vccq_supply=True, vccq_load=None),
        False,
        "qcom,vccq-parent-max-microamp",
    ),
    "ufs-sm8250-vddp-zero-load-invalid": (
        dict(vddp_supply=True, vddp_load=0),
        False,
        "qcom,vddp-ref-clk-max-microamp",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name, (kwargs, _, _) in CASES.items():
        (args.out / f"{name}.dts").write_text(render(**kwargs), encoding="utf-8")
    print(f"Generated {len(CASES)} Qualcomm UFS DTS fixtures in {args.out}")
    for name, (_, should_pass, expected_error) in CASES.items():
        print(f"{name}: {'PASS' if should_pass else 'EXPECTED-FAIL'}"
              + (f" ({expected_error})" if expected_error else ""))


if __name__ == "__main__":
    main()
