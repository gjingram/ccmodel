/******************************************************************************
 * Name: templates_test.hh
 * Author: Gabriel Ingram
 * Date 04/16/2021
 *
 * Description:
 * CCModel templates test header
 *
 * Changelog:
 * 04/16/2021  Gabriel Ingram  Original implementation
 *****************************************************************************/

#ifndef TEMPLATES_TEST_HH
#define TEMPLATES_TEST_HH

#include <vector>

template<typename A>
void testFunction1(A&);

template<typename A, typename B>
A& testFunction2(A, B*);

struct TestStruct {};

template<typename A,
template<typename> class B,
class C,
int n,
bool l = true,
typename ...var>
class TestTemplateClass1 : public TestStruct {
	
	public:
	TestTemplateClass1();
	~TestTemplateClass1();

	A       m1;
	B<C>*   m2;
	C&      m3;
	int     m4 = n;
	bool    m5 = l;

};

template<typename A, template<typename> class B>
class TestTemplateClass1<A, B, double, 2> {

	public:
	TestTemplateClass1();
	~TestTemplateClass1();

	template<typename C>
	class NestedTemplateClass {
		public:
		NestedTemplateClass();
		~NestedTemplateClass();

		A    nm1;
		B<A> nm2;
		C    nm3;
	};

};

template<typename A>
class TestTemplateClass2 {
	public:
	TestTemplateClass2();
	~TestTemplateClass2();

	A  tc1;
	A* tc2;

};

template<>
class TestTemplateClass2<double> {
	public:
	TestTemplateClass2();
	~TestTemplateClass2();
};

template<typename A>
class TestTemplateClass1<A, TestTemplateClass2, double, 2> {

	public:
	TestTemplateClass1();
	~TestTemplateClass1();

};

template<typename A, typename B>
class TestTemplateClass3 : public TestTemplateClass2<A> {
	public:
	TestTemplateClass3();
	~TestTemplateClass3();

};

template<typename A>
class TestTemplateClass4 : TestTemplateClass2<float> {
	public:
	TestTemplateClass4();
	~TestTemplateClass4();
};


template<typename A, template<typename> class B>
class TestNestedInheritance : public TestTemplateClass1<A, B, double, 2>::template NestedTemplateClass<A> {
	public:
	TestNestedInheritance();
	~TestNestedInheritance();
};

#endif
