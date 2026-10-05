# Assumptions and equations

Every value used by the executable scenarios appears in
[`data/source_data.csv`](../data/source_data.csv). A row is either tied to a
source in [`references/sources.md`](../references/sources.md) or explicitly
marked as a scenario assumption. Ranges are screening ranges, not confidence
intervals.

## Data-center heat balance

For an IT nameplate $P_{IT}$, instantaneous load fraction $f_L$, and heat
conversion fraction $f_H$:

$$
Q_{generated}=P_{IT}f_Lf_H
$$

The recovery loop is modeled in two distinct steps:

$$
Q_{source}=Q_{generated}f_{collect}
$$

$$
Q_{HX}=Q_{source}\epsilon_{HX}
$$

`collection_fraction` means the fraction of server heat entering the selected
recovery loop. `heat_exchanger_effectiveness` means the fraction transferred to
the secondary loop. They are not two different published versions of an overall
recovery rate.

Direct exchange is allowed when:

$$
T_{source,out} \ge T_{greenhouse,supply}+\Delta T_{approach}
$$

Otherwise the model sends $Q_{HX}$ through a screening heat pump. It estimates
COP from a fraction of the Carnot heating limit:

$$
COP=clip\left(\eta_C\frac{T_{cond,K}}{T_{cond,K}-T_{evap,K}},COP_{min},COP_{max}\right)
$$

where $T_{evap}=T_{source,out}-\Delta T_{source}$ and
$T_{cond}=T_{greenhouse,supply}+\Delta T_{sink}$. The heat pump’s electrical
input is retained in the output rather than hidden:

$$
W_{HP}=Q_{HX}/(COP-1), \qquad Q_{cond}=Q_{HX}+W_{HP}
$$

Finally, the modeled greenhouse delivery is

$$
Q_{delivered}=Q_{cond}(1-L_{distribution})
$$

for either direct exchange ($Q_{cond}=Q_{HX}$) or the heat-pump pathway.

## Greenhouse load

For floor area $A_f$, envelope-to-floor ratio $r_A$, overall envelope
U-value $U$, mean height $h$, air changes per hour $ACH$, air density
$\rho$, and specific heat $c_p$:

$$
q''_f=\left(Ur_A+\frac{\rho c_p ACH h}{3600}\right)
\max(T_{set}-T_{out},0)(1+m)
$$

The modeled peak area is $A_{supported}=Q_{delivered}/q''_f$, with units
converted from kW to W. This is a steady-state sensible-load screen. Solar gain,
lighting/equipment gain, crop latent load, ground/perimeter loss, wind-driven
leakage, thermal screens, and deliberate ventilation are not represented. The
omissions are documented in [`docs/limitations.md`](limitations.md) rather than
presented as measurements.

## Storage

The mismatch notebook uses an ideal cyclic storage calculation to find the
largest cumulative deficit in a repeating hourly profile. It then simulates a
water tank with 98% charge/discharge efficiency and 0.1% per-hour standing loss.
Tank volume is only a sensible-heat conversion:

$$
V=\frac{E_{kWh}\,3600}{\rho_w c_{p,w}\Delta T_{tank}}
$$

It is not a design for stratification, pressure, freeze protection, pumps,
controls, or structural loads.
