/******************************************************************************
 * Name: union_test.hh
 * Author: Gabriel Ingram
 * Date 04/15/2021
 *
 * Desciption:
 * CCModel union test header
 *
 * Changelog:
 * 04/15/2021  Gabriel Ingram  Initial implementation
 *****************************************************************************/

#ifndef UNION_TEST_HH
#define UNION_TEST_HH

union testUnion1 {
	double s1;
	float  s2;
	int    s3;
	bool   s4;
};

namespace Nest1 {
	namespace Nest2 {
		static union {
			double s1;
			float  s2;
			int    s3;
			bool   s4;
		};
	}
}

#endif
