/******************************************************************************
 * Name: namespace_test.hh
 * Author: Gabriel Ingram
 * Date: 04/11/2021
 *
 * Description:
 * CCModel namespace test header
 *
 * Changelog:
 * 04/11/2021  Gabriel Ingram  Initial implementation
 *****************************************************************************/

#ifndef NAMESPACE_TEST_HH
#define NAMESPACE_TEST_HH

namespace {
	// Anonymous namespace
	namespace TestAnonNested1 {
		// TestAnonNested1
	}
}

namespace TestNamespace1 {
	// TestNamespace1
}

namespace TestNested1 {
	// TestNested1
	namespace TestNested2 {
		// TestNested2
	}
}

#endif
