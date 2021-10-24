from ccmodel.reader import CcsReader

reader = CcsReader("../ccm_test")
test = reader.read("test/test_hh/class_test.ccs")
print(test.file)
for inc in test.includes:
    print(inc.file)
print(test.m_time)
test.ls()
