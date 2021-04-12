/******************************************************************************
 * Name: variable_test.hh
 * Author: Gabriel Ingram
 * Date: 04/12/2021
 *
 * Description:
 * CCModel variable test header
 *
 * Changelog:
 * 04/12/20201  Gabriel Ingram  Initial implementation
 *****************************************************************************/

#ifndef VARIABLE_TEST_HH
#define VARIABLE_TEST_HH

#include <vector>
#include <array>

double                           var1;
float                            var2;
std::vector<double>              var3;
void                            *var4;
int                              var5[3];
bool                           **var6;
std::vector<std::vector<double>> var7;
double                           var8[3][3];

namespace {
	float var9;
}

namespace Nest1 {
	namespace Nest2{
		static bool    var10;
		double const   var11 = 1;
		double const  *var12;
		double * const var13 = NULL;
	}
}

#endif
