import numpy as np
import os
import time
# import multiprocessing as mp
import shutil
import h5py
import sys
import units
import mynumerics as mn


import warnings

import matplotlib
# matplotlib.rcParams['text.usetex'] = True
# import mynumerics as mn
import matplotlib.pyplot as plt

arguments = sys.argv

showplots = not('-nodisplay' in arguments)


# results_path = os.path.join("D:\data", "Discharges", "I0_p","preion_8")
results_path = os.path.join("D:\data", "Discharges", "I0_p","scan2")

filename = 'analyses.h5'

FF_orders_plot = 4

filename_path = os.path.join(results_path,filename)
 
        
with h5py.File(filename_path, 'r') as InputArchive:
    # load data
   available_data = list(InputArchive.keys())
   
   Intens_map = InputArchive['Intensity_tmax_SI_p_I0_r_z'][:]
   Lcoh_map = InputArchive['Lcoh'][:]
   Lcoh_no_FSPA_map = InputArchive['Lcoh_no_FSPA'][:]
   zgrid = InputArchive['z_grid'][:]
   rgrid = InputArchive['r_grid'][:]
   I0_grid = InputArchive['I0_grid'][:]
   p_grid = InputArchive['p_grid'][:]
   Hgrid = InputArchive['Lcoh_Hgrid'][:]


contours = 1e3*np.asarray([0.0075, 0.015, 0.03, 0.06])
def plot_p_I0_map(data_map, title, fname, cmap='plasma',vmax=None):
    fig1, ax1 = plt.subplots()
    map1 = ax1.pcolor(p_grid, I0_grid, data_map.T, shading='auto', cmap=cmap, vmax=vmax)  
    
    map2 = ax1.contour(p_grid, I0_grid, data_map.T, contours, colors = "black", linestyles = ['dashdot','dotted','dashed','solid'])
    
    # ax1.set_xlim(left = 10)
    # ['solid', 'dashed', 'dashdot', 'dotted' ]
          
    # ax1.set_ylim([0,1e6*rmax])
    ax1.set_xlabel('p [mbar]'); ax1.set_ylabel('I0 [SI]');
    ax1.set_title(title)
    cbar = fig1.colorbar(map1) 
    cbar.set_label(r'$L_{coh}$ [mm]')
    
    # fig1.savefig(fname, dpi = 600)
    if showplots: plt.show()
               
plot_p_I0_map(1e3*Lcoh_map[1,:,:,0,-1], 'H17', 'test.png',vmax=60, cmap = 'plasma')





############## plot intensity curves ############################

I0_indices = [4,13,19]
p_indices = [4,13,19]
colors = ["tab:orange","tab:blue","tab:green"]
linestyles = ['-','--',':']

pressures_round = np.round(p_grid[p_indices])
I0s_round = 1e18*np.round(1e-18*np.asarray(I0_grid[p_indices]),decimals=1)

pressures_leg = [str(pressure_round)+' mbar' for pressure_round in pressures_round]
I0s_leg = [str(I0_round)+' W/m2' for I0_round in I0s_round]

fig, ax = plt.subplots()    
for k1 in range(len(I0_indices)):
    for k2 in range(len(p_indices)):
        ax.plot(1e3*zgrid, Intens_map[p_indices[k2],I0_indices[k1],0,:],
                color=colors[k1],
                linestyle=linestyles[k2],
                linewidth=3)    
        
        

 
# ax.plot(1e3*zgrid, Intens_map[0,0,0,:], color="tab:orange", linewidth=3)
# ax.plot(1e3*zgrid, Intens_map[0,9,0,:], color="tab:blue", linewidth=3)
# ax.plot(1e3*zgrid, Intens_map[0,4,0,:], color="tab:green", linewidth=3)

# ax.plot(1e3*zgrid, Intens_map[4,0,0,:], color="tab:orange", linewidth=3, linestyle="--")
# ax.plot(1e3*zgrid, Intens_map[4,9,0,:], color="tab:blue", linewidth=3, linestyle="--")
# ax.plot(1e3*zgrid, Intens_map[4,4,0,:], color="tab:green", linewidth=3, linestyle="--")

# ax.plot(1e3*zgrid, Intens_map[9,0,0,:], color="tab:orange", linewidth=3, linestyle=":")
# ax.plot(1e3*zgrid, Intens_map[9,9,0,:], color="tab:blue", linewidth=3, linestyle=":")
# ax.plot(1e3*zgrid, Intens_map[9,4,0,:], color="tab:green", linewidth=3, linestyle=":")

# ax.set_ylabel("Intensity [W/m2]")
# ax.legend(loc=1, ncol=3)
from matplotlib.lines import Line2D
custom_lines = [Line2D([1], [0], color="tab:orange", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="-"),
                Line2D([0], [0], color="tab:blue", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="--"),
                Line2D([0], [0], color="tab:green", lw=3),                
                Line2D([0], [0], color="tab:grey", lw=3, linestyle=":")]

ax.legend(custom_lines, [I0s_leg[0],
                         pressures_leg[0],
                         I0s_leg[1],
                         pressures_leg[1],
                         I0s_leg[2],
                         pressures_leg[2]],
          loc=1, ncol=3)

ax.set_title("On-axis defocusing")
ax.set_xlabel('z [mm]')
ax.tick_params(axis="both")
ax.set_ylabel("Intensity [W/m2]")

plt.show()


############## plot \Delta k curves ############################

I0_indices = [4,13,19]
p_indices = [4,13,19]
colors = ["tab:orange","tab:blue","tab:green"]
linestyles = ['-','--',':']

pressures_round = np.round(p_grid[p_indices])
I0s_round = 1e18*np.round(1e-18*np.asarray(I0_grid[p_indices]),decimals=1)

pressures_leg = [str(pressure_round)+' mbar' for pressure_round in pressures_round]
I0s_leg = [str(I0_round)+' W/m2' for I0_round in I0s_round]

fig, ax = plt.subplots()    
for k1 in range(len(I0_indices)):
    for k2 in range(len(p_indices)):
        ax.plot(1e3*zgrid, np.pi/Lcoh_map[1,p_indices[k2],I0_indices[k1],0,:],
                color=colors[k1],
                linestyle=linestyles[k2],
                linewidth=3)    



# ax.legend(loc=1, ncol=3)
from matplotlib.lines import Line2D
custom_lines = [Line2D([1], [0], color="tab:orange", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="-"),
                Line2D([0], [0], color="tab:blue", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="--"),
                Line2D([0], [0], color="tab:green", lw=3),                
                Line2D([0], [0], color="tab:grey", lw=3, linestyle=":")]

ax.legend(custom_lines, [I0s_leg[0],
                         pressures_leg[0],
                         I0s_leg[1],
                         pressures_leg[1],
                         I0s_leg[2],
                         pressures_leg[2]],
          loc=1, ncol=3)

ax.set_title("H17")
ax.set_xlabel('z [mm]')
ax.tick_params(axis="both")
ax.set_ylabel("|$\Delta$ k| [1/m]")
ax.set_ylim([0,500])

plt.show()


############## plot \Delta k curves ############################

I0_indices = [4,13,19]
p_indices = [4,13,19]
colors = ["tab:orange","tab:blue","tab:green"]
linestyles = ['-','--',':']

pressures_round = np.round(p_grid[p_indices])
I0s_round = 1e18*np.round(1e-18*np.asarray(I0_grid[p_indices]),decimals=1)

pressures_leg = [str(pressure_round)+' mbar' for pressure_round in pressures_round]
I0s_leg = [str(I0_round)+' W/m2' for I0_round in I0s_round]

fig, ax = plt.subplots()    
for k1 in range(len(I0_indices)):
    for k2 in range(len(p_indices)):
        ax.plot(1e3*zgrid, np.pi/Lcoh_no_FSPA_map[1,p_indices[k2],I0_indices[k1],0,:],
                color=colors[k1],
                linestyle=linestyles[k2],
                linewidth=3)    



# ax.legend(loc=1, ncol=3)
from matplotlib.lines import Line2D
custom_lines = [Line2D([1], [0], color="tab:orange", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="-"),
                Line2D([0], [0], color="tab:blue", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="--"),
                Line2D([0], [0], color="tab:green", lw=3),                
                Line2D([0], [0], color="tab:grey", lw=3, linestyle=":")]

ax.legend(custom_lines, [I0s_leg[0],
                         pressures_leg[0],
                         I0s_leg[1],
                         pressures_leg[1],
                         I0s_leg[2],
                         pressures_leg[2]],
          loc=1, ncol=3)

ax.set_title("H17, no FSPA")
ax.set_xlabel('z [mm]')
ax.tick_params(axis="both")
ax.set_ylabel("|$\Delta$ k| [1/m]")
ax.set_ylim([0,500])

plt.show()

# intensity map


contours = 1e3*np.asarray([15, 17, 19])
def plot_p_I0_map(data_map, title, fname, cmap='plasma',vmax=None):
    fig1, ax1 = plt.subplots()
    map1 = ax1.pcolor(p_grid, I0_grid, data_map.T, shading='auto', cmap=cmap, vmax=vmax)  
    
    map2 = ax1.contour(p_grid, I0_grid, data_map.T, contours, colors = "black")
    
    # ax1.set_xlim(left = 10)
    # ['solid', 'dashed', 'dashdot', 'dotted' ]
          
    # ax1.set_ylim([0,1e6*rmax])
    ax1.set_xlabel('p [mbar]'); ax1.set_ylabel('I0 [SI]');
    # ax1.set_title(title)
    cbar = fig1.colorbar(map1) 
    cbar.set_label(r'$I$ [cutoff]')
    
    # fig1.savefig(fname, dpi = 600)
    if showplots: plt.show()
               
plot_p_I0_map(1e3*Intens_map[:,:,0,-1], 'H17', 'test.png',vmax=None, cmap = 'plasma')


## Lcoh map at given time

choice = (1,13,5)
print(p_grid[choice[1]])
print(I0_grid[choice[2]]) 

fig1, ax1 = plt.subplots()
map1 = ax1.pcolor(1e3*zgrid, 1e6*rgrid, 1e3*Lcoh_map[
                                        choice[0],choice[1],choice[2],
                                        :,:], shading='auto', cmap='plasma', vmax=30)  

ax1.set_xlabel('z [mm]'); ax1.set_ylabel(r'r [$\mu$m]');
cbar = fig1.colorbar(map1) 
cbar.set_label(r'$L_{coh}$ [mm]')

if showplots: plt.show()



