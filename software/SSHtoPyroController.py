import sys
import Pyro4
import time

#takes up to two args for multiple uses (object name, radec, etc.)
arg1 = sys.argv[1]
arg2 = sys.argv[2]

#final arg is the function to call
function = sys.argv[3]

#access proxy motorcontroller
proxymotor = Pyro4.core.Proxy("PYRONAME:motorcontroller.server")
proxydata = Pyro4.core.Proxy("PYRONAME:datacontroller.server")

#call the proxy to perform methods based on function
if(function == "countsPoint"):
    print(proxymotor.positionMotorMover(float(arg1), float(arg2)))
elif(function == "reset"):
    proxymotor.reset()
elif(function == "inchesPoint"):
    print(proxymotor.inchesMotorMover(float(arg1), float(arg2)))
elif(function == "raDecScan"):
    print(proxymotor.radecScan(float(arg1), float(arg2)))
elif(function == "objectScan"):
    print(proxymotor.objectScan(arg1))
elif(function == "stop"):
    proxymotor.stopScan()
elif(function == "getOutput"):
    print(proxydata.output())
exit()
