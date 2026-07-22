import numpy as np
import matplotlib.pyplot as plt

field_area_unconverted = 6000 #ft**3
field_area = field_area_unconverted*(12)**3 #inches**3

swhc = 0.17 # inches per inches

'''
first hit, the field should be calcualted all together. The water capacitance we care about depends  
on the effective root depth of the plant. For example, the tomatoe estimated root depth of 13 inches 
gives a capacitance of root_depth*SWHC=13*0.17=3.04 inches. Its this 3.04 inches that should be mulitiplied
by the canopy area of the tomato plant to estimate how much capacitance-of-interest there is. So perhaps we 
can make a total capacitance measure as well, not that it will be usefull...Actually just looked up the soil 
depth in redlands florida and it said between 1/4 of and inch to 3 inches...so lets just ignore that tbh.

So capacitance-of-interest, which we will just call capacitance here, is swhc*root depth*canopy area
'''

#example plant is stage 3 tomato, again
Kc = 1 # dimensionless
root_depth = 13 #inches

'''
Next wee need the ET0 and Pm data. Since this is meant to be a system that takes in the current day data for precipitation
and evapotranspiration, we're going to have both the ET0 and the Pm be arrays of fake data. The data will have no gaps, and 
the order in the array will represent the day of the month. 

For the Pm data, a poisson distribution will estimate which days have rainfall and also how much rainfall to match the sporadic
nature of the rain--the fact that its typically not an everyday thing. The data is not meant to be all that realistic. The total 
sum of the rainfall will be normalized to 4.3 inches to match the september example in the "ETCalculationsExamplePaper.py" file.

For the ET0 data, they will be sampled from an normal distribution centered around the september ET0 found in the file above, with
a standard deviation of the square of the mean. 
'''

'''
third hit, we need to go inside the days. If we're testing for multiple irrigations a day....or maybe we don't if we're just calculating how many...
So yes we don't need to work with intra day data just yet.
'''

days = 30 #length of the arrays, how many days we're running this simulation

#STEP 1: Generating Pd (daily precipitation) and ET0 arrays
Pm_average = 0 #inches of rain that month
ET0_average = 0.13 #inches per day

rng = np.random.default_rng(seed=691)

rain_weight = rng.poisson(1,days)
Pd = Pm_average*rain_weight/np.sum(rain_weight)

ET0 = rng.normal(ET0_average,np.sqrt(ET0_average)/6,days)

#STEP 3: Calculating Crop ET
def crop_evapotranspiration(ET0, Kc=Kc):
    ETc = ET0*Kc
    return ETc

ETc = crop_evapotranspiration(ET0)

#STEP 3: Calculate Current Capacitance

#Assume the canopy under the tomato plant starts at 100% SWHC
#and it has a radius of 34 inches

Capacitance = root_depth*swhc #units of inches
# Canopy = np.pi*(34**3) #units of inches**3
# Capacity = Capacitance*Canopy #units of inches**3
# Actually ET0 and Pd are already in units of inches (not inches/day since this time they have individual day values)
# So lets just work in inches

#Including the PAW approach
#Like in the Drip Irrigation Paper lets assume Max moister is 13% and wilt moisture is 4%
#okay so if swhc means 13% moisture that means swhc/0.13=100% moisture (whatever that means)
#which makes 4% moisture in inches, (swhc/0.13)*0.04, lets call it swmc for soil water
#minimum capacity

swmc = (swhc/0.13)*0.04



current_capacity = Capacitance+0
cap_tracker = []
cap_tracker.append(current_capacity)


MAD = 0.5
irrigation_threshold = ((swhc-swmc)*MAD+swmc)*root_depth
irrigation_tracker = []

for i, ET in enumerate(ETc):
    current_capacity = current_capacity-ET+Pd[i]
    if current_capacity<=irrigation_threshold:
        irrigation_tracker.append(Capacitance-current_capacity)
        current_capacity=Capacitance+0
    else:
        irrigation_tracker.append(0)
    
    if current_capacity>=Capacitance:
        current_capacity=Capacitance+0
    
    cap_tracker.append(current_capacity)

cap_x = np.linspace(0,30,31)
x = np.linspace(1,30,30)


fig, axs = plt.subplots(4,1)
axs[0].plot(x,ET0)
axs[0].set_title("Daily Evapotranspiration")
axs[1].plot(x,Pd)
axs[1].set_title("Precipitation")
axs[2].plot(x,irrigation_tracker)
axs[2].set_title("Irrigation Amount")
axs[3].plot(cap_x,cap_tracker)
axs[3].hlines(swmc*root_depth,0,30)
axs[3].hlines(Capacitance,0,30)
axs[3].hlines(irrigation_threshold,0,30)
axs[3].set_title(r"'Inches of water' in soil")
plt.tight_layout()
plt.show()


'''
OKAY, so the problem might be that the drip irrigation paper sets a the 8 inch wetted bulb as the space that needs to be kepts at field capacity. 
which makes sense, since the the concentration of the water will increase the longer the drip irrigation system is on near the actuall drip, 
leaving more of the water entering the center to percolate below the root, where the plant cannot reach it. 

Claude wrote me something but when you decrease the MAD you get even more cycles a day instead of converging to the 9 cycles a day from the drip irrigation paper
but I do like how it made the graphs look prettier--its like in minecraft, when we just build a bunch of farms and don't stop to make them look pretty.
Like no, making them look pretty matters too.
'''

'''
Okay this is the next day and it looks like yes, both papers are doing a few different things. The drip irrigation paper, AE50000, irrigates every day to
match the ETc of the plant that day, and since its a drip irrigation system its somewhat slow which gives it the long daily total irrigation time, then 
paper split its cycles so that they just long enough for their total water output to be equal to the volume of water needed to fill the pre-defined area
of influence (which we assume is motivated by the fact that the water concentration is largest at the actuall drip point and at some point that concentration
will overcome the SWHC such that the water starts to percolate into the unreachable root depths) to SWHC, which is 50% of the SWHC in this case since the 
soil was assuming to be at 50% PAW initially. 

Then it splits the cycles evenly throughout the day. I think the mis assumptions between the papers is how much water the soil is losing at any given point.
I mean the precipetation paper I think only has the ETc and ET0 as what takes water from the soil, and the drip irrigation paper either take it so the small 
cylinder of influence loses half its water in a few hours or that water now spread over the soil so the concentration in the imediate surrounding is low 
enough again that we can drip water in without losing it to percolation... We'd have to check how far away the drip irrigation holes are to see if there 
really is enough space where the water can be spread through... Alternatively its to spread through the cylinder of influence, since drip irrigation is
all at single points and doesn't spread its water like other irrigation methods...Lets look at the hole distances

The distance between emmiters in the same row/tape is 12 inches. the distance between rows is 6 feet, lets assume the beds are 3 ft long and have two drip 
tapes through it. 
'''