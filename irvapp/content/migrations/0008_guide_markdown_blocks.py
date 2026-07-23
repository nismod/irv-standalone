from django.db import migrations


GUIDE_PAGE_NAME = "guide"
GUIDE_BLOCKS = [
    {
        "title": "Guide page content",
        "slot": "content",
        "markdown": """# User Guide for the Jamaica Systemic Risk Assessment Tool (J-SRAT)

[Download website user guide (this page) [PDF]](/guide_media/J-SRAT User Guide_2022-05.pdf)

[View video playlist introducing the J-SRAT [YouTube]](https://www.youtube.com/playlist?list=PL_Yf06STgGGtRfbvT1HRZk34Ay8n9oUV2)

[Download technical report detailing analysis methodology [PDF]](/publications/ECI_Jamaica_methodology_technical_report_vFinal.pdf)

## Table of Contents

[How to use this guide](#how-to-use-this-guide)

[Navigate around the J-SRAT](#navigate-around-the-j-srat)

[Explore the J-SRAT data and analysis](#explore-the-j-srat-data-and-analysis)

- [How are the transport, energy and water systems represented?](#how-are-the-transport-energy-and-water-systems-represented)
- [How are flooding and hurricanes represented?](#how-are-flooding-and-hurricanes-represented)
- [How are people and economic activities represented?](#how-are-people-and-economic-activities-represented)
- [How is climate risk from flooding or cyclones represented?](#how-is-climate-risk-from-flooding-or-cyclones-represented)
- [How is drought risk represented?](#how-is-drought-risk-represented)
- [How are adaptation options presented?](#how-are-adaptation-options-presented)
- [How are nature-based solutions represented?](#how-are-nature-based-solutions-represented)

[Trace the climate risk and adaptation analysis for a single asset](#trace-the-climate-risk-and-adaptation-analysis-for-a-single-asset)

[Prioritise and evaluate adaptation interventions](#prioritise-and-evaluate-adaptation-interventions)

[About this guide](#about-this-guide)

## How to use this guide

[Back to top](#table-of-contents)

This guide is intended to accompany the interactive web-based platform, which is part of the Jamaica Systemic Risk Assessment Tool (J-SRAT), and visualises the results of a climate risk and adaptation analysis of Jamaica's infrastructure.

The overall objectives of the J-SRAT are to:

1. Present the results of a climate risk analysis for Jamaica's infrastructure networks (transport, energy, water) to estimate the economic impacts of physical climate risks and identify locations of vulnerability within infrastructure networks.
2. Enable evaluation and prioritization of policies and investment options to reduce losses and enhance infrastructure resilience.

This guide aims to convey an initial understanding of the tool's content and capabilities. First, we introduce how to navigate around the tool. Then we introduce each of the major data and results layers. Finally, we work through two more analytical use cases: stepping through the climate risk and adaptation analysis for a single asset, then prioritising adaptation interventions based on cost-benefit analysis and digging into the details to evaluate a particular intervention.

For analysts, a detailed technical methodology report on the analysis is also available: Pant, R., Becher, O., Haggis R., Majid, A., Russell, T., Verschuur, J., and Hall, J.W. (2022). Final technical report on methodology and implementation of the Jamaica Systemic Risk Assessment Tool (J-SRAT). Environmental Change Institute, University of Oxford, UK.

For developers, the source code for the tool is developed and documented at [github.com/nismod/irv-jamaica](https://github.com/nismod/irv-jamaica). The analysis for Jamaica is produced using the code and models at [github.com/nismod/jamaica-infrastructure](https://github.com/nismod/jamaica-infrastructure).

## Navigate around the J-SRAT

[Back to top](#table-of-contents)

The top level of navigation for the tool is in the black top bar.

"J-SRAT" brings you to the home page, which gives a brief introduction and summary of the analysis.

Click across the links in the top navigation bar to see the "Exposure", "Risk" and "Adaptation" stages of the flooding, cyclone and drought infrastructure risk assessment and adaptation analysis.

"Nature-based Solutions" includes information about land-use and nature-based solutions.

"Data" includes a summary of data used in the tool.

![Jamaica Systemic Risk Assessment Tool (J-SRAT) homepage.](/guide_media/image2.png)

Click on "Exposure" to show the map view. The main controls on this screen are used throughout.

The left sidebar has various sections which control the data that is shown on the map.

![Map of Jamaica showing point locations of substations.](/guide_media/image3.png)

Click the search icon which is just to the right of the sidebar sections to search for places. This uses the OpenStreetMap Nominatim service and should find parishes, towns, some roads and some addresses by name. For example, search for "Norman Manley International".

![Search box showing 'Norman Manley International'.](/guide_media/image4.png)

Click the first result to zoom to the airport.

![Map zoomed to Norman Manley International Airport.](/guide_media/image5.png)

Below the search box, there is a map layer control. Hover over the layers icon to show it.

Switch the map background from the light grey "Map" background (designed by CARTO using OpenStreetMap data) to the "Satellite" imagery background (produced by EOX from Copernicus Sentinel-2 data).

Check or uncheck the box to hide or "Show labels".

![Satellite image map of Kingston Harbour.](/guide_media/image6.png)

In the top-right corner of the map, the plus and minus buttons control the map zoom. You can also scroll to zoom or double-click to zoom in and hold the shift key and double-click to zoom out.

In the bottom-right corner of the map, there is a scale bar for reference and an "i" icon which shows or hides information about the background maps when clicked.

## Explore the J-SRAT data and analysis

[Back to top](#table-of-contents)

## How are the transport, energy and water systems represented?

The "Exposure", "Risk", "Adaptation" and "Nature-based Solutions" tabs follow a consistent layout. The left sidebar controls the data that is shown on the map.

Start on the "Exposure" tab.

Click on the "Infrastructure" section to expand or collapse it.

Use the "eye" icons to hide or show all of a section's layers at once.

Under "Infrastructure", expand "Power" and "Transmission" and select "High Voltage" lines. Explore the other power system layers to see the elements of the network as they are included in the analysis.

![Map of Jamaica showing High Voltage power lines.](/guide_media/image7.png)

Use the top "Power" checkbox to deselect all power assets, and expand "Transport" to bring in roads layers.

![Map of Jamaica showing Class A and B roads.](/guide_media/image8.png)

Similarly, under "Water", bring in the water supply, irrigation and wastewater systems.

![Map of Jamaica showing water and wastewater pipelines and irrigation canals.](/guide_media/image9.png)

## How are flooding and hurricanes represented?

Open the "Hazards" section and select "River Flooding" to show potential flooding on the map. This is a return period map, showing the depth of flooding in any location across the island which is expected to be exceeded once in some number of years (once in 20 years, for example). Hover over shaded blue areas to see the depth of flooding in metres.

![Map of a flooded area, highlighting an exposed electricity substation.](/guide_media/image10.png)

In the sidebar, move the slider to show flooding for different return periods. A 500-year return period flood is much less likely and more intense, with deeper water levels and more area covered by the flood.

![Map of a flooded area, highlighting an exposed electricity substation under a more severe flood.](/guide_media/image11.png)

While looking at the hazards, we can overlay infrastructure networks to see where they might be affected.

![Map of Jamaica, showing roads exposed to 100-year return period river flooding.](/guide_media/image12.png)

Click on a road, for example, to see details of the asset damage calculated from the length of road exposed to different depths of flooding at each return period.

![Highlighted map of a road section, showing a chart and table of return period damages and indirect losses.](/guide_media/image13.png)

## How are people and economic activities represented?

Population is mapped to administrative boundaries, and economic activity is assigned to buildings.

In the left sidebar, open the "Regions" tab to hide or show boundaries. "Parishes" shows the top-level regions.

![Map of Jamaica with parish boundaries, focussing St Andrew Parish.](/guide_media/image14.png)

Select "Enumeration Districts" to see the small areas.

![Map of Jamaica with Enumeration District boundaries, focussing on ER88.](/guide_media/image15.png)

Change the "Layer Style" to "Population" to show population density on the map. Hover over areas to see population counts, and click on an area for a small detail sidebar to appear on the right of the screen.

![Map of Jamaica showing population density per Enumeration District, with a concentration of high density around Kingston and other towns.](/guide_media/image16.png)

Expand the "Buildings" section in the left sidebar and check that the eye icon is toggled on, then zoom in to see buildings. The buildings are not shown at all until quite high zoom levels.

![Zoomed in map showing individual building footprints, coloured by general use (commercial, residential, etc.).](/guide_media/image17.png)

Click on a building to see details, including the total assigned GDP and estimated rehabilitation cost. Risk and direct damages from flooding and cyclones have been assessed for buildings as for infrastructure assets, though no indirect effects are estimated beyond the disruption to the activity in the building itself.

![Focus on expected cyclone-related damages to an individual building](/guide_media/image18.png)

Toggle the "Hazards" section visibility to show flood maps under buildings.

![Zoomed in map showing buildings exposed to river flooding, with a focus on damages and losses arising from a specific commercial building.](/guide_media/image19.png)

## How is climate risk from flooding or cyclones represented?

On the "Risk" page, in the "Infrastructure" sidebar section, the "Layer style" defaults to show damages. Select the "Power", "Transmission", "Substations" layer to show expected direct damages or economic losses as evaluated for all of the substations across the island.

![Map of Jamaica showing electricity substations, coloured by all-hazard economic losses arising from failures.](/guide_media/image20.png)

From the controls in the sidebar, explore the contribution of individual hazards, and select the epoch (year) and RCP (climate scenario) to see how risks change as the hazards change. At this point in the analysis there is no accounting for economic growth or discounting over time: the comparison is holding everything constant except for the hazard maps.

## How is drought risk represented?

On the "Adaptation" page, the second sidebar section contains controls to show drought risk and drought-related adaptation options. Select for example "Population at risk" to see areas coloured by risk and "Population protected" to see points representing approximate locations of options to reduce the impacts of drought.

![Map of Parishes of Jamaica showing expected population disrupted by drought, and potential adaptation options.](/guide_media/image21.png)

## How are adaptation options presented?

On the "Adaptation" page, the left sidebar includes an "Adaption Options" layer style. Select a sector, sub sector and asset type to display the generic adaptation options that have been evaluated. For example, for "Transport", "Road", "Class A", you can look at "Elevate the roads" or a combined upgrade option.

![Table of adaptation prioritisation for all Class A roads, ordered by Cost-Benefit Ratio.](/guide_media/image22.png)

From here, the assets are shown on the map and ranked in the table on the right, according to the choice of "Displayed variable", which includes net present value of avoided direct damages or economic losses, total adaptation cost, or the cost-benefit ratio.

Hover over the rows of the table on the right to highlight asset locations. Click the magnifying glass icon to zoom in. Click the "zoom out" magnifying glass icon at the top of the table to get back to the full island view. Click on a row of the table to see the main asset attributes.

Once you have identified an asset of interest, click on it on the map to highlight it in blue, then switch the layer style to "Damages" or switch the page to "Risk" to show the full asset details sidebar. Scroll down for the full details on Adaptation Options for this particular asset.

![Table of adaptation options, costs and benefits calculated for a specific stretch of road, showing a map of the road and coastal flood hazard.](/guide_media/image23.png)

## How are nature-based solutions represented?

The "Nature-based solutions" tab enables analysis and exploration of various aspects of the land and sea.

Expand the "Terrestrial" section to show a long list of Land Use/Land Cover classes.

![Map of land-use/land-cover, filtered to highlight certain areas according to user-selected criteria.](/guide_media/image24.png)

Change the maximum or minimum values for elevation or slope to constrain the areas displayed - for example, look for high-slope areas with land cover that could be improved for slope stability and runoff reduction.

Apply various other constraints to see areas which are protected, or within 100m of a stream or forest.

Expand the "Marine" section to show coral, mangrove and seagrass, with 500m buffer zones around each habitat area.

![Map of marine habitats (coral, seagrass and mangroves) showing overlap and areas in proximity to existing habitats.](/guide_media/image25.png)

## Trace the climate risk and adaptation analysis for a single asset

[Back to top](#table-of-contents)

This use case revisits many of the previous stages, looking at a single infrastructure asset to understand the process of climate risk and adaptation analysis. It assumes that there is a particular asset that you are interested in and you want to assess it for risk and potential adaptation.

This example will use the substation with id "node_17", near Porus in the Parish of Manchester.

Start on the "Exposure" tab.

Under "Infrastructure" in the left sidebar, select "Power > Transmission > Substations" to show all substations.

In the map search box, type "Porus" and click on "Porus, Manchester" to zoom to the town and substation.

Under "Hazards" in the left sidebar, select "River flooding" to add a flood outline to the map.

Hover over the asset to see its ID and depth of flooding.

![Map of an electricity substation exposed to river flooding, with nearby transmission lines.](/guide_media/image26.png)

The substation intersects with different fluvial (river) flood outlines under baseline and future climate scenarios. From the depth of flooding, the analysis has estimated the direct damages to the substation itself, and indirect economic losses from buildings and businesses experiencing loss of power.

Click on the substation to show the calculated results in the right-hand details sidebar. Under the "Risk" section (not shown), the chart and table show the expected annual damages or losses.

Under the "Return Period Damages" section (shown below), the chart and table display in more detail the damages or losses which would result from a flood of a particular return period (or probability).

![Detail of an electricity substation, with damages and losses due to river flooding under current climate conditions.](/guide_media/image27.png)

In the "Return Period Damages" section, change the "Epoch" dropdown from 2010 to 2080 to see the change in damages under various possible climate change scenarios (i.e. Representative Concentration Pathways [RCP] 2.6, 4.5 and 8.5).

![Detail of an electricity substation, with damages and losses due to river flooding under future climate scenarios.](/guide_media/image28.png)

In the top menu, click on the "Risk" tab. This may change the background flood map but should leave the map location and asset selection unchanged.

Scroll back up to the "Risk" section in the right-hand sidebar.

![Detail of an electricity substation, with expected annual damages and expected annual economic losses across current and future scenarios.](/guide_media/image29.png)

One important thing to note is that, so far, only the flood hazard part of the equation has been changing in the calculations above. The "2080" risk values and return period damages have not yet considered any changes in population or the economy. These changes are included in the next step.

Once all the climate risks have been estimated, the analysis considers a chosen adaptation option for this substation, which is to build a protective wall that prevents flood waters from inundating the asset. We test different heights of flood protection walls and estimate the Net Present Value (NPV) cost, NPV benefits (in terms of avoided risks), and Benefit-Cost Ratio (BCR) values for each case.

Net Present Value is calculated over the asset lifetime, and both economic growth scenarios and discount rates go into the calculation. Population change is considered in some sectors - particularly in water, when calculating the risk of drought. The adaptation investment and maintenance costs, or the direct or indirect risk values are calculated for each year into the future, discounted and summed to give a single Net Present Value number. For more detail on these calculations, see section 2.2.2 of the Technical Report.

Scroll down to the "Adaptation Options" section.

![Detail of potential adaptation options for an electricity substation, with costs and benefits in terms of avoided risk.](/guide_media/image30.png)

Here we see that building a protective wall that is 1-meter high would incur an NPV cost of J$ 110 million over time and result in avoiding mean NPV risks of J$ 807 (somewhere between 761 and 863) million under the RCP 2.6 flooding scenario, which results in a BCR of 7.32 (somewhere between 6.91 and 7.83), which is much greater than the break-even value of 1. For this asset the chosen adaptation option presents a robust case for investment: the benefits are much greater than the costs.

## Prioritise and evaluate adaptation interventions

[Back to top](#table-of-contents)

This use case covers reviewing and prioritising adaptation options for an infrastructure sector, then going into detail on a specific asset to evaluate the direct and indirect risks, and costs and benefits of adaptation. It assumes that you start from a system- or sector-wide perspective and want to go through a process of screening assets for risk and potential adaptation.

Start from the "Adaptation" tab, chosen from the top menu bar.

In the left sidebar, make sure "Adaptation Options" is the layer style.

Select the sector as "Power", subsector as "Transmission" and asset type as "Substation" using the dropdown menus (the sector check boxes on the top left are not functional on this tab).

Select details of the hazard ("Flooding" is the only one available for this asset type) against which the adaptation option will protect. Here you can also change the climate scenario, adaptation option type, and, for some option types, protection level.

Select "Cost-Benefit Ratio" as the displayed variable.

The map then shows assets coloured by Cost-Benefit Ratio for prioritisation. In the right sidebar, the table shows assets, sorted in descending order with the most cost-beneficial at the top.

![Map showing electricity substations coloured by cost-benefit ratio of an adaptation option, with table in sorted order.](/guide_media/image31.png)

Hover over a row to indicate the asset on the map, drawing a dashed bright blue line around its location.

Click on a row for a few more details about the asset. At the right-hand end of the row, click on the zoom-in magnifying glass icon with a plus sign to zoom to the asset location. You may need to move the cursor back onto the row to see this if it has moved elsewhere.

To zoom out again to the whole island, click on the magnifying glass icon with a minus sign, which is at the top-right corner of the sidebar.

![Zoomed in map focussing on a substation with a high cost-benefit ratio of adaptation.](/guide_media/image32.png)

Once you have identified a candidate for prioritisation, zoom to its location so that it is clearly in view. You can then switch back to the "Exposure" or "Risk" tabs to bring up more details about the asset risk. In this example, we have prioritised the same substation with id "node_17", near Porus.

Click on the "Risk" tab in the top menu bar, then click on the asset to highlight it and show the right-hand details sidebar. Here, as we have seen previously, there are details of asset risk under different hazards and climate scenarios, both direct damages and indirect economic losses.

![Detail of the substation, expected damages and losses due to Cyclone hazard.](/guide_media/image33.png)

Scroll down to the "Adaptation Options" section to find the evaluated Net Present Value costs and benefits of different adaptation interventions under different hazards and climate scenarios.

![Detail of the substation, available adaptation options with costs and benefits in terms of avoided risk.](/guide_media/image34.png)

From any of the asset details sections (e.g. Adaptation Options as shown above), click on the download icon to save a CSV of all the table values, including all hazards and epochs.

## About this guide

[Back to top](#table-of-contents)

This document may be cited as follows:

> Russell, Tom, Ziarkowski, Maciej, Pant, Raghav, Becher, Olivia, Haggis Robyn, Majid, Aman, Verschuur, Jasper, Grant, Ardith, Mills, Anaitee, Williams, Edson, Fowler, Tim and Hall, Jim W. (2022). *User Guide for the Jamaica Systemic Risk Assessment Tool (J-SRAT)*. Environmental Change Institute, University of Oxford, UK.

Report copyright University of Oxford, 2022.

This report was produced as part of the project "A geospatial analysis platform for infrastructure risk assessment and resilient investment prioritisation in Jamaica" which was funded by the UK Foreign Commonwealth and Development Office to inform the FCDO as part of the Coalition for Climate Resilient Investments. The views expressed and recommendations set out in this report are the authors' own and do not necessarily reflect the position of the FCDO, CCRI or any stakeholder in Jamaica.

The materials have been prepared by Oxford University. Whilst every care has been taken by Oxford University to ensure the accuracy and completeness of the reports and maps, the reader must recognise that errors are possible through no fault of Oxford University and as such the parties give no express or implied representations or warranty as to:

(i) the quality or fitness for any particular purpose of the report or maps supplied or of any design, workmanship, materials or parts used in connection therewith or correspondence with regard to any description or sample; or

(ii) the accuracy, sufficiency or completeness of the reports or maps provided. In particular, there are hereby expressly excluded all conditions, warranties and other terms which might otherwise be implied (whether by common law, by statute or otherwise).

Oxford University, its employees, servants and agents shall accept no liability for any damage caused directly or indirectly by the use of any information contained herein and without prejudice to the generality of the foregoing, by any inaccuracies, defects or omissions.
""",
    },
]


def add_guide_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")
    Page = apps.get_model("content", "Page")

    page, _ = Page.objects.get_or_create(
        name=GUIDE_PAGE_NAME,
        defaults={"title": "Guide"},
    )

    for block in GUIDE_BLOCKS:
        MarkdownBlock.objects.update_or_create(
            page=page,
            slot=block["slot"],
            defaults={
                "title": block["title"],
                "markdown": block["markdown"],
            },
        )


def remove_guide_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")

    MarkdownBlock.objects.filter(
        page=GUIDE_PAGE_NAME,
        slot__in=[block["slot"] for block in GUIDE_BLOCKS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0007_data_markdown_blocks"),
    ]

    operations = [
        migrations.RunPython(add_guide_blocks, remove_guide_blocks),
    ]
