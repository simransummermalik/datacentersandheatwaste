# Poster layout for the Charlotte winter result

The present poster explains the idea several times before showing a result.
Use the hourly winter analysis as the center of the story. The new assets below
are plain Times New Roman PNGs and editable-text SVGs in `charts/`.

## Remove from the current version

- The **Sense → Decide → Act** boxes. They describe a possible control system,
  but this study did not test one.
- The cartoon **Heat Path** drawing. Its numerical path is already in the
  method; the icons and arrows take the space needed for a real result.
- The **11-row math table**. Keep one equation on the poster and let the QR
  code lead to the complete model.
- The current **3.6 ha** callout as a main result. It is a separate 0 °C
  design-point capacity estimate; the hourly winter study fixes **2.7 ha**.
  Mixing the two without labels makes the comparison look inconsistent.
- The **synthetic 24-hour heat balance** and its paragraph. The new plot uses
  measured hourly IT power and observed Charlotte weather.
- The **415 versus 945 TWh** chart if space is tight. It gives global context,
  while the poster's contribution is a Charlotte reliability screen.

## Place the new material

| Position on current poster | Heading | Content |
|---|---|---|
| Title bar | **Can Data-Center Waste Heat Heat a Greenhouse?** | Subtitle: “An hourly Charlotte winter screen using a measured compute-load proxy.” Keep your name, affiliation, logo, and QR code. |
| Left column, top | **Question and case** | Use the short case text below. |
| Left column, bottom | **Method** | Use the three-line method text and one metric equation below. |
| Center + right, upper half | **The 66-hour shortfall** | Insert [`poster_low_load_event.png`](../charts/poster_low_load_event.png) across both columns. Put the one-sentence caption directly below it. |
| Center, lower half | **Winter reliability** | Insert [`poster_reliability_table.png`](../charts/poster_reliability_table.png). |
| Right, lower half | **Heating energy cost** | Insert [`poster_cost_sidebar.png`](../charts/poster_cost_sidebar.png). |
| Full-width bottom strip | **Finding and limits** | Use the finding and limitations text below; add source line. |

If the event plot cannot span two columns, put it in the whole center column
and move the cost sidebar below the right-column introduction. Keep the event
plot larger than every other figure.

## Paste-ready text

**Question and case**

> Can recovered data-center heat meet the hourly winter demand of a 2.7 ha
> greenhouse in Charlotte? The greenhouse is held at 18 °C. The hypothetical
> source is a 10 MW IT facility averaging 8 MW, with 10.5 MWh of thermal storage.

**Method**

> I paired 2,160 hours of NOAA Charlotte temperature with a measured Colorado
> HPC IT-power profile, scaled to 8 MW average load. Each hour, the model
> calculates greenhouse heat loss, recoverable heat, storage dispatch, and any
> remaining backup heat. The Colorado profile is a temporal proxy, not a
> measured Charlotte AI workload.

> Heating-hour coverage = hours with demand and no backup ÷ hours with demand.

**Caption below the event plot**

> One 66-hour dip in the measured compute-load profile caused 125 MWh of backup
> heat—97.9% of this modeled winter's backup energy. The 10.5 MWh tank helped
> with short gaps but could not bridge a multi-day shortfall.

**Finding and limits strip**

> **96.5%** of heating hours were covered without backup; **128 MWh** still
> required backup over the 90-day winter. Eliminating backup with storage alone
> in this exact scenario would require about **149 MWh** of usable capacity.
> These are screening results for one winter and a cross-site load proxy.

**Source line, in small type**

> NOAA Global Hourly, Charlotte Douglas 72314013881 (2024–25); NLR ESIF HPC
> IT-power data (Colorado, DOI 10.7799/3015212); EIA 2025 North Carolina
> commercial electricity and gas averages. Model, assumptions, and hourly
> results: QR code.

## Visual treatment

Use a white body background, dark text, and one dark-green accent for headings.
Keep all content aligned to the same column edges. Use Times New Roman
throughout, with a larger title and a limited number of text sizes. The new
panels have no gradients, cartoon icons, decorative arrows, or colored cards.
The cost panel is an energy-only reference comparison; no actual greenhouse
heater, tariff, heat purchase price, or project capital cost was supplied.
