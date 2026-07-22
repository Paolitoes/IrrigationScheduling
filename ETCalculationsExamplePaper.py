'''
Source: https://ask.ifas.ufl.edu/publication/AE458
The method outlined here is not responsive to current weather or soil conditions, it is only an
estimate based on the historical soil and weather characteristics, but it can still provide a base
guideline for which to base a rudimentary irrigation schedule off.

This method produces daily run time of irrigation system per day given historical monthly estimates.

"Irrigate for X minutes every Y days" would be the final message. Should Y be less than 1, that means 
multiple irrigation cycles are needed per day.

Possible Problems:
Flow Rate -- the 23.5 gallons an hour flow rate here is all going to a 118 diameter sprinkler. 
If 23.5 gallons is regular for a single sprinkler then fine. Actually after looking some things up, 
it seems llike, for an orchard single sprinkler, thats around the right amount per sprinkler. 

The IFAS "How to Determine Run Time and Irrigation Cycles for Drip Irrigation: Tomato and Pepper Examples" paper
got very different values for the irrigation schedule, namely that we should irrigate 9 times a day for 32.1 minutes. 

The only way we get multiple irrigation times a day in this system is if the inches irrigation depth, aka the estimate 
for how many inches of water that the soil can hold to be above the depletion level, is less than the inches of water each 
crop needs a day.  

In the other Drip Irrigation paper, 1) the effective precipitation is not accounted for at all, 2) April, a month with a 
higher ETc for tomatoes, was used as the example month, 3) the drip irrigation system might have less gallons/hour (which 
only effects length of irrigation not how many cycles but still), and 4) instead of basing how much water to add off of MAD
and SWHC, it filled the field to plant available capacity.

So for #4 I suspect that the MAD and SWHC approach might be equivalent to the PAW approach, in fact it might actually be more 
water, since it doesn't have the wilting point as the floor but instead 0 water as the floor...wait that does affect things 
because then the PAW approach has a smaller "Inches irrigation depth" estimate (the paper used total volume of water needed) 
and that makes it easier for the ETc to be larger than it, creating multiple cycles a day. That alongside both the april ET0 
of 0.17which is 0.04 inches higher than September's ET0 of 0.13 used here and the complete disregard to precipitation, means 
the irrigation rate for each crop in the drip irrigation paper is likely much higher. 

In fact, since the drip irrigation paper doesn't include precipitation, it uses the ETc of the crop directly as the irrgation 
requirement. The ETc for this method in september was 0.13 inches, and the calculated irrigation depth was 0.03, so 0.03/0.13
give 0.2307 as in we have to irrigate every 0.2307 days or rather 1/0.2307 = 4.3 rounded up to 5 times a day. The april ETc of 
0.17 with the 0.03 inched depth of this paper gives 5.6 rounded to 6 cycles a day, and the decrease in the irrigation depth of
the 50% PAW approach likely account for the 2.6 (the drip irrigation paper got 8.2 cycle really, and rounded to 9 so, 8.2 - 5.6
give 2.6) cycle difference. 

Okay wow. The paper are likely both right, just the difference from including the precipitation, and likely that the precipitation 
was higher in the florida subtropical hurricane months, made the difference so drastic. Calculation of the effective rainfall likely
is accounting for the fact that the rain is not evenly spaced to fill the SWHC of the land exactly every time and stop, so a monthly 
ETc of 3.5 inches is not completely covered by historical average rainfall of 4.2 inches, since a lot of those 4.2 inches are wasted
being poured onto land that can't contain it. Also the effective rainfall equation is likely overestimating how much of that water
should be counted, since the florida soil is on the lower ends of SWHC.

So perhaps a bespoke method to incorporate the effective precipitation is to 1) track the actually daily precipitation on the field using
a rain gauge, 2) keep a running estimate of the current field moister or distance from the SWHC. Then we can calculate an estimate from 
rain gauge and the field area of the total volume of water that the field gained, which can be added to the current estimate for the amount of
water currently held by the soil, and anything above the SWHC is not counted towards the effective precipitation--becuase the soil could hold it.
The estimate of the distance from the SWHC can be made more confident by the occasional slight overfill of the field, which means we will know the feild
is at max capacity again, and the area integrations of the ET0 and ETc of the crops of the field can be used daily to "remove" water from the estimate
which gets less and less confident as we move away from our "max capacity" garunteed data points.  Honestly that sounds doable.

'''

import numpy as np
import matplotlib.pyplot as plt

# Soil Series Data

#Source: https://websoilsurvey.nrcs.usda.gov/app/WebSoilSurvey.aspx -> rectangle area of interest -> Soil data explorer
# -> Soil Properties and Qualities -> Soil Physical Properties -> All Layers (Weighted Average) -> view Rating
#"Krome very gravelly marly loam-Urban land complex, 0 to 2 percent slopes"
swhc = 0.17 # Soil Water Holding Capacity, in inches per inches


#Plant Characteristics

#Using Tomatoes as example plant
#Source: Vegetable production handbook of florida, Chapter 3: Principles and Practices of Irrigation Management for Vegetables
# Crop Coefficients are given based on stage of plant growth, which seems to be split into however many stages--I think it might depend on the crop coefficient source, 
# if they don't give it in days from seeding/transplanting.
# we're gonna assume stage 3 for this tomato
Kc_tomato = 1 # Crop coefficients are dimensionless, they are the ratio between the ETc and ET0 (aka so when multiplying ET0 by Kc, we'd get an estimate for the ETc, which is whatever units your ET0 was in)
root_depth_tomato = 12 #measured in inches, guestimate from looking online


#Weather Data
# ET0 for homestead station: https://fawn.ifas.ufl.edu/tools/et/graphic.php?locId=440
# We're gonna use they values they use here, the actual values are available under the "Data Access" Tab in the website above, but there in daily amounts in CVS and I dont want to calculate the averages right now
# This should be in the calculations page, but again I just didn't want to do these myself right now.
sept_ET0, sept_Pm = 0.13, 4.2 #ET0 here is inches/day, Pm is also inches (I'm assuming a month)
octo_ET0, octo_Pm = 0.12, 3.5
nove_ET0, nove_Pm = 0.09, 2.4
dece_ET0, dece_Pm = 0.08, 1.9


#Irrigation System Characteristics
#All of this right now are just fake numbers, they should be measured once the irrigation system is in place
flow_rate_preconversion = 23.5 # gallons/hour
flow_rate = flow_rate_preconversion*231 # inches/hour
effective_wetted_diameter = 118 #diameter of area wetted by each sprinkler I'm assuming, measured in inches
irrigation_efficiency = 0.95 #drip irrigation systems do not loose all that much water to the air


#Local Managment Practices 
MAD = 0.5 #the Management Allowable Depletion, the precentage of plant-available water that can be extracted from the root zone before a crop experiences water stress


#Actual Calculations

#STEP 1: Calculate historical average monthl and daily ET0 and total average monthly precipitation, Pm
#we imported the values above.

#STEP 2: Calculate crop ET
def crop_evapotranspiration(ET0, Kc=Kc_tomato):
    ETc = ET0*Kc
    return ETc

sept_ETc = crop_evapotranspiration(sept_ET0)
octo_ETc = crop_evapotranspiration(octo_ET0)
nove_ETc = crop_evapotranspiration(nove_ET0)
dece_ETc = crop_evapotranspiration(dece_ET0)

print(f"sept_ET0: {sept_ET0}")
print(f"sept_ETc: {sept_ETc}")

#STEP 3: Calculate Effective Precipitaion
def soil_water_storage_factor(root_depth):
    D = .8*root_depth*swhc
    return 0.5317+0.2951*D-0.0576*D**2+0.0038*D**3

def effective_precipitation(Pm,ETc,root_depth=root_depth_tomato):
    '''
    Return effective precipitation in inches/day
    '''
    return soil_water_storage_factor(root_depth)*(0.7092*Pm**0.8242-0.11556)*(10**(0.2426*ETc))/30.5

sept_Pe = effective_precipitation(sept_Pm,sept_ETc)
octo_Pe = effective_precipitation(octo_Pm,octo_ETc)

print(f"sept_Pe: {sept_Pe}")

#STEP 4: Net Irrigation Requirement 
def net_irrigation_requirement(ETc,Pe):
    return ETc-Pe
 
sept_irr = net_irrigation_requirement(sept_ETc,sept_Pe)

print(f"sept_irr: {sept_irr}")

#STEP 5:  Gross Irrigation requirement
def gross_irrigation_requirement(net_irr, irrigation_efficiency=irrigation_efficiency):
    return net_irr/irrigation_efficiency

sept_gross_irr = gross_irrigation_requirement(sept_irr)

print(f"sept_gross_irr: {sept_gross_irr}")

#STEP 6: Irrigation Run Time Per cycle/event
def irrigation_rate(flow_rate, diameter):
    return flow_rate/(np.pi*(0.5*diameter)**2)

irr_rate = irrigation_rate(flow_rate,effective_wetted_diameter)

print(f"irr_rate: {irr_rate}")

def irrigation_schedule(MAD,gross_irr):
    print(f"Irrigate for {MAD*swhc*60/irr_rate} minutes every {MAD*swhc/gross_irr} Days")

irrigation_schedule(MAD,sept_gross_irr)







