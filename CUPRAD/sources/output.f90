! There are modules used for saving the ouputs
!
! - "write_output": it saves fields and plasma-density during the propagation 
!
! - "code_continuation_output": it stores the end-plane solution in the form of the code input for possible continuation
!
! - "linked_list_out": it saves the data buffered in the linked list at the end of the code
!
! The original procedures were developed by Stefan Skupin
! The change to HDF5 was designed by Jan Vabek and 
! co-implemented by Jakub Jelinek
!
! see some notes and references on PHDF5 at the end of the file.


!> @brief This module collect all the procedures for storing outputs of the code.
!!
!! @author Jan Vábek
!! @author Stefan Skupin
!! @author Jakub Jelínek
MODULE output
  USE constants
  USE fields
  USE parameters
  USE mpi_stuff
  USE long_step
  USE run_status
  USE normalization
  USE HDF5
  USE HDF5_helper
  USE h5namelist
  USE pre_ionised

  ! for testing
  USE density_module

CONTAINS
  
  SUBROUTINE write_output
    USE fft
    IMPLICIT NONE
    
    ! General purpose variables: looping, dummy variables
    INTEGER(4) k1,k2
    
    ! the kind of this variable has to correspond with the precision stored in HDF5-file
    REAL(4), ALLOCATABLE :: fields_array(:,:,:), plasma_array(:,:,:), rgrid(:), tgrid(:)  
    REAL(4), ALLOCATABLE :: spect_array_1(:),  spect_array_2(:,:), spect_array_3(:,:), spect_array_4(:,:), spect_array_5(:,:) 
    INTEGER(HSIZE_T)               :: r_offset

    INTEGER(4) j,l
    REAL(8) rhotemp,r,mpa
    COMPLEX(8) help
    LOGICAL, SAVE  :: first = .TRUE.
    INTEGER(HID_T) :: file_id       ! File identifier 
    INTEGER(HID_T) :: group_id      ! Group identifier 
    INTEGER(HID_T) :: h5parameters  ! Property list identifier 
    INTEGER(HSIZE_T), DIMENSION(3) :: dims, offset, ccount

    INTEGER(HSIZE_T), DIMENSION(3) :: dims_shape, offset_shape, ccount_shape ! for testing the shape

    INTEGER(HSIZE_T), DIMENSION(2) :: dims_2d, offset_2d, ccount_2d
    INTEGER                        :: error
    LOGICAL                        :: group_status

    CHARACTER(*), PARAMETER :: field_dset_name=       out_grpname//"/output_field"
    CHARACTER(*), PARAMETER :: plasma_dset_name=      out_grpname//"/output_plasma"
    CHARACTER(*), PARAMETER :: spect_1d_dset_name_1=  out_grpname//"/omegagrid"
    CHARACTER(*), PARAMETER :: spect_1d_dset_name_2=  out_grpname//"/spectral_intensity_integrated_over_the_numerical_box"
    CHARACTER(*), PARAMETER :: spect_1d_dset_name_3=  out_grpname//"/spectral_intensity_integrated_over_cylinder_with_radius_rfill"
    CHARACTER(*), PARAMETER :: spect_1d_dset_name_4=  out_grpname//"/spectral_intensity"
    CHARACTER(*), PARAMETER :: spect_1d_dset_name_5=  out_grpname//"/spectral_phase"
    CHARACTER(*), PARAMETER :: zgrid_dset_name =      out_grpname//"/zgrid"
    CHARACTER(*), PARAMETER :: tgrid_dset_name =      out_grpname//"/tgrid"
    CHARACTER(*), PARAMETER :: rgrid_dset_name =      out_grpname//"/rgrid"

    REAL(8) :: local_time_MPI


    ! DENSITY MOD
    REAL  :: density_mod_data(1,dim_r)
      


    ! convert actual electric field into SI units and prepare to write
    allocate(fields_array(dim_r_local,dim_t, 1))
    r_offset = dim_r_start(num_proc)-1
    DO k1=1, dim_r_local
      DO k2=1, dim_t
        fields_array(k1,k2,1) = REAL( efield_factor*REAL( (efield_osc(k2)*e(k2,r_offset+k1)) ) , 4 ) ! SINGLE PRECISION, corresponding H5T_NATIVE_REAL (REAL(.,8) corresponds to H5T_NATIVE_DOUBLE)
      ENDDO
    ENDDO

    ! obtain local time-dependent plasma density (the same procedure as in longstep_rk)
    ! (the computation is redundant, but it's not a critical performance issue, kept as is for clarity)
    allocate(plasma_array(dim_r_local,dim_t,1))
    k1 = 1
    DO l=dim_r_start(num_proc),dim_r_end(num_proc)
      e_2=ABS(e(1:dim_t,l))**2
      e_2KK=e_2**KK
      IF (apply_pre_ionisation) THEN
         rhotemp = initial_electron_density(r,z,l,dim_r_start(num_proc))
      ELSE
         rhotemp = 0.D0
      ENDIF
      rhompi=0.D0
      rho1=0.D0
      rho2=0.D0
      rhoth=0.D0
      rhotr=0.D0
      rhofh=0.D0
      rhoslg2=0.D0
      rhoav=0.D0

      DO j=1,dim_t
         e_2KKm2(j)=rhotemp
         IF (j.NE.dim_t) THEN
            CALL calc_rho(rhotemp,mpa,e_2(j),e_2(j+1),l)
         ENDIF
      ENDDO
      
      plasma_array(k1,:,1) = REAL(plasma_normalisation_factor_m3*e_2KKm2,4) ! SI units
      k1 = k1 + 1

    ENDDO

    ! Calculate dimensions for the field to be preallocated, the offset and the hyperslab size
    dims = (/int(Nz_points,HSIZE_T),int(dim_r,HSIZE_T), int(dim_t,HSIZE_T)/)
    offset = (/int(output_write_count-1,HSIZE_T),int(dim_r_start(num_proc)-1,HSIZE_T),int(0,HSIZE_T)/)
    ccount = (/int(1,HSIZE_T), int(dim_r_local,HSIZE_T) , int(dim_t,HSIZE_T)/)

    dims_shape = (/int(dim_r,HSIZE_T), int(dim_t,HSIZE_T),int(Nz_points,HSIZE_T)/)
    offset_shape = (/int(dim_r_start(num_proc)-1,HSIZE_T),int(0,HSIZE_T), int(output_write_count-1,HSIZE_T) /)
    ccount_shape = (/int(dim_r_local,HSIZE_T), int(dim_t,HSIZE_T), int(1,HSIZE_T)/)

    CALL h5open_f(error) 
    CALL h5pcreate_f(H5P_FILE_ACCESS_F, h5parameters, error) ! create HDF5 access parameters
    CALL h5pset_fapl_mpio_f(h5parameters, MPI_COMM_WORLD, MPI_INFO_NULL, error) ! set parameters for MPI access
    CALL h5fopen_f(main_h5_fname, H5F_ACC_RDWR_F, file_id, error, access_prp = h5parameters ) ! Open collectivelly the file
    CALL h5pclose_f(h5parameters,error) ! close the parameters


    ! The datasets are initiated in the first call of this subroutine, filled in next calls
    IF ( first ) THEN

      ! first = .FALSE.

      !Create group for the output if it does not already exist
      CALL h5lexists_f(file_id, out_grpname, group_status, error)
      IF ( group_status .EQV. .FALSE. ) THEN
        CALL h5gcreate_f(file_id, out_grpname, group_id, error) 
        CALL h5gclose_f(group_id, error)
      ENDIF
          
      ! Create dataset for electric fields and write the first plane
      CALL create_3D_array_real_dset_p(file_id, field_dset_name, fields_array, dims_shape, offset_shape, ccount_shape)

      ! Create dataset for plasma density and write the first plane
      CALL create_3D_array_real_dset_p(file_id, plasma_dset_name, plasma_array, dims_shape, offset_shape, ccount_shape)

      CALL h5fclose_f(file_id,error)

      ! The main process adds units + writes the grids + prepare extendable z-grid
      ! (It's easier to write attributes serially https://forum.hdfgroup.org/t/write-attributes-collectively-in-mpi-run/4902/2)
      IF (my_rank.EQ.0) THEN ! single-write start

        CALL h5fopen_f (main_h5_fname, H5F_ACC_RDWR_F, file_id, error) ! Reopen file.

        CALL h5_add_units_1D(file_id, field_dset_name, '[V/m]') 
	      CALL h5_add_units_1D(file_id, plasma_dset_name, '[m^(-3)]') 

        ! Prepare r- and t-grids in SI units
	      allocate(tgrid(dim_t),rgrid(dim_r))
        DO k1=1, dim_t
          tgrid(k1) = REAL( tps*(tlo+REAL(k1,8)*delta_t) , 4)
        ENDDO
        DO k1=1, dim_r
          rgrid(k1) = REAL( w0m*(REAL(k1-1,8)*delta_r) , 4)
        ENDDO

        CALL create_dset(file_id, rgrid_dset_name, rgrid, dim_r)
        CALL h5_add_units_1D(file_id, rgrid_dset_name, '[m]')
        CALL create_dset(file_id, tgrid_dset_name, tgrid, dim_t)
        CALL h5_add_units_1D(file_id, tgrid_dset_name, '[s]')
        deallocate(tgrid,rgrid)

        ! prepare extendable z-grid
        CALL create_1D_dset_unlimited(file_id, zgrid_dset_name, (/REAL(four_z_Rayleigh*z,4)/), 1) ! the actual z-coordinate in SI units 
        CALL h5_add_units_1D(file_id, zgrid_dset_name, '[m]')


        !! TEST DENSITY MODULATION (same principle, prepare + extend in next iterations)
        DO k1 = 1, dim_r
          density_mod_data(1,k1) = REAL( density_mod(k1), 4 ) !!! SINGLE PRECISION
        ENDDO 
        CALL create_2D_dset_unlimited(file_id, "test_density", density_mod_data, dim_r) 

        CALL h5fclose_f(file_id, error) ! close the file


      ENDIF ! single-writer


    ELSE ! next iterations where fields are already prepared

      ! write electric field
      CALL write_hyperslab_to_dset_p(file_id, field_dset_name, fields_array, offset_shape, ccount_shape)

      ! write plasma density
      CALL write_hyperslab_to_dset_p(file_id, plasma_dset_name, plasma_array, offset_shape, ccount_shape)

      CALL h5fclose_f(file_id,error)

      ! extend z-grid
      IF (my_rank.EQ.0) THEN 
        CALL h5open_f(error)
        CALL h5fopen_f(main_h5_fname, H5F_ACC_RDWR_F, file_id, error)
        ! only z-grid in 1D
        CALL extend_1D_dset_unlimited(file_id, zgrid_dset_name, (/REAL(four_z_Rayleigh*z,4)/),& ! the actual z-coordinate in SI units 
              new_dims=(/int(output_write_count,HSIZE_T)/),  memspace_dims=(/int(1,HSIZE_T)/),&
              offset=(/int(output_write_count-1,HSIZE_T)/), hyperslab_size=(/int(1,HSIZE_T)/))
        
        !! TEST DENSITY MODULATION
        DO k1 = 1, dim_r
          density_mod_data(1,k1) = REAL( density_mod(k1), 4 ) !!! SINGLE PRECISION
        ENDDO 
        CALL extend_2D_dset_unlimited(file_id, "test_density", density_mod_data, & 
                                      new_dims = (/int(output_write_count, HSIZE_T), int(dim_r, HSIZE_T)/), & 
                                      memspace_dims = (/int(1,HSIZE_T), int(dim_r, HSIZE_T)/), & 
                                      offset = (/int(output_write_count-1,HSIZE_T),int(0,HSIZE_T)/), & 
                                      hyperslab_size = (/int(1,HSIZE_T), int(dim_r, HSIZE_T)/))

        CALL h5fclose_f(file_id,error)

      ENDIF ! single-write end
    ENDIF

    ! Deallocate no longer needed arrays
    deallocate(fields_array)
    deallocate(plasma_array)
    CALL h5close_f(error) ! Close fortran H5 interface


    ! Various diagnostics
    !!!!!!!!!!!!!!!!!! TO BE DISCUSSED !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    etemp=CSHIFT(e,dim_t/2-1,1)
    CALL dfftw_execute(plan_spec)
    DO l=dim_r_start(num_proc),dim_r_end(num_proc)
     DO  j=1,dim_th
        help=etemp(j+dim_t/2,l)
        etemp(j+dim_t/2,l)=etemp(j,l)
        etemp(j,l)=help
     ENDDO
    ENDDO

    e_2(1:dim_t)=0.D0
    e_2KKm2(1:dim_t)=0.D0
    DO l=dim_r_start(num_proc),dim_r_end(num_proc)
      r=REAL(l-1)*delta_r
      e_2(1:dim_t)=e_2(1:dim_t)+ABS(etemp(1:dim_t,l))**2*REAL(l-1,8)
      IF (rfil.GT.r) e_2KKm2(1:dim_t)=e_2KKm2(1:dim_t)+ABS(etemp(1:dim_t,l))**2*REAL(l-1,8)
    ENDDO


    CALL MPI_REDUCE(e_2(1:dim_t),e_2KK(1:dim_t),dim_t,MPI_DOUBLE_PRECISION,MPI_SUM,0,MPI_COMM_WORLD,ierr)
    CALL MPI_REDUCE(e_2KKm2(1:dim_t),e_2(1:dim_t),dim_t,MPI_DOUBLE_PRECISION,MPI_SUM,0,MPI_COMM_WORLD,ierr)
    IF (my_rank.EQ.0) THEN
      dims_2d = (/int(Nz_points,HSIZE_T), int(dim_t,HSIZE_T)/)
      offset_2d = (/int(output_write_count-1,HSIZE_T),int(0,HSIZE_T)/)
      ccount_2d = (/int(1,HSIZE_T),int(dim_t,HSIZE_T)/)
      IF ( first ) THEN
        allocate(spect_array_1(1:dim_t),spect_array_2(1,1:dim_t),spect_array_3(1,1:dim_t), &
          spect_array_4(1,1:dim_t),spect_array_5(1,1:dim_t))
      ELSE
        allocate(spect_array_2(1,1:dim_t),spect_array_3(1,1:dim_t), spect_array_4(1,1:dim_t),spect_array_5(1,1:dim_t))
      ENDIF

! local_time_MPI  = MPI_Wtime()
! IF (my_rank.EQ.0) THEN
!   print *, "second data write, file open, only 0th worker:", local_time_MPI - start_time_MPI
! ENDIF  

      CALL h5open_f(error)
      CALL h5fopen_f(main_h5_fname, H5F_ACC_RDWR_F, file_id, error)
      IF ( first ) THEN
        DO j=1,dim_t
          spect_array_1(j) = REAL(k_t*REAL(j-1-dim_th,8)+omega_uppe,4) 
          spect_array_2(1,j) = REAL(e_2KK(j),4)
          spect_array_3(1,j) = REAL(e_2(j),4)
          spect_array_4(1,j) = REAL(ABS(etemp(j,1))**2,4)
          spect_array_5(1,j) = REAL(ATAN2(AIMAG(etemp(j,1)),REAL(etemp(j,1))+1.D-20),4)
        ENDDO
        CALL create_1D_array_real_dset(file_id, spect_1d_dset_name_1, spect_array_1, dim_t)
	      CALL h5_add_units_1D(file_id, spect_1d_dset_name_1, '[?]')
        CALL create_and_preallocate_2D_array_real_dset(file_id, spect_1d_dset_name_2, spect_array_2, dims_2d, offset_2d, ccount_2d)
	      CALL h5_add_units_1D(file_id, spect_1d_dset_name_2, '[arb.u.]')
        CALL create_and_preallocate_2D_array_real_dset(file_id, spect_1d_dset_name_3, spect_array_3, dims_2d, offset_2d, ccount_2d)
        CALL h5_add_units_1D(file_id, spect_1d_dset_name_3, '[arb.u.]')
        CALL create_and_preallocate_2D_array_real_dset(file_id, spect_1d_dset_name_4, spect_array_4, dims_2d, offset_2d, ccount_2d)
        CALL h5_add_units_1D(file_id, spect_1d_dset_name_4, '[arb.u.]')
        CALL create_and_preallocate_2D_array_real_dset(file_id, spect_1d_dset_name_5, spect_array_5, dims_2d, offset_2d, ccount_2d)
        CALL h5_add_units_1D(file_id, spect_1d_dset_name_5, '[arb.u.]')
        deallocate(spect_array_1, spect_array_2, spect_array_3, spect_array_4, spect_array_5)
      ELSE
        DO j=1,dim_t
          spect_array_2(1,j) = REAL(e_2KK(j),4)
          spect_array_3(1,j) = REAL(e_2(j),4)
          spect_array_4(1,j) = REAL(ABS(etemp(j,1))**2,4)
          spect_array_5(1,j) = REAL(ATAN2(AIMAG(etemp(j,1)),REAL(etemp(j,1))+1.D-20),4)
        ENDDO
        CALL write_hyperslab_to_2D_dset(file_id, spect_1d_dset_name_2, spect_array_2, offset_2d, ccount_2d)
        CALL write_hyperslab_to_2D_dset(file_id, spect_1d_dset_name_3, spect_array_3, offset_2d, ccount_2d)
        CALL write_hyperslab_to_2D_dset(file_id, spect_1d_dset_name_4, spect_array_4, offset_2d, ccount_2d)
        CALL write_hyperslab_to_2D_dset(file_id, spect_1d_dset_name_5, spect_array_5, offset_2d, ccount_2d)
        deallocate(spect_array_2, spect_array_3, spect_array_4, spect_array_5)
      ENDIF
      CALL h5fclose_f(file_id, error)
      CALL h5close_f(error) ! close the HDF5 workspace

! local_time_MPI  = MPI_Wtime()
! IF (my_rank.EQ.0) THEN
!   print *, "second data write, file close, only 0th worker:", local_time_MPI - start_time_MPI
! ENDIF  

    ENDIF
    output_write_count = output_write_count + 1 !increase counter in all cases

    IF (first) first = .FALSE.
 
    RETURN
  END SUBROUTINE  write_output

  SUBROUTINE  code_continuation_output
    USE ppt
    USE normalization
    USE HDF5
    USE HDF5_helper
    IMPLICIT  NONE

    INTEGER(4) k,k1,k2
    CHARACTER*10  iz,filename
    INTEGER(HSIZE_T)               :: r_offset
    INTEGER(HID_T) :: file_id       ! File identifier 
    INTEGER(HID_T) :: group_id      ! Group identifier 
    INTEGER(HID_T) :: field_group_id! Field out group identifier
    INTEGER(HID_T) :: h5parameters  ! Property list identifier 
    INTEGER(HSIZE_T), DIMENSION(2) :: dims, offset, ccount
    INTEGER :: error
    LOGICAL :: group_status

    INTEGER(HID_T) :: indexes_group_id
    CHARACTER(*), PARAMETER :: indexes_groupname = outcont_grpname//"/indexes_group"    
    REAL(4), ALLOCATABLE :: real_e(:,:),imag_e(:,:)

    WRITE(iz,920) z
    DO  k=1,10
       IF (iz(k:k).EQ.' ') iz(k:k)='0'
       IF (iz(k:k).EQ.'.') iz(k:k)='_'
    ENDDO
    IF (my_rank.EQ.0) THEN
       filename='non'
       OPEN(unit_logfile,FILE='PROP_RAD.LOG',STATUS='UNKNOWN')
       DO
          READ(unit_logfile,*,END=999) filename
       ENDDO
999    CONTINUE
       CLOSE(unit_logfile)
    ENDIF
    CALL MPI_BCAST(filename,10,MPI_CHARACTER,0,MPI_COMM_WORLD,ierr)
    IF (filename.NE.iz) THEN
       CALL h5open_f(error)
       CALL h5pcreate_f(H5P_FILE_ACCESS_F, h5parameters, error) ! create HDF5 access parameters
       CALL h5pset_fapl_mpio_f(h5parameters, MPI_COMM_WORLD, MPI_INFO_NULL, error) ! set parameters for MPI access
       CALL h5fopen_f(main_h5_fname, H5F_ACC_RDWR_F, file_id, error, access_prp = h5parameters ) ! Open collectivelly the file
       CALL h5pclose_f(h5parameters,error) ! close the parameters

       !Create group for the output if it does not already exist
       CALL h5lexists_f(file_id, out_grpname, group_status, error)
       IF ( group_status .EQV. .FALSE. ) THEN
         CALL h5gcreate_f(file_id, out_grpname, group_id, error) 
       ELSE
         CALL h5gopen_f(file_id, out_grpname, group_id, error)
       ENDIF
       CALL h5lexists_f(file_id, outcont_grpname, group_status, error)
       IF ( group_status.EQV..FALSE.) THEN
         CALL h5gcreate_f(file_id, outcont_grpname, field_group_id, error) 
       ELSE
         CALL h5gopen_f(file_id, outcont_grpname, field_group_id, error)
       ENDIF
       IF(my_rank.EQ.0) THEN
          OPEN(unit_logfile,FILE='PROP_RAD.LOG',STATUS='UNKNOWN',POSITION='APPEND')
          WRITE(unit_logfile,*) iz    
          CLOSE(unit_logfile)
       ENDIF
       CALL create_dset(field_group_id,'num_proc',num_proc)
       CALL create_dset(field_group_id,'dim_t',dim_t)
       CALL create_dset(field_group_id,'dim_r',dim_r)
       CALL create_dset(field_group_id,'rek0',rek0)
       CALL create_dset(field_group_id,'rekp',rekp)
       CALL create_dset(field_group_id,'c3',c3)
       CALL create_dset(field_group_id,'c5',c5)
       CALL create_dset(field_group_id,'gamma1',gamma1)
       CALL create_dset(field_group_id,'gamma2',gamma2)
       CALL create_dset(field_group_id,'muk',muk)
       CALL create_dset(field_group_id,'betainv2KK',beta_inv_2KK)
       CALL create_dset(field_group_id,'KK',KK)
       CALL create_dset(field_group_id,'rho0',rho0)
       CALL create_dset(field_group_id,'nu',nu)
       CALL create_dset(field_group_id,'alpha',alpha)
       CALL create_dset(field_group_id,'alphaquad',alphaquad)
       CALL create_dset(field_group_id,'rhoat_inv',rhoat_inv)
       CALL create_dset(field_group_id,'xdk',xdk)
       CALL create_dset(field_group_id,'tdk',tdk)
       CALL create_dset(field_group_id,'raman',raman)
       CALL create_dset(field_group_id,'omega',omega)
       CALL create_dset(field_group_id,'komega',komega(1:dim_t),dim_t)
       CALL create_dset(field_group_id,'NN',NN)
       CALL create_dset(field_group_id,'eta1',eta1)
       CALL create_dset(field_group_id,'eta2',eta2)
       CALL create_dset(field_group_id,'lt',lt)
       CALL create_dset(field_group_id,'lr',lr)
       CALL create_dset(field_group_id,'proplength',proplength)
       CALL create_dset(field_group_id,'outlength',outlength)
       CALL create_dset(field_group_id,'delta_z',delta_z)
       CALL create_dset(field_group_id,'z',z)
       CALL create_dset(field_group_id,'z_out',z_out)
       CALL create_dset(field_group_id,'rfil',rfil)
       CALL create_dset(field_group_id,'switch_rho',switch_rho)
       CALL create_dset(field_group_id,'switchKerr',switch_dKerr)
       CALL create_dset(field_group_id,'switch_T',switch_T)
       CALL create_dset(field_group_id,'absorb',absorb)
       CALL create_dset(field_group_id,'increase',increase)
       CALL create_dset(field_group_id,'decrease',decrease)
       CALL create_dset(field_group_id,'rhodist',rhodist)
       CALL create_dset(field_group_id,'timelimit',timelimit)
       CALL create_dset(field_group_id,'photenergy',photon_energy)
       CALL create_dset(field_group_id,'pulsedurat',pulse_duration)
       CALL create_dset(field_group_id,'critpower',critical_power)
       CALL create_dset(field_group_id,'beam_waist',beam_waist)
       CALL create_dset(field_group_id,'ionpot',ionisation_potential)
       CALL create_dset(field_group_id,'rescharge',residue_charge)
       CALL create_dset(field_group_id,'n0_indice',n0_indice)
       CALL create_dset(field_group_id,'critdens',critical_density)
       CALL create_dset(field_group_id,'atomdens',atomic_density)
       CALL create_dset(field_group_id,'angmom',angular_momentum)
       CALL create_dset(field_group_id,'finished',finished)
       CALL create_dset(field_group_id,'omega_uppe',omega_uppe)

       ! efield_factor = SQRT(critical_power*1.D9*3.D8*4.D0*PI*1.D-7/(4.D0*PI*beam_waist**2*1.D-4*2.D0*n0_indice))*2.D0 ! normalization factor electric field V/m
       ! defined in the first step

       ALLOCATE(real_e(dim_t,dim_r/num_proc),imag_e(dim_t,dim_r/num_proc))
       r_offset = dim_r/num_proc*my_rank
       DO k1=1, dim_t
         DO k2=1, dim_r/num_proc
            real_e(k1,k2) = REAL(REAL((efield_factor*efield_osc(k2)*e(k1,k2+r_offset))),4)
            imag_e(k1,k2) = REAL(AIMAG((efield_factor*efield_osc(k2)*e(k1,k2+r_offset))),4)
         ENDDO
       ENDDO
       dims = (/int(dim_t,HSIZE_T), int(dim_r,HSIZE_T)/)
       offset = (/int(0,HSIZE_T),int(dim_r/num_proc*my_rank,HSIZE_T)/)
       ccount = (/int(dim_t,HSIZE_T),int(dim_r/num_proc,HSIZE_T)/)
       CALL create_2D_array_real_dset_p(field_group_id, "startfield_r", real_e, dims, offset, ccount)
       CALL create_2D_array_real_dset_p(field_group_id, "startfield_i", imag_e, dims, offset, ccount)
       DEALLOCATE(real_e,imag_e)
       CALL h5gcreate_f(file_id, indexes_groupname, indexes_group_id, error)
       CALL create_dset(indexes_group_id, "r_vector", REAL(xx(1:i_x_max),4), i_x_max)
       CALL create_dset(indexes_group_id, "z_vector", REAL(zz(1:i_z_max),4), i_z_max)
       CALL create_2D_array_real_dset(indexes_group_id, "indexes", REAL(Indice_norm(1:i_x_max, 1:i_z_max),8), i_x_max, i_z_max)
       CALL h5gclose_f(indexes_group_id, error)
       CALL h5gclose_f(field_group_id, error)
       CALL h5gclose_f(group_id, error)
       CALL h5fclose_f(file_id, error)
       CALL h5close_f(error)
    ENDIF

920 FORMAT (F10.6)

    RETURN
  END SUBROUTINE code_continuation_output
  
  SUBROUTINE linked_list_out
    USE linked_list
    USE longstep_vars
    USE HDF5_helper

    IMPLICIT NONE
    
    INTEGER        :: i
    INTEGER(HID_T) :: file_id       ! File identifier 
    INTEGER(HID_T) :: h5parameters  ! Property list identifier 
    INTEGER(HSIZE_T), DIMENSION(2) :: dims, offset, ccount
    INTEGER                        :: error

    CHARACTER(LEN=25) :: fluence_dset_name=longstep_grpname//"/fluence"
    CHARACTER(LEN=23) :: plasma_channel_dset_name=longstep_grpname//"/plasma_channel"
    CHARACTER(LEN=22) :: losses_plasma_dset_name=longstep_grpname//"/losses_plasma"
    CHARACTER(LEN=26) :: losses_ionization_dset_name=longstep_grpname//"/losses_ionization"
    REAL(4), ALLOCATABLE :: fluence_part(:,:)
    REAL(4), ALLOCATABLE :: plasma_channel_part(:,:)
    REAL(4), ALLOCATABLE :: losses_plasma_part(:,:)
    REAL(4), ALLOCATABLE :: losses_ionization_part(:,:)
    TYPE(list_t), POINTER      :: next_fluence_ll
    TYPE(list_t), POINTER      :: next_plasma_channel_ll
    TYPE(list_t), POINTER      :: next_losses_plasma_ll
    TYPE(list_t), POINTER      :: next_losses_ionization_ll
    
    ! Open HDF5 archive collectivelly
    CALL h5open_f(error)
    CALL h5pcreate_f(H5P_FILE_ACCESS_F, h5parameters, error) ! create HDF5 access parameters
    CALL h5pset_fapl_mpio_f(h5parameters, MPI_COMM_WORLD, MPI_INFO_NULL, error) ! set parameters for MPI access
    CALL h5fopen_f(main_h5_fname, H5F_ACC_RDWR_F, file_id, error, access_prp = h5parameters ) ! Open collectivelly the file
    CALL h5pclose_f(h5parameters,error) ! close the parameters
    
    ! Calculate the size of the dataset
    dims = (/int(length_of_linked_list,HSIZE_T),int(dim_r,HSIZE_T)/)
    ALLOCATE(fluence_part(1,dim_r_local))
    ALLOCATE(plasma_channel_part(1,dim_r_local))
    ALLOCATE(losses_plasma_part(1,dim_r_local))
    ALLOCATE(losses_ionization_part(1,dim_r_local))

    DO i=1,length_of_linked_list
      offset = (/int(i-1,HSIZE_T),int(dim_r_start(num_proc)-1,HSIZE_T)/)
      ccount = (/int(1,HSIZE_T), int(dim_r_local,HSIZE_T)/)
      IF (i .EQ. 1) THEN
        fluence_part(1,:) = transfer(list_get(fluence_ll), fluence_part(1,:))   
        next_fluence_ll => list_next(fluence_ll)
        CALL create_2D_array_real_dset_p(file_id, fluence_dset_name, fluence_part, dims, offset, ccount)

        plasma_channel_part(1,:) = transfer(list_get(plasma_channel_ll), plasma_channel_part(1,:))   
        next_plasma_channel_ll => list_next(plasma_channel_ll)
        CALL create_2D_array_real_dset_p(file_id, plasma_channel_dset_name,&
                                        REAL(plasma_normalisation_factor_m3,4)*plasma_channel_part, dims, offset, ccount)
        
        losses_plasma_part(1,:) = transfer(list_get(losses_plasma_ll), losses_plasma_part(1,:))   
        next_losses_plasma_ll => list_next(losses_plasma_ll)
        CALL create_2D_array_real_dset_p(file_id, losses_plasma_dset_name, losses_plasma_part, dims, offset, ccount)
        
        losses_ionization_part(1,:) = transfer(list_get(losses_ionization_ll), losses_ionization_part(1,:))   
        next_losses_ionization_ll => list_next(losses_ionization_ll)
        CALL create_2D_array_real_dset_p(file_id, losses_ionization_dset_name, losses_ionization_part, dims, offset, ccount)
      ELSE
        fluence_part(1,:) = transfer(list_get(next_fluence_ll), fluence_part(1,:))
        CALL write_hyperslab_to_2D_dset(file_id, fluence_dset_name, fluence_part, offset, ccount)
        next_fluence_ll => list_next(next_fluence_ll)
        
        plasma_channel_part(1,:) = transfer(list_get(next_plasma_channel_ll), plasma_channel_part(1,:))   
        CALL write_hyperslab_to_2D_dset(file_id, plasma_channel_dset_name, &
                                        REAL(plasma_normalisation_factor_m3,4)*plasma_channel_part, offset, ccount)
        next_plasma_channel_ll => list_next(next_plasma_channel_ll)
        
        losses_plasma_part(1,:) = transfer(list_get(next_losses_plasma_ll), losses_plasma_part(1,:))   
        CALL write_hyperslab_to_2D_dset(file_id, losses_plasma_dset_name, losses_plasma_part, offset, ccount)
        next_losses_plasma_ll => list_next(next_losses_plasma_ll)
        
        losses_ionization_part(1,:) = transfer(list_get(next_losses_ionization_ll), losses_ionization_part(1,:))  
        CALL write_hyperslab_to_2D_dset(file_id, losses_ionization_dset_name, losses_ionization_part, offset, ccount)
        next_losses_ionization_ll => list_next(next_losses_ionization_ll)
      ENDIF
    END DO
    DEALLOCATE(fluence_part, plasma_channel_part, losses_plasma_part, losses_ionization_part)
    CALL list_free(fluence_ll)
    CALL list_free(plasma_channel_ll)
    CALL list_free(losses_plasma_ll)
    CALL list_free(losses_ionization_ll)
    
    ! Terminate collective access
    CALL h5fclose_f(file_id, error)
    CALL h5close_f(error)

    ! Add units (not implemented for collective access)
      IF (my_rank.EQ.0) THEN ! single-write start
        CALL h5open_f(error)
        CALL h5fopen_f (main_h5_fname, H5F_ACC_RDWR_F, file_id, error) ! Open an existing file.
        CALL h5_add_units_1D(file_id, fluence_dset_name, '[C.U.]') 
	      CALL h5_add_units_1D(file_id, plasma_channel_dset_name, '[m^(-3)]') 
        CALL h5_add_units_1D(file_id, losses_plasma_dset_name, '[C.U.]') 
	CALL h5_add_units_1D(file_id, losses_ionization_dset_name, '[C.U.]')
        CALL h5fclose_f(file_id, error) ! close the file
        CALL h5close_f(error)
      ENDIF 

  END SUBROUTINE linked_list_out

  SUBROUTINE write_extended_dz
    USE longstep_vars
    ! For storing in HDF5
    INTEGER(HID_T)    :: file_id       ! File identifier 
    INTEGER(HID_T)    :: group_id      ! Group identifier 
    INTEGER           :: error         ! hdferr

    CALL h5open_f(error) 
    CALL h5fopen_f (main_h5_fname, H5F_ACC_RDWR_F, file_id, error)
    CALL h5gopen_f(file_id, log_grpname, group_id, error)
    CALL extend_1D_dset_unlimited(group_id, 'zgrid_dz_CU', (/REAL(z,4)/), new_dims=(/int(dz_write_count,HSIZE_T)/), & 
                          memspace_dims=(/int(1,HSIZE_T)/), offset=(/int(dz_write_count-1,HSIZE_T)/), hyperslab_size=(/int(1,HSIZE_T)/))
    CALL extend_1D_dset_unlimited(group_id, 'zgrid_dz_SI', (/REAL(four_z_Rayleigh*z,4)/), new_dims=(/int(dz_write_count,HSIZE_T)/), & 
                          memspace_dims=(/int(1,HSIZE_T)/), offset=(/int(dz_write_count-1,HSIZE_T)/), hyperslab_size=(/int(1,HSIZE_T)/))
    CALL extend_1D_dset_unlimited(group_id, 'dz', (/REAL(delta_z,4)/), new_dims=(/int(dz_write_count,HSIZE_T)/), & 
                          memspace_dims=(/int(1,HSIZE_T)/), offset=(/int(dz_write_count-1,HSIZE_T)/), hyperslab_size=(/int(1,HSIZE_T)/))
    CALL extend_1D_dset_unlimited(group_id, 'maxphase', (/REAL(maxphase,4)/), new_dims=(/int(dz_write_count,HSIZE_T)/), & 
                          memspace_dims=(/int(1,HSIZE_T)/), offset=(/int(dz_write_count-1,HSIZE_T)/), hyperslab_size=(/int(1,HSIZE_T)/))
    CALL h5gclose_f(group_id, error) 
    CALL h5fclose_f(file_id, error)
    CALL h5close_f(error)
    dz_write_count = dz_write_count + 1
  END SUBROUTINE write_extended_dz


END MODULE output



!
!   This implementation almost straightforwadly follows tutorials from HDF5 portal. The only extension is our 3-dimensionality of the code.
!   The code is in a "raw" form, without encapsulating in functions (see comment below).
!   This is a stable version. However, it's probably not the final version. THere rest some serious things to test (row-, column-majorness etc.).
!   We use pre-allocation of the file. The reason is that appending would require chunking, that is a rather advanced HDF5 topic, especially for performance issues.
!   There is need to call some operations collectivelly https://portal.hdfgroup.org/display/HDF5/Collective+Calling+Requirements+in+Parallel+HDF5+Applications
!     - It seems that barriers are induced by these commands.
!     - We encountered a problem when we tried to do single-worker operation before the collective open. Working with one file has to be done with cre if the file is accessed both sequentially and parallelly. We encountered some problems with that, doing collective first and sequential after seems stable.
