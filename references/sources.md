# Sources and parameter provenance

The executable model uses sources to bound choices, not to imply that one
published project is representative of every data center or greenhouse. Values
marked “scenario assumption” in `data/source_data.csv` should be replaced by
site measurements during a feasibility study.

The `source_id` values in the parameter CSV map to the numbered entries below:
`NREL_ESIF_2014` → 3, `NREL_WASTE_HEAT_2022` → 2,
`LU_2024_HX` → 6, `NREL_5GDHC_2022` → 13,
`CORNELL_NRAES_003` → 7, `USDA_VIRTUAL_GROWER_2010` → 9,
`ALABAMA_EXTENSION_CROP_TEMPS` → 11, `NASA_AIR_PROPERTIES` → 12, and
`ENERGYPLUS_PSYCHROMETRICS` → 12. `ASSUMPTION` means the value is a declared
scenario choice rather than a measured fact.

## Data-center heat and temperature

1. U.S. Department of Energy, Federal Energy Management Program, [Best
   Practices Guide for Energy-Efficient Data Center Design (2024)](https://www.energy.gov/sites/default/files/2024-07/best-practice-guide-data-center-design.pdf).
   The heat-reuse chapter emphasizes that higher leaving air/water temperature
   improves reuse opportunities, recommends a nearby heat host, and distinguishes
   direct use from heat-pump-assisted reuse.
2. A. Lämml et al., National Renewable Energy Laboratory, [Valuation of Novel
   Waste Heat Sources (NREL/TP-5500-83352)](https://docs.nrel.gov/docs/fy22osti/83352.pdf).
   The report uses measured NREL data and gives representative water-cooled
   data-center supply temperature around 36.5 °C and air-cooled heat-exchanger
   temperature around 30.6 °C. Those values motivate the 25–55 °C scenario
   range; they are not a universal operating envelope.
3. NREL, [Managing Data Centers in Multi-Use Environments](https://betterbuildingssolutioncenter.energy.gov/sites/default/files/Thursday%20-%20Managing%20Data%20Centers%20in%20Multi-Use%20Environments.pdf).
   The NREL ESIF example reports warm-water cooling and a high fraction of IT heat
   entering the liquid loop. It is a demonstration, not a fleet average.
4. Yuan et al., [Data center waste heat recovery: a review](https://doi.org/10.1016/j.rser.2023.113777), *Renewable and Sustainable Energy Reviews* (2023).
   Review context for air- and liquid-cooling temperatures and reuse pathways.
5. Murphy et al., [Empirical data-center waste-heat characterization](https://doi.org/10.1016/j.enconman.2024.118322), *Energy Conversion and Management* (2024).
   An example of why real source temperature and heat-flow profiles matter.
6. Lu et al., [Heat exchanger performance for data-center heat reuse](https://doi.org/10.1016/j.apenergy.2023.122473), *Applied Energy* (2024).
   Case-study context for exchanger effectiveness ranges. The repository uses
   0.50–0.90 as an explicit screening range, not as a guaranteed value.

## Greenhouse heat loss

7. E. Bartok, [Energy Conservation for Commercial Greenhouses (NRAES-3)](https://ecommons.cornell.edu/bitstream/handle/1813/67126/NRAES-003.pdf?sequence=1), Cornell Cooperative Extension.
   Source for (Q=UA\Delta T), infiltration terms, covering U-values, air-change
   ranges, and envelope-area geometry. The guide notes that the sizing equation
   is a no-solar-gain calculation.
8. University of Georgia Cooperative Extension, [Greenhouses: Heating,
   Ventilation, and Cooling](https://fieldreport.caes.uga.edu/publications/B792/greenhouses-heating-ventilation-and-cooling/).
   Independent explanation of transmission, infiltration, structure condition,
   and wind effects.
9. USDA Agricultural Research Service, [Virtual Grower: Software to Calculate
   Heating Costs of Greenhouse Production](https://www.ars.usda.gov/ARSUserFiles/50820500/GPRG/2010PublicationsandSummaries/VirtualGrowerSoftware%5BArticle%5D.pdf).
   U-value and air-leakage examples plus the warning that feasibility estimates
   are not a substitute for an energy audit.
10. USDA ARS, [Virtual Grower 3 manual](https://www.ars.usda.gov/ARSUserFiles/50820500/software/309/Manual%20for%20Virtual%20Grower%203_0.pdf).
    Geometry, schedules, curtains, and model caveats.
11. Alabama Cooperative Extension, [temperature ranges for hydroponic greenhouse
    crops](https://www.aces.edu/blog/topics/crop-production/transplant-production-for-hydroponic-greenhouse-systems/).
    Crop-specific day/night ranges; supports treating 18 °C as a generic scenario,
    not a universal setpoint.
12. NASA Glenn, [air properties](https://www.grc.nasa.gov/WWW/K-12/BGP/airprop.html),
    and EnergyPlus, [psychrometric services](https://bigladdersoftware.com/epx/docs/25-1/module-developer/psychrometric-services.html).
    Reference context for air density and specific-heat dependence on state.

## Storage and heat-pump framing

13. NREL, [Valuation of Novel Waste Heat Sources](https://docs.nrel.gov/docs/fy22osti/83352.pdf),
    especially the low-temperature district-heating discussion. The COP in this
    repository is a transparent Carnot-fraction screen, not a manufacturer map.
14. Purdue Extension, [Heating and Cooling in Greenhouses](https://www.purdue.edu/hla/sites/cea/wp-content/uploads/sites/15/2021/01/Heating-and-Cooling-in-Greenhouses-1.pdf),
    for low-temperature bench/root-zone heating context. A root-zone loop should
    not be assumed to cover all greenhouse heat without a separate emitter study.

## Community and food access

15. USDA Economic Research Service, [Food Access Research Atlas](https://ers.usda.gov/data-products/food-access-research-atlas)
    and [documentation](https://ers.usda.gov/data-products/food-access-research-atlas/documentation).
    Access indicators involve proximity plus income/vehicle and transportation
    context, and do not measure every affordability or food-quality condition.
16. USDA ERS, [Food security measurement](https://ers.usda.gov/topics/food-nutrition-assistance/food-security-in-the-us/measurement).
    Food insecurity is an economic and social condition, not merely distance from
    a greenhouse.
17. USDA ERS, [Community Food Security Assessment Toolkit](https://ers.usda.gov/publications/43179).
    Separates availability, accessibility, affordability, household security,
    community resources, and community assessment.
18. Siegner, Sowerwine, and Acey, [A systematic review of urban agriculture and
    food security](https://www.mdpi.com/2071-1050/10/9/2988), *Sustainability* (2018).
    Useful caution that production potential is easier to report than actual
    access and distribution outcomes.
19. USDA NRCS, [Best Practices for the Sustainable Urban Farm](https://www.nrcs.usda.gov/sites/default/files/2025-01/Best-Practices-for-the-Sustainable-Urban-Farm.pdf).
    Practical constraints including land tenure, zoning, cost, distribution, and
    communication with growers and food-justice organizations.
