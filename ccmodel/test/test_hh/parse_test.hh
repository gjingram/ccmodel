/******************************************************************
 * Name: parse_test.hh
 * Author: Gabriel Ingram
 * Date: 10/06/2020
 * 
 * Description:
 *  This file has been used to test and verify clang parsing
 *  of ether modules
 * 
 * Changelog:
 * 10/06/2020   Gabriel Ingram  Initial implementation
 * 
 ******************************************************************/

#ifndef PARSE_TEST_HH
#define PARSE_TEST_HH

// System includes
#include <vector>
#include <stdint.h>

// Ether includes
//#include "arch/ether_macros.h"
//#include "arch/data_management/data_pin.h"

//!< An inline ether comment

/*< An ether comment spanning
    multiple lines >*/

enum testEnum1 {
    A = 0,
    B = 1
};

enum class testEnum2 : uint32_t {
    A = 0,
    B = 1
};

double testFunc1(double, float a, int b);
double testFunc1(int, float, double a = 20.0);
double testFunc1(double *, double &);

std::vector<float> var;
static double statVar;
float etherStateVar;

namespace testNamespace1 {
    int var1;
    namespace testNamespace2 {
        int var2;
    }
}

typedef std::vector<double> doubleVec;
using floatVec = std::vector<float>;
namespace ttNamespace1 = testNamespace1::testNamespace2;
using std::vector;
using namespace testNamespace1::testNamespace2;

template<template<class> class O, typename A, size_t n, size_t b = 1, class ...var>
A& testTemplateFunction(A& classIn) { int a = n; return classIn; }

typedef struct {
    double                a1;
    int                   a2;
    std::vector<double *> a3;
} TestCStruct;

struct TestCppStruct {
    double                b1;
    int                   b2;
    std::vector<double *> b3;

    TestCppStruct() {};
    ~TestCppStruct() {};
};

class TestCppClass {

    public:
    TestCppClass() : t(0) {}
    TestCppClass(double) : t(0) {}
    virtual ~TestCppClass() {};

    double testMethod1(TestCppClass &) const;
    virtual void testMethod2(float);
    virtual void testMethod3() = 0;

    private:
    const  double t;
    double testMethod1();

};

template<class A, class B>
class TestTemplateClass1 : public TestCppClass, public TestCppStruct {

    public:
    TestTemplateClass1();
    virtual ~TestTemplateClass1();

    virtual void testMethod3() override;

    template<class T>
    T testMethod4(A&);

    double testMethod5(B&);

};

template<class A>
class TestTemplateClass1<A, std::vector<float>> {

    public:
    TestTemplateClass1();
    virtual ~TestTemplateClass1();

    double test_spec_func();

};

template<class C>
using testPartial = TestTemplateClass1<C, float>;

class TestCppClass2 : public TestTemplateClass1<float, double> {

    public:
    TestCppClass2();
    virtual ~TestCppClass2();

};


#endif
