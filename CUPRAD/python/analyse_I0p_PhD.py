import numpy as np
import os
import time
# import multiprocessing as mp
import shutil
import h5py
import sys
import units
import mynumerics as mn
import HHG
import XUV_refractive_index as XUV_index


import warnings

import matplotlib
# matplotlib.rcParams['text.usetex'] = True
# import mynumerics as mn
import plot_presets as pp

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

arguments = sys.argv

showplots = not('-nodisplay' in arguments)


# results_path = os.path.join("D:\data", "Discharges", "I0_p","preion_8")
# results_path = os.path.join("D:\data", "Discharges", "I0_p","scan2")

results_paths = [os.path.join("D:\data", "Discharges", "I0_p","scan1"),
                 os.path.join("D:\data", "Discharges", "I0_p","scan2")]

preions = np.asarray([0,0.08])


OutPath = 'outputs_PhD' 
if os.path.exists(OutPath) and os.path.isdir(OutPath):
  shutil.rmtree(OutPath)
  print('deleted previous results')
os.mkdir(OutPath)


filename = 'analyses.h5'

FF_orders_plot = 4

Ip_eV = 13.99961
lambdaSI = 792e-9


Intens_map = []; plasma_map = []; Lcoh_map = []; Lcoh_no_FSPA_map = []; Cutoff_map = []
for results_path in results_paths:
    filename_path = os.path.join(results_path,filename)
     
            
    with h5py.File(filename_path, 'r') as InputArchive:
        # load data
       available_data = list(InputArchive.keys())
       
       Intens_map.append(InputArchive['Intensity_tmax_SI_p_I0_r_z'][:])
       Lcoh_map.append(InputArchive['Lcoh'][:])
       Lcoh_no_FSPA_map.append(InputArchive['Lcoh_no_FSPA'][:])
       zgrid = InputArchive['z_grid'][:] # assumed shared
       rgrid = InputArchive['r_grid'][:]
       I0_grid = InputArchive['I0_grid'][:]
       p_grid = InputArchive['p_grid'][:]
       Hgrid = InputArchive['Lcoh_Hgrid'][:]
       plasma_map.append(InputArchive['plasma_tmax'][:])
       
       Cutoff_map.append(HHG.ComputeCutoff(Intens_map[-1]/units.INTENSITYau,
                                       mn.ConvertPhoton(lambdaSI,'lambdaSI','omegaau'),
                                       mn.ConvertPhoton(Ip_eV,'eV','omegaau')
                                       )[1])



N_atm = 2.7e19 * 1e6
XUV_table_type_diffraction = 'NIST' # {Henke, NIST}
XUV_table_type_absorption = 'Henke' # {Henke, NIST} 
gas_type = 'Kr'

def f2_funct(E):
    return XUV_index.getf2(gas_type + '_' + XUV_table_type_absorption, E)

def sigma(omega):
    f2_value    = f2_funct(mn.ConvertPhoton(omega, 'omegaSI', 'eV'))
    lambdaSI    = mn.ConvertPhoton(omega, 'omegaSI', 'lambdaSI')
    return 2.0 * units.r_electron_classical * lambdaSI * f2_value

def L_abs(omega,pressure):
    f2_value    = f2_funct(mn.ConvertPhoton(omega, 'omegaSI', 'eV'))
    lambdaSI    = mn.ConvertPhoton(omega, 'omegaSI', 'lambdaSI')
    rho0 = pressure*N_atm
    return 1.0 / (2.0 * rho0 * units.r_electron_classical * lambdaSI * f2_value) 

## (p,I0) space

choices = [[0,1],[1,1]]


contours = 1e3*np.asarray([0.0075, 0.015, 0.03, 0.0595])
contours_signal = np.asarray([0.5,0.75,0.9,0.99])
Lcoh_saturation = 20. # 60.

delta_k_lims = {'vmin' : 0.0, 'vmax': 0.5}
# delta_k_lims = {'vmin' : 0.0, 'vmax': 0.5}



for choice1 in choices:

    local_title = r'$\eta_0$='+ '{:.0f}'.format(100*preions[choice1[0]]) + ' %'
                  
    # coherence map
    image = pp.figure_driver()  
    image.set_fontsizes = 'triplet' 
    image.sf = [pp.plotter() for k1 in range(2)]
    
    image.sf[0].method = plt.pcolor    
    image.sf[0].args = [p_grid, I0_grid,(1e3*Lcoh_map[choice1[0]][choice1[1],:,:,0,-1]).T]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}  
    if (np.max((1e3*Lcoh_map[choice1[0]][1,:,:,0,-1]).T) > Lcoh_saturation): image.sf[0].kwargs['vmax']=Lcoh_saturation
    
    image.sf[0].colorbar.show = True  
    image.sf[0].colorbar.kwargs = {'label': r'$L_{coh}$ [mm]'}
    
    image.sf[1].method = plt.contour
    
    image.sf[1].args = image.sf[0].args + [contours]
    image.sf[1].kwargs = {'colors' : "black"} #'linestyles' : ['dashdot','dotted','dashed','solid']}
    image.sf[1].colorbar.show_contours = True    
      
    image.xlabel = r'$p$ [mbar]'; image.ylabel = r'$I_0$ [SI]'
    
    image.title = 'H'+str(Hgrid[choice1[1]])+', '+local_title

    outfpath = os.path.join(OutPath,
                         'Lcoh_pI0_eta'+'{:.0f}'.format(100*preions[choice1[0]])+'_H'+str(Hgrid[choice1[1]])
                         )
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    image.annotation = [['(b)'],
                    {'xy' : (0.025, .9),
                     'xycoords' : 'axes fraction',
                     'color' : 'w'}]   
    pp.plot_preset(image)

    # Delta k
    Lcoh_temp = 1e3*(Lcoh_map[choice1[0]][choice1[1],:,:,0,-1]).T

    # reverse map
    orig_map=plt.cm.get_cmap('plasma')

    image.sf[0].args = [p_grid, I0_grid, np.pi/Lcoh_temp]
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : orig_map.reversed(), **delta_k_lims} 
    # image.sf[1].args = image.sf[0].args + [contours_signal]
    image.sf[0].colorbar.kwargs = {'label': r'$|\Delta k_{'+str(Hgrid[choice1[1]])+'}|$ [1/mm]'}
    
    
    outfpath = os.path.join(OutPath,
                         'Delta_k_pI0_eta'+'{:.0f}'.format(100*preions[choice1[0]])+'_H'+str(Hgrid[choice1[1]])
                         )
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    image.annotation = [['(a)'],
                    {'xy' : (0.025, .9),
                     'xycoords' : 'axes fraction',
                     'color' : 'w'}]        
    pp.plot_preset(image)
    
    # rescale to XUV signal
    Lcoh_temp = 1.*(Lcoh_map[choice1[0]][choice1[1],:,:,0,-1]).T
    XUV_signal = np.zeros(Lcoh_temp.shape)
    
    for k1 in range(len(p_grid)):
      L_abs_temp = L_abs(Hgrid[choice1[1]]*mn.ConvertPhoton(lambdaSI,'lambdaSI','omegaSI'),1e-3*p_grid[k1])
      for k2 in range(len(I0_grid)):
        XUV_signal[k2,k1] = 1.0/(1+4.*(np.pi**2) * (L_abs_temp/Lcoh_temp[k2,k1])**2) 

    image.sf[0].args = [p_grid, I0_grid,XUV_signal]
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'} 
    image.sf[1].args = image.sf[0].args + [contours_signal]
    image.sf[0].colorbar.kwargs = {'label': r'$I_{'+str(Hgrid[choice1[1]])+'}$ [arb. u.]'}
    
   
    outfpath = os.path.join(OutPath,
                         'XUV_signal_pI0_eta'+'{:.0f}'.format(100*preions[choice1[0]])+'_H'+str(Hgrid[choice1[1]])
                         )
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    image.annotation = [['(c)'],
                    {'xy' : (0.875, .9),
                     'xycoords' : 'axes fraction'}]   
    pp.plot_preset(image)
    
    
    # ionisations
    image = pp.figure_driver()
    image.set_fontsizes = 'doublet+'     
    image.sf = [pp.plotter() for k1 in range(2)]
    
    image.sf[0].method = plt.pcolor    
    image.sf[0].args = [p_grid, I0_grid,(plasma_map[choice1[0]][:,:,0,-1]).T]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}  
    
    image.sf[0].colorbar.show = True
    image.sf[0].colorbar.kwargs = {'label': r'Ionisation [%]'}
    
    # image.sf[1].method = plt.contour
    
    # image.sf[1].args = image.sf[0].args + [contours]
    # image.sf[1].kwargs = {'colors' : "black"} #'linestyles' : ['dashdot','dotted','dashed','solid']}
    # image.sf[1].colorbar.show_contours = True    
      
    image.xlabel = r'$p$ [mbar]'; image.ylabel = r'$I_0$ [SI]'
    
    image.title = local_title
    
    outfpath = os.path.join(OutPath,'Ionisation_pI0_eta'+'{:.0f}'.format(100*preions[choice1[0]]))
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    
    pp.plot_preset(image)
    
    # intensity
    image = pp.figure_driver() 
    image.set_fontsizes = 'doublet+' 
    image.sf = [pp.plotter() for k1 in range(2)]
    
    image.sf[0].method = plt.pcolor    
    image.sf[0].args = [p_grid, I0_grid,(Cutoff_map[choice1[0]][:,:,0,-1]).T]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}  
    
    image.sf[0].colorbar.show = True  
    image.sf[0].colorbar.kwargs = {'label': r'Cutoff [-]'}  
    
    # image.sf[1].method = plt.contour
    
    # image.sf[1].args = image.sf[0].args + [contours]
    # image.sf[1].kwargs = {'colors' : "black"} #'linestyles' : ['dashdot','dotted','dashed','solid']}
    # image.sf[1].colorbar.show_contours = True    
      
    image.xlabel = r'$p$ [mbar]'; image.ylabel = r'$I_0$ [SI]'
    
    image.title = local_title
    
    outfpath = os.path.join(OutPath,'Cutoff_pI0_eta'+'{:.0f}'.format(100*preions[choice1[0]]))
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    pp.plot_preset(image)


# sys.exit()

# ionisation difference
image = pp.figure_driver()
image.set_fontsizes = 'doublet+'     
image.sf = [pp.plotter()]
image.sf[0].method = plt.pcolor    
image.sf[0].args = [p_grid, I0_grid,abs((plasma_map[1][:,:,0,-1]).T - (plasma_map[0][:,:,0,-1]).T -8. )]    
image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}  
image.sf[0].colorbar.show = True   
image.xlabel = r'$p$ [mbar]'; image.ylabel = r'$I_0$ [SI]'
# image.savefig_args = [os.path.join(OutPath,'figure1.pdf')]
# image.savefig_kwargs = {'dpi' : 600}
pp.plot_preset(image)

#intensity difference
image = pp.figure_driver() 
image.set_fontsizes = 'doublet+'    
image.sf = [pp.plotter()]
image.sf[0].method = plt.pcolor    
image.sf[0].args = [p_grid, I0_grid,abs((Intens_map[1][:,:,0,-1]).T - (Intens_map[0][:,:,0,-1]).T)/np.max((Intens_map[0][:,:,0,-1]).T)]    
image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}  
image.sf[0].colorbar.show = True   
image.xlabel = r'$p$ [mbar]'; image.ylabel = r'$I_0$ [SI]'
pp.plot_preset(image)




## (r,z) Cut-offs & ionisations
# choices = []

choices = [(0,13,5,1),(1,13,5,1),
            (0,13,17,1),(1,13,17,1),
            (0,5,5,1),(1,5,5,1),
            (0,18,17,1),(1,18,17,1)]

# choices = [(0,0,0,1),(1,0,0,1),
#             (0,0,19,1),(1,0,19,1),
#             (0,19,0,1),(1,19,0,1),
#             (0,19,19,1),(1,19,19,1)]

annotation_text = '(b)'

for choice1 in choices:
   
    local_title = r'$I_0$='+'{:.2e}'.format(1e-4*I0_grid[choice1[2]]) + r' W/cm$^2$, ' +\
                  r'$p$='+'{:.0f}'.format(p_grid[choice1[1]]) + ' mbar, '+\
                  r'$\eta_0$='+ '{:.0f}'.format(100*preions[choice1[0]]) + ' %'
                  
    fname_string = 'I0_'+str(choice1[2])+'_p'+str(choice1[1])+'_eta'+str(choice1[0])
   
    image = pp.figure_driver() 
    image.annotation = [[annotation_text],
                    {'xy' : (0.025, .9),
                     'xycoords' : 'axes fraction',
                     'color' : 'w'}]
    
    image.set_fontsizes = 'doublet+' 
    image.sf = [pp.plotter() for k1 in range(2)]
    
    image.sf[0].method = plt.pcolor    
    image.sf[0].args = [1e3*zgrid, 1e6*rgrid, Cutoff_map[choice1[0]][
                                            choice1[1],choice1[2],
                                            :,:]]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}    
    
    image.sf[0].colorbar.show = True    
    image.xlabel = r'$z$ [mm]'; image.ylabel = r'$\rho$ [$\mu$m]'
    
    image.sf[0].colorbar.show = True
    image.sf[0].colorbar.kwargs = {'label': r'Cutoff [-]'}   
    
    image.sf[1].method = plt.contour
    contours = np.asarray([15,17,19,21,23])
    image.sf[1].args = image.sf[0].args + [contours]
    image.sf[1].kwargs = {'colors' : "black"} #'linestyles' : ['dashdot','dotted','dashed','solid']}
    image.sf[1].colorbar.show_contours = True    
    
    
    image.title = local_title
                  
    outfpath = os.path.join(OutPath,'Cutoff_rz_'+fname_string)
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    pp.plot_preset(image)
    
    ####
    
    image = pp.figure_driver()
    image.annotation = [[annotation_text],
                    {'xy' : (0.025, .9),
                     'xycoords' : 'axes fraction',
                     'color' : 'w'}]    
    image.set_fontsizes = 'doublet+' 
    image.sf = [pp.plotter()]
    
    image.sf[0].method = plt.pcolor    
    image.sf[0].args = [1e3*zgrid, 1e6*rgrid, plasma_map[choice1[0]][
                                            choice1[1],choice1[2],
                                            :,:]]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}    
    
    image.sf[0].colorbar.show = True    
    image.xlabel = r'$z$ [mm]'; image.ylabel = r'$\rho$ [$\mu$m]'
    
    image.sf[0].colorbar.show = True
    image.sf[0].colorbar.kwargs = {'label': r'Ionisation [%]'}
    
    image.title = local_title
    
    
    outfpath =os.path.join(OutPath,'Ionisation_rz_'+fname_string)
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    pp.plot_preset(image)
    
    ## Coherence maps
    image = pp.figure_driver()
    image.annotation = [[annotation_text],
                    {'xy' : (0.025, .9),
                     'xycoords' : 'axes fraction',
                     'color' : 'w'}]    
    image.set_fontsizes = 'doublet+' 
    image.sf = [pp.plotter()]
    
    image.sf[0].method = plt.pcolor    
    Lcoh_tmp = 1e3*Lcoh_map[choice1[0]][
                                            choice1[3],choice1[1],choice1[2],
                                            :,:]
    image.sf[0].args = [1e3*zgrid, 1e6*rgrid, Lcoh_tmp]    
    image.sf[0].kwargs = {'shading' : 'auto', 'cmap' : 'plasma'}   
    if (np.max(Lcoh_tmp) > Lcoh_saturation): image.sf[0].kwargs['vmax']=Lcoh_saturation
    
    image.sf[0].colorbar.show = True    
    image.xlabel = r'$z$ [mm]'; image.ylabel = r'$\rho$ [$\mu$m]'
    
    image.sf[0].colorbar.show = True
    image.sf[0].colorbar.kwargs = {'label': r'$L_{coh}$ [mm]'}
    
    image.title = 'H' + str(Hgrid[choice1[3]]) + ', ' + local_title
    
    
    fname_string = fname_string + '_H' + str(Hgrid[choice1[3]])
    outfpath =os.path.join(OutPath,'Lcoh_rz_'+fname_string)
    image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
    image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
    pp.plot_preset(image)





# intensity curves

I0_indices = [4,13,19]
p_indices = [4,13,19]
colors = ["k","b","r"]
linestyles = ['-','--',':']

annotation_text = '(c)'

image = pp.figure_driver()  
image.annotation = [[annotation_text],
                    {'xy' : (0.05, .9), # 0.15 0.05
                     'xycoords' : 'axes fraction'}]

image.set_fontsizes = 'doublet+'  
image.sf = [] 

pressures_round = np.round(p_grid[p_indices])
I0s_round = 1e18*np.round(1e-18*np.asarray(I0_grid[p_indices]),decimals=1)

pressures_leg = [str(pressure_round)+' mbar' for pressure_round in pressures_round]
I0s_leg = [str(I0_round)+' W/m2' for I0_round in I0s_round]

for k1 in range(len(I0_indices)):
    for k2 in range(len(p_indices)):
        image.sf.append(pp.plotter())
        image.sf[-1].args =[1e3*zgrid, Cutoff_map[0][p_indices[k2],I0_indices[k1],0,:]]
        image.sf[-1].kwargs = {'color' : colors[k1], 'linestyle' : linestyles[k2]}
        
# custom_lines = [Line2D([1], [0], color="k", lw=3),
#                 Line2D([0], [0], color="tab:grey", lw=3, linestyle="-"),
#                 Line2D([0], [0], color="b", lw=3),
#                 Line2D([0], [0], color="tab:grey", lw=3, linestyle="--"),
#                 Line2D([0], [0], color="r", lw=3),                
#                 Line2D([0], [0], color="tab:grey", lw=3, linestyle=":")]

custom_lines = [Line2D([1], [0], color="k", lw=3),
                Line2D([0], [0], color="r", lw=3), 
                Line2D([0], [0], color="b", lw=3),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="--"),
                Line2D([0], [0], color="tab:grey", lw=3, linestyle="-"),                               
                Line2D([0], [0], color="tab:grey", lw=3, linestyle=":")]

# legend_entries = [I0s_leg[0],
#                   pressures_leg[0],
#                   I0s_leg[1],
#                   pressures_leg[1],
#                   I0s_leg[2],
#                   pressures_leg[2]]

legend_entries = [I0s_leg[0],
                  I0s_leg[1],
                  I0s_leg[2],
                  pressures_leg[0],                  
                  pressures_leg[1],                  
                  pressures_leg[2]]

image.legend_args = [custom_lines,legend_entries]
# image.legend_kwargs = {'loc': 1, 'ncol': 2}
image.legend_kwargs = {'ncol': 2}
# image.legend_set_in_layout = False
# image.legend_kwargs = {'ncol': 3}


image.right_ylim_args = [16.345521723472736, 27.996160718565243]
image.add_right_y_axis = True
# image.right_ylim_args = [0, 1]

image.right_ylim_args = list(units.INTENSITYau*HHG.ComputeInvCutoff(np.asarray(image.right_ylim_args),
                                        mn.ConvertPhoton(lambdaSI,'lambdaSI','omegaau'),
                                        mn.ConvertPhoton(Ip_eV,'eV','omegaau')
                                        ))
image.right_ylabel =  r'$I$ [SI]'

image.title = r"On-axis cutoff"
image.xlabel = r'$z$ [mm]'
# ax.tick_params(axis="both")
image.ylabel = r'Cutoff [-]'

image.xlim_args = [[0,15]]


outfpath = os.path.join(OutPath,'Cutoff_onaxis')
image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
    
pp.plot_preset(image)
image.add_right_y_axis = False; image.right_ylim_args = []; del image.right_ylabel


# Delta k
choiceHs = [1]
choice_preions = [0,1]

ylims1 = [[[0,5.5],[0,0.4]]]
ylims2 = [[[0,0.12],[0,0.03]]]

k_H = -1; k_preion = -1
for choiceH in choiceHs:
    k_H += 1
    for choice_preion in choice_preions:
        k_preion += 1
        k3 = 0
        fname_string = '_eta'+str(k_preion)
        for k1 in range(len(I0_indices)):
            for k2 in range(len(p_indices)):
                image.sf[k3].args =[1e3*zgrid, 1e-3*np.pi/Lcoh_map[choice_preion][choiceH,p_indices[k2],I0_indices[k1],0,:]] # np.pi/Lcoh_map[0][1,p_indices[k2],I0_indices[k1],0,:]
                k3+=1
                
                
        image.xlabel = r'$z$ [mm]'
        # ax.tick_params(axis="both")
        image.ylabel = r'$|\Delta k|$ [1/mm]'
        image.title = r'H'+str(Hgrid[choiceH]) + r', $\eta_0$='+ '{:.0f}'.format(100*preions[choice_preion]) + ' %'
        
        image.ylim_args = [ylims1[k_H][k_preion]]
        
        outfpath = os.path.join(OutPath,'Lcoh_onaxis_'+'H'+str(Hgrid[choiceH])+fname_string)
        image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
        image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
        
        pp.plot_preset(image)
        
        
        # scaled
        k3 = 0
        for k1 in range(len(I0_indices)):
            for k2 in range(len(p_indices)):
                image.sf[k3].args =[1e3*zgrid,
                                    1e-3*np.pi/(p_grid[p_indices[k2]]*Lcoh_map[choice_preion][choiceH,p_indices[k2],I0_indices[k1],0,:])
                                    ] # np.pi/Lcoh_map[0][1,p_indices[k2],I0_indices[k1],0,:]
                k3+=1
                

        image.xlabel = r'$z$ [mm]'
        # ax.tick_params(axis="both")
        image.ylabel = r'$|\Delta k / p|$ [1/mm$\cdot$mbar]'
        image.title = r'H'+str(Hgrid[choiceH]) + r', $\eta_0$='+ '{:.0f}'.format(100*preions[choice_preion]) + ' %'
        
        image.ylim_args = [ylims2[k_H][k_preion]]
        
        
        outfpath = os.path.join(OutPath,'Lcoh_onaxis_scaled_'+'H'+str(Hgrid[choiceH])+fname_string)
        image.savefigs_args = [[outfpath + '.pdf'], [outfpath + '.png']]
        image.savefigs_kwargs = [{'bbox_inches' : 'tight'} for k1 in range(2)]
        
        pp.plot_preset(image)


