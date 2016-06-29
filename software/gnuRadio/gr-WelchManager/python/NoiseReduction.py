'''
    Tests whether deltaP = 1/sqrt(nToDo)
    frequency coordinates will be generated by iBin*nyquistfreq/nBin
'''
import numpy as np
import matplotlib.pylab as plt
from welch import welch
from gnuradio import gr, gr_unittest
from gnuradio import blocks
import sys
nf = 1024
nToDo1 = 10
nToDo2 = 100
nToDo3 = 1000
fs = 10000
sigma = .1
nData = nf
def noisegen(nToDo):
    np.random.seed(0)
    realdata = np.random.normal(0,sigma,nToDo*nData)
    imagdata = np.zeros(len(realdata))*1.j
    data = np.add(realdata, imagdata)
    return data
def test(nToDo, noverlap):
    sourcedata = noisegen(nToDo)
    lData = nf * nToDo
    tb = gr.top_block ()
    item_size = np.dtype("complex64").itemsize
    s2v = blocks.stream_to_vector(item_size, lData)
    scale = 'density'
    src = blocks.vector_source_c(sourcedata)
    wel = welch(lData, scale, nf, fs, noverlap)
    dst = blocks.vector_sink_c(nf)
    tb.connect(src,s2v)
    tb.connect(s2v,wel)
    tb.connect(wel,dst)
    tb.run ()
    result = dst.data()
    return result
def testwithavg(nToDo, noverlap):
    sourcedata = noisegen(nToDo)
    nData = nf
    tb = gr.top_block ()
    item_size = np.dtype("complex64").itemsize
    s2v = blocks.stream_to_vector(item_size, nData)
    scale = 'density'
    src = blocks.vector_source_c(sourcedata)
    wel = welch(nData, scale, nf, fs, noverlap)
    dst = blocks.vector_sink_c(nf)
    tb.connect(src,s2v)
    tb.connect(s2v,wel)
    tb.connect(wel,dst)
    tb.run ()
    result = dst.data()
    ravg = np.add(np.zeros(nf),np.zeros(nf)*1j)
    c = 1
    for n in range(0,nToDo):
        ravg = np.add(ravg,result[n*nf:c*nf])
        c = c + 1
    ravg = ravg/nToDo
    return ravg
Test1_1 = testwithavg(nToDo1, 0)
Test1_2 = testwithavg(nToDo2, 0)
Test1_3 = testwithavg(nToDo3, 0)
Test2_1 = test(nToDo1, 0)
Test2_2 = test(nToDo2, 0)
Test2_3 = test(nToDo3, 0)
Test3_1 = test(nToDo1, .5)
Test3_2 = test(nToDo2, .5)
Test3_3 = test(nToDo3, .5)
#nametocall = 'fspectrum'+str(nf)+'.txt'
#freqrange = np.genfromtxt(nametocall)
fn = fs/2
frange1 = 2*np.arange(nf/2)*fn/nf
frange2 = -2*np.arange(nf/2)*fn/nf
frange3 = frange2[::-1]
frange = np.append(frange1,frange3)
print 'Standard Deviation: of Test1_1'
print np.std(Test1_1)
print 'Standard Deviation: of Test1_1 * 1/sqrt(10)'
print np.std(Test1_1)*1/np.sqrt(10)
print 'Standard Deviation: of Test1_2'
print np.std(Test1_2)
print 'Standard Deviation: of Test1_3'
print np.std(Test1_3)
print 'Standard Deviation: of Test2_1'
print np.std(Test2_1)
print 'Standard Deviation: of Test2_2'
print np.std(Test2_2)
print 'Standard Deviation: of Test2_3'
print np.std(Test2_3)
print 'Standard Deviation: of Test1_1 * 1/sqrt(2)'
print np.std(Test1_1)*1/np.sqrt(2)
print 'Standard Deviation: of Test3_1'
print np.std(Test3_1)
print 'Standard Deviation: of Test3_2'
print np.std(Test3_2)
print 'Standard Deviation: of Test3_3'
print np.std(Test3_3)
'''
#np.savetxt('data.txt',Test1_1)
plt.figure(0)
plt.subplot(211)
plt.title('Scipy frequency bin values')
plt.semilogy(freqrange[0],Test1_1[0])
plt.subplot(212)
plt.title('Formulaic frequency bin values')
plt.semilogy(frange[:512],Test1_1[:512],'c')
plt.semilogy(frange[512:],Test1_1[512:],'c')
'''
plt.figure(1)
plt.subplot(221)
plt.title('Test 1: Individual Welch functions, averaged, no overlap')
plt.semilogy(frange[:512],Test1_1[:512],'r', label='10 Sets')
plt.semilogy(frange[:512],Test1_2[:512],'g', label='100 Sets')
plt.semilogy(frange[:512],Test1_3[:512],'c', label='1000 Sets')
plt.semilogy(frange[513:],Test1_1[513:],'r')
plt.semilogy(frange[513:],Test1_2[513:],'g')
plt.semilogy(frange[513:],Test1_3[513:],'c')
plt.legend()
plt.xlim(-5000,5000)
plt.subplot(222)
plt.title('Test 2: Single Welch function, no overlap')
plt.semilogy(frange[:512],Test2_1[:512],'r', label='10 Sets')
plt.semilogy(frange[:512],Test2_2[:512],'g', label='100 Sets')
plt.semilogy(frange[:512],Test2_3[:512],'c', label='1000 Sets')
plt.semilogy(frange[513:],Test2_1[513:],'r')
plt.semilogy(frange[513:],Test2_2[513:],'g')
plt.semilogy(frange[513:],Test2_3[513:],'c')
plt.legend()
plt.xlim(-5000,5000)
plt.subplot(223)
plt.title('Test 3: Single Welch function, 50% overlap')
plt.semilogy(frange[:512],Test3_1[:512],'r', label='10 Sets')
plt.semilogy(frange[:512],Test3_2[:512],'g', label='100 Sets')
plt.semilogy(frange[:512],Test3_3[:512],'c', label='1000 Sets')
plt.semilogy(frange[513:],Test3_1[513:],'r')
plt.semilogy(frange[513:],Test3_2[513:],'g')
plt.semilogy(frange[513:],Test3_3[513:],'c')
plt.legend()
plt.xlim(-5000,5000)
#plt.savefig('NoiseReductionTest.svg')
plt.figure(2)
plt.hist(Test1_1.real,bins=30,color='r')
plt.hist(Test1_2.real,bins=30,color='g')
plt.hist(Test1_3.real,bins=30,color='c')
plt.show()