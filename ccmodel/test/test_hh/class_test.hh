/******************************************************************************
 * Name: class_test.hh
 * Author: Gabriel Ingram
 * Date 04/14/2021
 *
 * Description:
 * CCModel class test header
 *
 * Changelog
 * 04/15/2021  Gabriel Ingram  Original Implementation
 *****************************************************************************/

#ifndef CLASS_TEST_HH
#define CLASS_TEST_HH

#include <vector>
#include <string>
#include <array>
#include <map>


typedef struct {
	double a1;
	float  a2;
	bool   a3;
} TestStruct1;


struct TestStruct2 {
	
	std::string                a1;
	int                        a2;
        std::map<std::string, int> a3;

	TestStruct2();
	TestStruct2(int);
	~TestStruct2();

	double testMethod1();
	double testMethod2(std::string);
	void*  testMethod3(int);

};


class TestClass1 {
	
	public:
	TestClass1();
	TestClass1(double);
	~TestClass1();

	union {
		double u1;
		float  u2;
	};

	enum {
		TEST_ENUM1,
		TEST_ENUM2
	};

	typedef struct tdef_type {
		double s1;
		float  s2;
	} tdef;

	class NestedClass1 {
		public:
		NestedClass1();
		~NestedClass1();

		double n1;

		void testMethod1();
	};

	public:
	std::string           b1;
	std::vector<double>   b2;
	std::array<double, 3> b3;

	void testMethod4();

	private:
	double                t1;
	float                 t2;

	float testMethod5(std::string, std::vector<double>&);

};


class TestClass2 : public TestStruct2, private TestClass1 {

	public:
	TestClass2();
	~TestClass2();

};

#endif
