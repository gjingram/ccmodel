/******************************************************************************
 * Name: function_test.hh
 * Author: Gabriel Ingram
 * Date: 04/14/2021
 *
 * Description:
 * CCModel function test header
 *
 * Changelong
 * 04/14/2021  Gabriel Ingram  Initial implementation
 *****************************************************************************/

#ifndef FUNCTION_TEST_HH
#define FUNCTION_TEST_HH

#include <vector>

double              testFunction1();
void*               testFunction2(double &);
float               testFunction3(double, float);
void                testFunction3(double *, double **, float&);
std::vector<double> testFunction4(int);
extern void         testFunction5();
static void         testFunction6(double);

extern "C" {
	double testFunction7(float a, float b, float c = 2);
}

namespace Nest1 {
	void testFunction8();
	namespace Nest2 {
		double testFunction9();
	}
}


#endif
