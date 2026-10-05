# Where this model can fail

The results are useful for asking which assumptions deserve measurement. They
are not a construction specification or an estimate of annual crop output.

## Engineering limits

- The IT-to-heat fraction is an energy-boundary approximation. Facility power,
  cooling electricity, fan power, and heat rejected outside the selected loop
  are not a measured PUE/ERE calculation.
- Collection fraction, exchanger effectiveness, distribution loss, heat-pump
  efficiency, and temperatures are scenario inputs. A real project needs
  coolant flow and supply/return measurements, exchanger pinch temperatures,
  controls data, and a manufacturer performance map.
- A low-temperature source may technically supply a heat pump while still being
  economically or electrically unattractive. This repository does not price
  electricity, carbon, backup cooling, water, piping, land, or maintenance.
- The heat pump is allowed to add compressor electricity to the condenser heat.
  That output is not “free recovered heat”; compare it with the explicit
  electrical-input column.
- The greenhouse equation omits solar, crop latent load, ground/perimeter loss,
  thermal bridges, screens, and wind-driven infiltration. Some omissions lower
  load while others raise it, so the net bias is not guaranteed.
- A single peak-design point must not be multiplied by 8,760 hours. An annual
  study needs hourly weather, crop schedules, sun, ventilation, and equipment
  availability.
- The storage example starts with a full idealized tank and uses a synthetic
  24-hour profile. It demonstrates time mismatch, not a seasonal-storage claim.

## Conditions that make the idea stop making sense

The concept is a poor fit when the source stream is too cool for direct use and
the heat pump’s electricity is unavailable or costly; when the greenhouse is
far enough away that pipe losses and capital dominate; when the data center
cannot guarantee heat availability while the greenhouse needs backup; when the
cooling system must reject heat independently for reliability; or when a site
has no practical water, land, permitting, ownership, or distribution path. A
large nameplate IT load does not remove these constraints.

## Community limits

The model does not identify a “food desert,” count residents, infer demand, or
claim that a greenhouse fixes food insecurity. USDA access indicators themselves
do not capture all affordability, quality, availability, transportation, and
household-resource questions. A real siting study would involve residents,
growers, food organizations, land owners, and local governments before treating
thermal capacity as a community benefit.

