import numpy as np
import os
import time
# import multiprocessing as mp
import shutil
import h5py
import sys
import copy
import units
import mynumerics as mn
import Hfn
import Hfn2

from scipy import integrate


import Hankel_tools
import MMA_administration as MMA


# import mynumerics as mn
import matplotlib.pyplot as plt

import XUV_refractive_index as XUV_index


import plot_presets as pp




# inputs from hdf5-input


gas_type = 'Ar'
XUV_table_type_diffraction = 'NIST' # {Henke, NIST}
XUV_table_type_absorption = 'Henke' # {Henke, NIST} 
apply_diffraction = ['dispersion', 'absorption']

Nr_max = 235 #470; 235; 155-still fine    
Hrange = [16, 18] # [17, 18] # [14, 36] [17, 18] [16, 20] [14, 22]

kr_step = 2 # descending order, the last is "the most accurate"
ko_step = 1

rmax_FF = 8*1e-4
Nr_FF = 50 # 10 # 200
distance_FF = 1.

FF_orders_plot = 4    
Nz_max_sum = 5 # 41

file_CUPRAD = 'results.h5'
file_TDSE = 'results_merged.h5'
out_h5name = 'test_Hankel.h5'


arguments = sys.argv

showplots = not('-nodisplay' in arguments)

if ('-here' in arguments):
    results_path = os.getcwd()
    results_CUPRAD = os.getcwd()
    results_TDSE = os.getcwd()
else:

    results_path = os.path.join("D:\sharepoint", "OneDrive - ELI Beamlines",
                    "data", "Sunrise","tmp","h5debug","TDSEs","t4_tmp")
    
    results_path = os.path.join("D:\sharepoint", "OneDrive - ELI Beamlines",
                    "data", "Sunrise","tmp","h5debug","TDSEs","t1")

    results_path = os.path.join("D:\sharepoint", "OneDrive - ELI Beamlines",
                    "data", "Sunrise","tmp","h5debug","TDSEs","t3mod")  
    
    results_path = os.path.join("D:\sharepoint", "OneDrive - ELI Beamlines",
                    "data", "Sunrise","tmp","h5debug","TDSEs","t2")  
    
    results_path = os.path.join("D:\sharepoint", "OneDrive - ELI Beamlines",
                    "data", "Sunrise","tmp","h5debug","TDSEs","densmod","t1")  



file = "results_TDSEM.h5"
file = "results.h5"

file = os.path.join(results_path,file)



rgrid_FF = np.linspace(0.0, rmax_FF, Nr_FF)


# load data
print('processing:', file)             
with h5py.File(file, 'r') as InpArch:
    # print(InpArch.keys())
    # print('h5path',MMA.paths['CUPRAD_inputs']+'/laser_wavelength')
    omega0 = mn.ConvertPhoton(1e-2*mn.readscalardataset(InpArch,
                                                        MMA.paths['CUPRAD_inputs']+
                                                        '/laser_wavelength','N'),'lambdaSI','omegaau')
    inverse_GV_IR = InpArch[MMA.paths['CUPRAD_logs']+'/inverse_group_velocity_SI'][()]; group_velocity_IR = 1./inverse_GV_IR
    # pressure_mbar = 1e3*InputArchiveCUPRAD['/inputs/medium_pressure_in_bar'][()]
    rho0_init = 1e6 * mn.readscalardataset(InpArch, MMA.paths['CUPRAD_inputs']+
                                           '/calculated/medium_effective_density_of_neutral_molecules','N') # SI
    
    pressure = Hankel_tools.pressure_constructor(InpArch)
    preset_gas = 'vacuum'
    
    
    print(MMA.paths['global_inputs']+'/gas_preset')
    print(InpArch[MMA.paths['global_inputs']].keys())
    xxx = InpArch[MMA.paths['global_inputs']+'/gas_preset'][()]
    # yyy = InpArch[MMA.paths['global_inputs']+'/gas_preset'].decode()
    preset_gas = mn.readscalardataset(InpArch,MMA.paths['global_inputs']+'/gas_preset','S')
    
    effective_IR_refrective_index = inverse_GV_IR*units.c_light
    
    # try:
    #     preset_gas = mn.readscalardataset(InpArch,MMA.paths['global_inputs']+'/gas_preset','S')
    # except:
    #     preset_gas = 'vacuum' 
    
    # pressure = 1.
    # preset_gas = 'vacuum'
    

    
    FSourceTerm =    InpArch[MMA.paths['CTDSE_outputs']+'/FSourceTerm'][:,:,:,0] + \
                  1j*InpArch[MMA.paths['CTDSE_outputs']+'/FSourceTerm'][:,:,:,1]
    ogrid = InpArch[MMA.paths['CTDSE_outputs']+'/omegagrid'][:]
    rgrid_macro = InpArch[MMA.paths['CTDSE_outputs']+'/rgrid_coarse'][:]
    zgrid_macro = InpArch[MMA.paths['CTDSE_outputs']+'/zgrid_coarse'][:]
    
    FSourceTerm_sparse = InpArch[MMA.paths['CTDSE_outputs']+'/FSourceTerm'][:,:,0:-1:2,0] + \
                        1j*InpArch[MMA.paths['CTDSE_outputs']+'/FSourceTerm'][:,:,0:-1:2,1]
  
                        
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.sf[0].args = [ogrid, np.abs(FSourceTerm[0,0,:])]
    image.sf[0].method = plt.semilogy
    pp.plot_preset(image)
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.sf[0].args = [ogrid/omega0, np.abs(FSourceTerm[0,0,:])]
    image.sf[0].method = plt.semilogy
    pp.plot_preset(image)
    
    ko_min = mn.FindInterval(ogrid/omega0, 16)
    ko_max = mn.FindInterval(ogrid/omega0, 20)
    
    # print(type(InputArchiveTDSE))
    # grp =  InputArchiveCUPRAD['/logs']
    # print(type(grp))
    
    omega_au2SI = mn.ConvertPhoton(1.0, 'omegaau', 'omegaSI')
    ogridSI = omega_au2SI * ogrid
    omega0SI = omega_au2SI * omega0
    
    target_static = Hankel_tools.FSources_provider(InpArch[MMA.paths['CTDSE_outputs']+'/zgrid_coarse'][:],
                                                   InpArch[MMA.paths['CTDSE_outputs']+'/rgrid_coarse'][:],
                                                   omega_au2SI*InpArch[MMA.paths['CTDSE_outputs']+'/omegagrid'][:],
                                                   FSource = np.transpose(FSourceTerm,axes=(0,2,1)),
                                                   data_source = 'static',
                                                   ko_min = ko_min,
                                                   ko_max = ko_max)
    
    # target_dynamic = Hankel_tools.FSources_provider(InpArch[MMA.paths['CTDSE_outputs']+'/zgrid_coarse'][:],
    #                                                 InpArch[MMA.paths['CTDSE_outputs']+'/rgrid_coarse'][:],
    #                                                 omega_au2SI*InpArch[MMA.paths['CTDSE_outputs']+'/omegagrid'][:],
    #                                                 h5_handle = InpArch,
    #                                                 h5_path = MMA.paths['CTDSE_outputs']+'/FSourceTerm',
    #                                                 data_source = 'dynamic',
    #                                                 ko_min = ko_min,
    #                                                 ko_max = ko_max)
    
    # target_static_Ar = Hankel_tools.FSources_provider(InputArchiveTDSE['zgrid_coarse'][:],
    #                                                InputArchiveTDSE['rgrid_coarse'][:],
    #                                                omega_au2SI*InputArchiveTDSE['omegagrid'][:],
    #                                                FSource = np.transpose(FSourceTerm,axes=(1,2,0)),
    #                                                data_source = 'static',
    #                                                ko_min = ko_min,
    #                                                ko_max = ko_max)
    
    
    # plane1_dyn = next(target_dynamic.Fsource_plane)
    # plane2_dyn = next(target_dynamic.Fsource_plane)
        
 
    
 
    pf1 = Hankel_tools.get_propagation_pre_factor_function( target_static.zgrid,
                                                            target_static.rgrid,
                                                            target_static.ogrid,
                                                            preset_gas = 'Ar',
                                                            pressure = pressure,
                                                            absorption_tables = 'Henke',
                                                            include_absorption = True,
                                                            dispersion_tables = 'Henke',
                                                            include_dispersion = True,
                                                            effective_IR_refrective_index = effective_IR_refrective_index)[0]
    

    pf2 = Hankel_tools.get_propagation_pre_factor_function( target_static.zgrid,
                                                            target_static.rgrid,
                                                            target_static.ogrid,
                                                            preset_gas = 'Ar',
                                                            pressure = pressure,
                                                            absorption_tables = 'Henke',
                                                            include_absorption = True,
                                                            dispersion_tables = 'Henke',
                                                            include_dispersion = True,
                                                            effective_IR_refrective_index = 1.0)[0]
    
    
    # sys.exit(0)
    
    HL_end_full, HL_cum_full, pf = Hfn2.HankelTransform_long(target_static, # FSourceTerm(r,z,omega)
                              distance_FF, rgrid_FF,
                              preset_gas = preset_gas,
                              pressure = pressure,
                              absorption_tables = 'Henke',
                              include_absorption = True,
                              dispersion_tables = 'Henke',
                              include_dispersion = True,
                              effective_IR_refrective_index = effective_IR_refrective_index,
                              integrator_Hankel = HT.trapezoidal_integrator, # integrate.trapz,
                              integrator_longitudinal = 'trapezoidal',
                              near_field_factor = True,
                              store_cumulative_result = True,
                              frequencies_to_trace_maxima = None,
                              )
    
    
    target_static = Hankel_tools.FSources_provider(InpArch[MMA.paths['CTDSE_outputs']+'/zgrid_coarse'][:],
                                                   InpArch[MMA.paths['CTDSE_outputs']+'/rgrid_coarse'][:],
                                                   omega_au2SI*InpArch[MMA.paths['CTDSE_outputs']+'/omegagrid'][:],
                                                   FSource = np.transpose(FSourceTerm,axes=(0,2,1)),
                                                   data_source = 'static',
                                                   ko_min = ko_min,
                                                   ko_max = ko_max)
    
    HL_end_vac, HL_cum_vac, pf_vac = Hfn2.HankelTransform_long(target_static, # FSourceTerm(r,z,omega)
                              distance_FF, rgrid_FF,
                              preset_gas = preset_gas,
                              pressure = pressure,
                              absorption_tables = 'Henke',
                              include_absorption = True,
                              dispersion_tables = 'Henke',
                              include_dispersion = True,
                              effective_IR_refrective_index = 1.,
                              integrator_Hankel = HT.trapezoidal_integrator, # integrate.trapz,
                              integrator_longitudinal = 'trapezoidal',
                              near_field_factor = True,
                              store_cumulative_result = True,
                              frequencies_to_trace_maxima = None,
                              )
    


    HL_end, HL_cum = HL_end_full, HL_cum_full
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(HL_cum[0].T)]
    image.sf[0].method = plt.pcolormesh
    pp.plot_preset(image)
    
    
    # image.sf[0].args[-1] = np.abs(HL_cum[1].T)
    # pp.plot_preset(image)


    # image.sf[0].args[-1] = np.abs(HL_cum[3].T)
    # pp.plot_preset(image)
    

    # image.sf[0].args[-1] = np.abs(HL_cum[6].T)
    # pp.plot_preset(image)
    

    # image.sf[0].args[-1] = np.abs(HL_cum[9].T)
    # pp.plot_preset(image)    
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'disp'
    image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(HL_end.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'vac'
    image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(HL_end_vac.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'dif'
    image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(HL_end_vac.T-HL_end.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'dif_rel'
    image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(HL_end_vac.T)/np.max(np.abs(HL_end.T))]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    
    # image = pp.figure_driver()
    # image.sf = [pp.plotter() for k1 in range(32)]
    # image.sf[0].args = [target_static.ogrid/omega0SI, rgrid_FF, np.abs(Hankel_long_static_Ar.T)]
    # image.sf[0].method = plt.pcolormesh
    # pp.plot_preset(image)
    
    
    ko_19 = mn.FindInterval(target_static.ogrid/omega0SI, 19)
    pref_val = np.squeeze(np.asarray([pf(k1)[:,ko_19] for k1 in range(len(target_static.zgrid))]))
    pref_val_vac = np.squeeze(np.asarray([pf_vac(k1)[:,ko_19] for k1 in range(len(target_static.zgrid))]))
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'pref mod'
    image.sf[0].args = [target_static.zgrid, target_static.rgrid, np.abs(pref_val.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)


    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'pref phase'
    image.sf[0].args = [target_static.zgrid, target_static.rgrid, np.angle(pref_val.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)


    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = 'pref phase vac'
    image.sf[0].args = [target_static.zgrid, target_static.rgrid, np.angle(pref_val_vac.T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    

    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = "arg(z/z')"
    image.sf[0].args = [target_static.zgrid, target_static.rgrid, np.angle((pref_val/pref_val_vac).T)]
    image.sf[0].method = plt.pcolormesh
    image.sf[0].colorbar.show = True
    pp.plot_preset(image)
    
    
    
    # signal build-up for H19
    ko_19 = mn.FindInterval(target_static.ogrid/omega0SI, 19)
    
    image = pp.figure_driver()
    image.sf = [pp.plotter() for k1 in range(32)]
    image.title = "H19"
    image.sf[0].args = [target_static.zgrid[1:], np.max(np.abs(HL_cum[:,ko_19,:]),axis=1)]
    image.sf[1].args = [target_static.zgrid[1:], np.max(np.abs(HL_cum_vac[:,ko_19,:]),axis=1)]
    pp.plot_preset(image)
    





    # Hankel_long_static_Ar = Hfn2.HankelTransform_long(target_static_Ar, # FSourceTerm(r,z,omega)
    #                           distance_FF, rgrid_FF,
    #                           preset_gas = 'Ar',
    #                           pressure = 1.,
    #                           absorption_tables = 'Henke',
    #                           include_absorption = True,
    #                           dispersion_tables = 'Henke',
    #                           include_dispersion = True,
    #                           effective_IR_refrective_index = 1.,
    #                           integrator_Hankel = integrate.trapz,
    #                           integrator_longitudinal = 'trapezoidal',
    #                           near_field_factor = True,
    #                           store_cumulative_result = False,
    #                           frequencies_to_trace_maxima = None
    #                           )

    # Hankel_long_dynamic = Hfn2.HankelTransform_long(target_dynamic, # FSourceTerm(r,z,omega)
    #                           distance_FF, rgrid_FF,
    #                           preset_gas = preset_gas,
    #                           pressure = pressure,
    #                           absorption_tables = 'Henke',
    #                           include_absorption = True,
    #                           dispersion_tables = 'Henke',
    #                           include_dispersion = True,
    #                           effective_IR_refrective_index = effective_IR_refrective_index,
    #                           integrator_Hankel = integrate.trapz,
    #                           integrator_longitudinal = 'trapezoidal',
    #                           near_field_factor = True,
    #                           store_cumulative_result = False,
    #                           frequencies_to_trace_maxima = None,
    #                           )
    # print(np.array_equal(Hankel_long_dynamic,HL_end))