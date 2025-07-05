General remarks & problems occured along the way
================================================

* PREREQUISITE: MPI version of HDF5 has to be installed (should be on clusters anyway)
    <--- Fortran HDF5 is inherently not thread-safe!!!

* Compilation flags?? (which to select, i.e. -Wall etc.)

* Purpose of 'MKL_LIBS_MT' variable?
    <--- Likely a local variable on Occigen cluster

* CMAKE needs to have packages already installed – may be a drawback!!!

* In ```CMakeLists.txt``` the line ```include_directories(/usr/local/include)```
    has to be there else the system grabs incorrect version of hdf5.mod file 
    incompatible with the compiling language (older version of gfortran vs 
    mpif90 wrapper). This line had to be essentially hardcoded to compile with HDF5
    libraries. 
    <--- Fixed by correctly loading the HDF5 package and including via HDF5_INCLUDE_DIRS

* HDF5_ROOT has to be set to the proper installation of the HDF5. My local previous
    installation was set to conda installation, which didn't include the HDF5 with 
    MPI. The workaround was to set the environment variable as follows:
        ```export HDF5_ROOT=/usr/local/```
    Then it was able to find the proper installation and compile. I just had to 
    set:
        ```find_package(HDF5 REQUIRED COMPONENTS Fortran HL)```
    and then for the target library linking:
        ```target_link_libraries(cuprad_occigen.e fftw3 fftw3_mpi ${HDF5_LIBRARIES})```
    <--- This fix is no longer necessary in the non-Conda env!

* Need to find a way how to link FFTW3 library without giving the explicit path (maybe unavoidable)
    <--- Setting the proper environment variables LIBRARY_PATH

* Problem on Quantum cluster:
    ```Fatal Error: Can't open module file 'linked_list.mod' for reading at (1)```
    Has to be addressed! After a few attempts it compiles OK.
    <--- Addressed by including the file during the compilation

* The makefile is built using the following command:
    ```cmake -D CMAKE_Fortran_COMPILER=mpifort ..```
    <--- Not necessary with proper installation of the packages (non-Conda env).
    * You can enter interactive cmake cofiguration by using `ccmake`

* In order to compile the code using non-GNU standard (flag -std=gnu, -std=2003 etc.),
    several modifications had to be done. First, non-gnu standards do not support
    the following lines:
    ``` REAL (IMAG (Z)) ```, instead they support ```REAL (AIMAG (Z))```.

    Next, the variable buffer is defined as 32-bit float, however it was compared
    with 64-bit float ```0.D0```. Rewriting to ```0.``` fixed the issue.

    Last, the X descriptor was incorrectly written in ```write_listing.f90``` file.
    Instead of ```WRITE(100,'(a,t50,es12.4, x,a)')``` we need to add '1' in front of 
    'x' so the correct form is: ```WRITE(100,'(a,t50,es12.4, 1x,a)')```

* The code must be compiled in the default Mac environment, NOT Conda!!! With 
    the change of the environment the code compiles okay without specifying 
    the compiler explicitly during cmake call, now it is sufficient to compile 
    the code using ```cmake ..```.

* Predefining CMAKE_Fortran_COMPILER is probably a good approach

* Invoking CMake with the following commands yields more information about linking
    cmake -D CMAKE_Fortran_COMPILER=mpifort -D CMAKE_EXPORT_COMPILE_COMMANDS:BOOL=ON -D CMAKE_VERBOSE_MAKEFILE:BOOL=TRUE ..

* **Local environment variables have to be set correctly** otherwise it needs to be
    set manually in CMakeLists. This is the case of the FFTW3 library. One way is
    to set explicitly 
        ```link_directories(/usr/local/lib)```
    or check that the environment variable LIBRARY_PATH is set to a location 
    of FFTW libs. This can be set as follows:
        ```export LIBRARY_PATH=/usr/local/lib```
    To compile the C code, the CPATH has to be set at the following:
        ```CPATH=/usr/local/include```

* Header ```malloc.h``` is deprecated, it is sufficient to use ```stdlib.h```.

* To run the TDSE part of the coupled model, one has to first preprocess the 
  ```results.h5``` file. In the script ```1DTDSE/post_processing/prepare_TDSE.py```, 
  the path to the ```results.h5``` has to be fixed. The Python script then 
  makes a copy (<--- feature to be probably removed later) and writes necessary
  input data information for the TDSE computation. The data is provided in form
  of an ```.inp``` file located inside ```1DTDSE/processing/...```. Then the script ```prepare_TDSE.py``` calls some routines from the 'universal_input' python package provided on Git (it is convenient to include this package in PYTHONPATH env variable).

* To compile the TDSE library as a dynamic library, we must run the following command:
  ```mpicc -fPIC -shared -lhdf5 -lfftw3 -o singleTDSE.so sources/constants.c sources/tools_algorithmic.c sources/tools_MPI-RMA.c sources/tools_hdf5.c sources/tridiag.c sources/tools_fftw3.c sources/structures.c sources/tools.c sources/prop.c sources/singleTDSE.c```

* To compile 1DTDSE with Intel MKL fftw3.h, we need to manually set the environment path CPATH as
  ```export CPATH=${CPATH}:${MKLROOT}/include/fftw```
CPATH may not include the correct path to fftw headers.

* Check the field propagator in ```propagation``` function!!! For electron we have $\exp(-i E x)$.