import RPi.GPIO as GPIO
import time
import numpy as np
from datetime import datetime
import calendar
import Pyro4
import ephem

class MotorControl(object):

    def __init__(self): #constructor
        
        
        self.currentPosition = 0
        self.currentPosition2 = 0
        self.updater = 0
        self.updater2 = 0
    
        self.scan = False #notes if the telescope is currently scanning

        #USER DEFINED: Set relay inputs/outputs
    
        self.firstRelayIn = 6
        self.secondRelayIn = 19
        self.thirdRelayIn = 24
        self.fourthRelayIn = 18
        
        self.motorOneIn = 17
        self.motorTwoIn = 12

        ########################################
        
        self.location = ephem.Observer()
                        
        #USER DEFINED: Set longitude, latitude, and elevation

        self.location.lon = 41.825
        self.location.lat = -88.2439
        self.location.elevation = 230

        #####################################################

        self.location.date = time.strftime("%Y/%m/%d") + " " + time.strftime("%H:%M:%S")
    
        #sets up the Pi GPIO pins to be controllable
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.firstRelayIn, GPIO.OUT)
        GPIO.setup(self.secondRelayIn, GPIO.OUT)
        GPIO.setup(self.thirdRelayIn, GPIO.OUT)
        GPIO.setup(self.fourthRelayIn, GPIO.OUT)
        GPIO.setup(self.motorOneIn, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.motorTwoIn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    #reset the telescope by retracting the motors (separately)
    @Pyro4.expose
    def reset(self):
        #reset first motor
        for n in range(25000):
            GPIO.output(self.firstRelayIn, GPIO.HIGH)
            GPIO.output(self.secondRelayIn, GPIO.LOW)
            time.sleep(0.001)
        GPIO.output(self.firstRelayIn, GPIO.HIGH)
        GPIO.output(self.secondRelayIn, GPIO.HIGH)
        #reset second motor
        for n in range(20000):
            GPIO.output(self.thirdRelayIn, GPIO.HIGH)
            GPIO.output(self.fourthRelayIn, GPIO.LOW)
            time.sleep(0.001)
        GPIO.output(self.fourthRelayIn, GPIO.HIGH)
        GPIO.output(self.thirdRelayIn, GPIO.HIGH)
        
        self.currentPosition = 0
        self.currentPosition2 = 0
        

    #converts inches to position which is then passed to positionMotorMover
    @Pyro4.expose
    def inchesMotorMover(self, inches1, inches2, offset = 0):
        position1 = round(inches1 * 95.47)
        position2 = round(inches2 * 95.47)

        self.positionMotorMover(self, position1, position2, offset = 0)

    #converts radec to altaz to motor position then passes the position to positionMotorMover
    @Pyro4.expose
    def radecMotorMover(self, ra, dec, offset = 0):
        #radec to altaz calculation - revisit to see if this can be replaced with PyEphem's o.alt and o.az attributes
        latitude = self.location.lat
        longitude = self.location.lon
        radegs = ra * 15
        unitime = datetime.utcnow()
        ut = unitime.hour + unitime.minute / 60. + unitime.second / 3600. + offset
        dj2000 = float((calendar.timegm(time.gmtime()) - 946727936.) / 86400.) + offset / 24
        lst = 100.46 + 0.985647 * dj2000 + longitude + (15 * ut)

        while lst < 0:
            lst += 360
        if lst > 360:
            lst -= 360

        while lst > 360:
            lst -= 360
        if lst < 0:
            lst += 360

        hourAngle = lst - radegs

        while hourAngle < 0:
            hourAngle += 360
        if hourAngle > 360:
            hourAngle -= 360

        while hourAngle > 360:
            hourAngle -= 360
        if hourAngle < 0:
            hourAngle += 360

        rightAscension = radegs * (np.pi / 180)
        declination = dec * (np.pi / 180)
        lat = latitude * (np.pi / 180)
        longi = longitude * (np.pi / 180)
        ha = hourAngle * (np.pi / 180)

        sinALT = np.sin(declination) * np.sin(lat) + np.cos(declination) * np.cos(lat) * np.cos(ha)
        radALT = np.arcsin(sinALT)
        ALT = radALT * (180 / np.pi)

        cosELEV = (np.sin(declination) - np.sin(radALT) * np.sin(lat)) / (np.cos(radALT) * np.cos(lat))
        radELEV = np.arccos(cosELEV)
        ELEV = radELEV * (180 / np.pi)
        if np.sin(ha) < 0:
            AZ = ELEV
        else:
            AZ = 360 - ELEV

        print(ALT)
        print(AZ)
        
        #altaz to position converter (presumably)
        a = AZ * (np.pi / 180)
        e = (ELEV + 0.1) * (np.pi / 180)
        x = np.cos(a) * np.sin((np.pi / 2) - e)
        z = np.cos((np.pi / 2) - e)
        alpha = np.arccos(x)
        delta = np.arccos(z / (np.sin(np.arccos(x))))
        alphaindegs = alpha * (180 / np.pi)
        deltaindegs = delta * (180 / np.pi)
        alphadata_extension = [0, 0.8125, 1.875, 2.125, 2.875, 3.375, 4, 4.75, 5.75, 6.5, 7.5, 8.375, 9.5, 10.5, 11.625,
                               12.625, 13.4375, 14.4375]
        alphadata_angle = [23.93, 28.07, 31.26, 34.13, 37.66, 40.89, 43.49, 46.77, 53.45, 58.22, 63.11, 68.13, 74.42,
                           80.98, 87.46, 94.3, 103.54, 105]
        position = np.interp(alphaindegs, alphadata_angle, alphadata_extension)
        deltadata_extension = [0, 1, 2, 3, 4, 5, 6, 7]
        deltadata_angle = [26, 37, 47, 55, 65, 73, 81, 90]
        position2 = np.interp(deltaindegs, deltadata_angle, deltadata_extension)
        positionincounts = round(position * 95.47)
        positionincounts2 = round(position2 * 95.47)



        print(positionincounts)
        print(positionincounts2)

        self.positionMotorMover(self, positionincounts, positionincounts2, offset = 0)

    #moves the motors based on position input; the "final step" for any motor control methods
    @Pyro4.expose
    def positionMotorMover(self, positionincounts, positionincounts2, offset = 0): #creates the function to go to a set length, note: the values have to be in decimal form

        self.currentPosition  # calls variables
        self.currentPosition2
        self.updater = 0
        self.updater2 = 0

        #if there is a problem with the coordinate, return "stop" to let scanning methods know to stop
        if positionincounts > 1340:
            print('Motor 1 cannot extend that far.')
            return "stop"
        elif positionincounts2 > 670: 
            print('Motor 2 cannot extend that far.')
            return "stop"
        elif positionincounts < 0:
            print('Motor 1 cannot retract that far.')
            return "stop"
        elif positionincounts2 < 0:
            print('Motor 2 cannot retract that far.')
            return "stop"

        current_state = 1

        if current_state == 1:
            last_state = current_state - 1
        else:
            last_state = current_state + 1
        if positionincounts > 1340 or positionincounts < 0:
            print('That Right Ascension is too large for the motor.')
        else:
            while (self.currentPosition) != positionincounts: #creates a loop till it gets to the position it needs to be at
                last_state = current_state
                current_state = GPIO.input(self.motorOneIn)
                if (self.currentPosition) < positionincounts: #checks if the motor needs to go in or out
                    if last_state == 0 and current_state == 1: #counting everytime the pulse changes
                        self.currentPosition += 1 #extends the motor
                        self.updater += 1 #update timer
                    if last_state == 1 and current_state == 0:
                        self.currentPosition = self.currentPosition + 1
                        self.updater += 1
                    GPIO.output(self.firstRelayIn, GPIO.LOW)
                    GPIO.output(self.secondRelayIn, GPIO.HIGH)
                    if self.updater == 1: #prints out position at a certain interval and resets the update timer 
                        print('Your current position is (A) in motor 1 ',self.currentPosition)
                        self.updater = 0
                    time.sleep(0.001)
                if (self.currentPosition) > positionincounts:
                    if last_state == 0 and current_state == 1:
                        self.currentPosition -= 1 #retracts the motor
                        self.updater += 1
                    if last_state == 1 and current_state == 0:
                        self.currentPosition -= 1
                        self.updater += 1
                    GPIO.output(self.firstRelayIn, GPIO.HIGH)
                    GPIO.output(self.secondRelayIn, GPIO.LOW)
                    if self.updater == 1:
                        print('Your current position is (B) in motor 1 ',(self.currentPosition))
                        self.updater = 0
                    time.sleep(0.001)
                time.sleep(0.001)
            GPIO.output(self.firstRelayIn, GPIO.LOW)
            GPIO.output(self.secondRelayIn, GPIO.LOW)
            currentPositionininches = positionincounts/95.47
            print('You have reached your position in motor 1')
            print(currentPositionininches)
            current_state2 = 1
            
        
        if current_state2 == 1:
            last_state2 = current_state2 - 1
        else:
            last_state2 = current_state2 + 1
        if positionincounts2 > 670 or positionincounts2 < 0:
            print('That declination is too large for the motor.')
        else:
            while (self.currentPosition2) != positionincounts2: #creates a loop till it gets to the position it needs to be at
                last_state2 = current_state2
                current_state2 = GPIO.input(self.motorTwoIn)
                if (self.currentPosition2) < positionincounts2: #checks if the motor needs to go in or out
                    if last_state2 == 0 and current_state2 == 1: #counting everytime the pulse changes
                        self.currentPosition2 += 1 #extends the motor
                        self.updater2 += 1 #update timer
                    if last_state2 == 1 and current_state2 == 0:
                        self.currentPosition2 = self.currentPosition2 + 1
                        self.updater2 += 1
                    GPIO.output(self.thirdRelayIn, GPIO.LOW)
                    GPIO.output(self.fourthRelayIn, GPIO.HIGH)
                    if self.updater2 == 1: #prints out position at a certain interval and resets the update timer 
                        print('Your current position is (A) in motor 2 ',self.currentPosition2)
                        self.updater2 = 0
                    time.sleep(0.001)
                if (self.currentPosition2) > positionincounts2:
                    if last_state2 == 0 and current_state2 == 1:
                        self.currentPosition2 -= 1 #retracts the motor
                        self.updater2 += 1
                    if last_state2 == 1 and current_state2 == 0:
                        self.currentPosition2 -= 1
                        self.updater2 += 1
                    GPIO.output(self.thirdRelayIn, GPIO.HIGH)
                    GPIO.output(self.fourthRelayIn, GPIO.LOW)
                    if self.updater2 == 1:
                        print('Your current position is (B) in motor 2 ',(self.currentPosition2))
                        self.updater2 = 0
                    time.sleep(0.001)
                time.sleep(0.001)
            GPIO.output(self.thirdRelayIn, GPIO.LOW)
            GPIO.output(self.fourthRelayIn, GPIO.LOW)
            currentPositionininches2 = positionincounts2/95.47
            print('You have reached your position in motor 2')
            print(currentPositionininches2)


        #commented out for now since no data is being recorded
        '''
        rafile = open('/home/pi/Data/ra.txt', 'w')
        rafile.write(str(ra))
        rafile.close()
        decfile = open('/home/pi/Data/dec.txt', 'w')
        decfile.write(str(dec))
        decfile.close()
        pos1file = open('/home/pi/Data/pos1.txt', 'w')
        pos1file.write(str(currentPositionininches))
        pos1file.close()
        pos2file = open('/home/pi/Data/pos2.txt', 'w')
        pos2file.write(str(currentPositionininches2))
        pos2file.close()
        '''

        #if no errors, return nothing
        return ""

    #stops scanning; used in methods to make sure two scans aren't running at once
    @Pyro4.expose
    def stopScan(self):
        print("----- SCAN STOPPED -----")
        self.scan = False

    #scans an object based on its name
    @Pyro4.expose
    def objectScan(self, object, offset = 0):
        if self.scan == True: #stops scanning if telescope is already scanning
            self.stopScan()
            time.sleep(2)
        self.scan = True

        #determines what object PyEphem should calculate based on its name
        o = ""
        if object == "Sun":
            o = ephem.Sun(self.location)
        elif object == "Jupiter":
            o = ephem.Jupiter(self.location)
        elif object == "Moon":
            o = ephem.Moon(self.location)
        o.compute(self.location)

        #loop with conditions that the motorcontrol program hasn't errored and the scan hasn't been stopped
        while self.motorcontrol(self.hoursToDecimal(o.ra.__str__()), self.hoursToDecimal(o.dec.__str__()), offset) != "stop" and self.scan == True:
            #calculate position to point to every second
            self.location.date = time.strftime("%Y/%m/%d") + " " + time.strftime("%H:%M:%S")
            #recompute position of object as it moves
            o.compute(self.location)
            time.sleep(1)
            #motorcontrol statement doesn't need to be called as it's called in the loop condition

        #if the loop breaks due to errors, stop the scan
        self.scan = False



    #scans a constant ra/dec value
    @Pyro4.expose
    def radecScan(self, ra, dec, offset = 0):
        if self.scan == True: #stop scan if telescope is already scanning
            self.stopScan()
            time.sleep(2)
        self.scan = True

        #loop with conditions that the motorcontrol program hasn't errored and the scan hasn't been stopped
        while self.motorcontrol(ra, dec, offset) != "stop" and self.scan == True:
            time.sleep(1)
            #motorcontrol statement doesn't need to be called as it's called in the loop condition

        # if the loop breaks due to errors, stop the scan
        self.scan = False



    #converts the ra/dec hours/mins/secs format output by PyEphem to decimal for motorcontrol() method to use
    def hoursToDecimal(self, str):
        output = 0
        hour = str[:str.index(':')]
        output += float(hour)
        str = str[str.index(':') + 1:]
        minute = str[:str.index(':')]
        output += float(minute)/60.0
        str = str[str.index(':') + 1:]
        second = str
        output += float(second)/3600.0
        return output
