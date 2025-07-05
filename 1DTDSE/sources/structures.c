/**
 * @file structures.c
 * @brief Contains methods operating over defined structures.
 * 
 * @copyright Copyright (c) 2023
 * 
 */
#include "structures.h"

/**
 * @brief Frees up the memory of the output struct.
 * 
 * @param outputs Output structure.
 */
void outputs_destructor(outputs_def *outputs)
{
	free((*outputs).tgrid);
	(*outputs).tgrid = NULL;

	free((*outputs).omegagrid);
	(*outputs).omegagrid = NULL;

	free((*outputs).Efield);
	(*outputs).Efield = NULL;

	free((*outputs).sourceterm);
	(*outputs).sourceterm = NULL;

	free((*outputs).PopTot);
	(*outputs).PopTot = NULL;
	
	free((*outputs).FEfield);
	(*outputs).FEfield = NULL;

	free((*outputs).Fsourceterm);
	(*outputs).Fsourceterm = NULL;

	free((*outputs).FEfieldM2);
	(*outputs).FEfieldM2 = NULL;

	free((*outputs).FsourcetermM2);
	(*outputs).FsourcetermM2 = NULL;
	
	free((*outputs).PopInt);
	(*outputs).PopInt = NULL;
	
	free((*outputs).expval);
	(*outputs).expval = NULL;
}
/**
 * @brief Frees up the memory of the input struct.
 * 
 * @param in Input structure.
 */
void inputs_destructor(inputs_def *in) 
{
	free((*in).psi0);
	(*in).psi0 = NULL;

	free((*in).x);
	(*in).x = NULL;

	free((*in).Efield.tgrid);
	(*in).Efield.tgrid = NULL;
	
	free((*in).Efield.Field);
	(*in).Efield.Field = NULL;
}

/**
 * @brief Frees C matrix.
 * 
 * @param buf Buffer matrix for deletion.
 * @param N_rows Number of rows in the matrix.
 */
void free_mtrx(double ** buf, int N_rows) {
	int i;
	for (i = 0; i < N_rows; i++) {
		free(buf[i]);
		buf[i] = NULL;
	}
	free(buf);
	buf = NULL;

}

/**
 * @brief Returns printing structure for HDF5 writing and sets all prints to 1.
 * 
 * @return output_print_def 
 */
output_print_def Set_all_prints(void)
{
	output_print_def res;

	res.Efield = 1;
	res.FEfield = 1;
	res.sourceterm = 1;
	res.Fsourceterm = 1;
	res.FEfieldM2 = 1;
	res.FsourceTermM2 = 1;
	res.PopTot = 1;
	res.tgrid = 1;
	res.omegagrid = 1;
	res.PopInt = 1;
	res.expval_x = 1;

	return res;
}

/**
 * @brief Returns printing structure for HDF5 writing and sets all prints to 0.
 * 
 * @return output_print_def 
 */
output_print_def Initialise_Printing_struct(void)
{
	output_print_def res;

	res.Efield = 0;
	res.FEfield = 0;
	res.sourceterm = 0;
	res.Fsourceterm = 0;
	res.FEfieldM2 = 0;
	res.FsourceTermM2 = 0;
	res.PopTot = 0;
	res.tgrid = 0;
	res.omegagrid = 0;
	res.PopInt = 0;
	res.expval_x = 0;

	return res;
}
