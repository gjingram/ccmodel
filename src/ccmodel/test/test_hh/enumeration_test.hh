/******************************************************************************
 * Name: enumeration_test.hh
 * Author: Gabriel Ingram
 * Date: 04/14/2021
 *
 * Description:
 * CCModel enumeration test header
 *
 * Changelog:
 * 04/14/2021  Gabriel Ingram  Initial implementation
 *****************************************************************************/

#ifndef ENUMERATION_TEST_HH
#define ENUMERATION_TEST_HH

#include <stdint.h>

enum testEnum1 {
    A = 0,
    B = 1
};

enum class testEnum2 {
    A = 0,
    B = 1,
    C = 2
};

namespace Nest1 {
	enum testEnum3 {
		A1 = 0,
		A2 = 1,
		A3 = 2,
		A4 = 4
	};

	enum class testEnum4 : int32_t {
		A,
		B,
		C
	};
}

#endif
