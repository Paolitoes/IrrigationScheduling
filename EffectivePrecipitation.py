import numpy as np
import matplotlib.pyplot as plt

field_area_unconverted = 6000 #ft**3
field_area = field_area_unconverted*(12)**3 #inches**3

swhc = 0.1 # inches per inches

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
root_depth = 6 #inches

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

MAD = 0.5

#Irrigate Once soil has reached MAD from capacity
#   Won't include cycles per day calcualtions, because, in this case, that will 
#   only happen if the total daily irrigation requirement is larger than the 
#   soil capacitance.

I1_capacity = Capacitance+0
I1_CapTracker = []
I1_IrrTracker = []
I1_threshold = (1-MAD)*swhc*root_depth
print(I1_threshold)

for i, ET in enumerate(ETc):
    I1_capacity += Pd[i]-ET
    I1_irrigation = 0
    if I1_capacity>=Capacitance:
        I1_capacity = Capacitance+0
    elif I1_capacity<=I1_threshold:
        I1_irrigation = Capacitance-I1_capacity
        I1_capacity += I1_irrigation

    I1_CapTracker.append(I1_capacity)
    I1_IrrTracker.append(I1_irrigation)


#Irrigate to match the daily Irrigation Requirement of Previous Day
Ir_capacity = Capacitance+0
Ir_CapTracker = []
Ir_IrrTracker = []
Ir_irrigation = 0

for i, ET in enumerate(ETc):
    Ir_capacity += Pd[i]-ET+Ir_irrigation
    Ir_IrrTracker.append(Ir_irrigation)
    if Ir_capacity <= Capacitance:
        Ir_irrigation = np.min([Capacitance-Ir_capacity,ET])
    else:
        Ir_capacity=Capacitance
        Ir_irrigation=0
    Ir_CapTracker.append(Ir_capacity)
    

#Plotting
x = np.linspace(1,30,30)

fig, axs = plt.subplots(3,1)
#Effective Precipitation and ET Plot
epp = axs[0]
epp.plot(x,Pd,label="Effective Precipitation (in)")
epp.plot(x,ETc,label="Evapotranspiration (in)")
epp.set_title("Water I/O")
epp.legend()

#Single Irrigation Plot
sip = axs[1]
sip.plot(x,I1_CapTracker,label="Current Capacity (in)")
sip.plot(x,I1_IrrTracker,label="Irrigation (in)")
sip.set_title(f"Irrigate at MAD of {MAD}")
sip.legend()

#Match-loss Irrigation
mli = axs[2]
mli.plot(x,Ir_CapTracker,label="Current Capacity (in)")
mli.plot(x,Ir_IrrTracker,label="Irrigation (in)")
mli.set_title("Irrigate to match yesterday's loss")

# mli.plot(x,np.convolve(Ir_CapTracker,[.2,.2,.2,.2,.2],mode='same'),label="Moving Average")
# That was to double check that one day offset irrigation didn't reduce current capacity over time
# and it looks like it doesn't, which it shouldn't, so everything is good.

mli.legend()

plt.tight_layout()
plt.show()


#Next is adding the how many cycles a day measurement...that will probs have to be squared with precipitation of that day. 
#   rough time for you, future paolo.