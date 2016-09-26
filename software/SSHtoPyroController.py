import sys
import Pyro4
import time

#takes up to two args for multiple uses (object name, radec, etc.)
arg1 = sys.argv[1]
arg2 = sys.argv[2]

#final arg is the function to call
function = sys.argv[3]

#access proxy motorcontroller
proxy = Pyro4.core.Proxy("PYRONAME:motorcontroller.server")

#call the proxy to perform methods based on function
if(function == "countsPoint"):
    proxy.positionMotorMover(float(arg1), float(arg2))
elif(function == "reset"):
    proxy.reset()
elif(function == "inchesPoint"):
    proxy.inchesMotorMover(float(arg1), float(arg2))
elif(function == "raDecScan"):
    proxy.radecScan(float(arg1), float(arg2))
elif(function == "objectScan"):
    proxy.objectScan(arg1)
elif(function == "stop"):
    proxy.stopScan()
exit()
