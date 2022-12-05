'''
Self-Replicating Robot System
====================================================================================================================
Author: Vishal Gattani
E-mail: vgattani@umd.edu
--------------------------------------------------------------------------------------------------------------------
Libraries to be installed using the command: $ pip3 install matplotlib numpy pandas plotly chart_studio
--------------------------------------------------------------------------------------------------------------------
'''
#

import platform
print(f'Python version: {platform.python_version()}')
import random
import math
import time
import numpy as np
import pandas as pd
pd.set_option('display.max_columns', None)
import matplotlib.pyplot as plt
import sys
from matplotlib.patches import Rectangle
import os
from _plotly_future_ import v4_subplots
import plotly
import plotly.io as pio
import numpy as np
import chart_studio
import chart_studio.plotly as cspy
import chart_studio.tools as tls
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

username = 'vishalgattani' # your username\n",
api_key = 'WSy2EFPTbxYYm3Rmcx53' # your api key - go to profile > settings > regenerate key\n",
chart_studio.tools.set_credentials_file(username=username, api_key=api_key)


'''
Global Variables
'''
# set random number generator
random.seed()
# global variables
rid = 1
nid = 0
aid = 0
pid = 0
decimalPlaces = 3
# simulation parameters
mc = False
mc_num_steps = 500
numTasksBeforeFail = 5
timesteps = 100				#; % Number of iterations/time-steps that the simulation goes through.
check = input("Enter initial Non-Printable Materials or press enter for default value of 300.0: \n --> ")
if check=="":
    NonPr = 300.0 				#; % The robot system=s starting quantity of nonprintable components.
else:
    NonPr = check

check = input("Enter initial Printable Materials or press enter for default value of 100.0: \n --> ")
if check=="":
    Printable = 100.0 			#; % The robot system’s starting quantity of printable components.
else:
    Printable = check

check = input("Enter initial Raw Materials or press enter for default value of 50.0: \n --> ")
if check=="":
    Materials = 50.0 			#; % The robot system’s starting quantity of raw printing materials.
else:
    Materials = check

check = input("Enter initial Environment Materials or press enter for default value of 500.0: \n --> ")
if check=="":
    Env_Materials = 500.0 		#; % The environment’s quantity of collectable raw printing materials.
else:
    Env_Materials = check

BaseCost_NonPr = 1 			#; % Base robot cost of nonprintable components.
PrintCost_NonPr = 1 		#; % Print capability cost of nonprintable components.
AssembleCost_NonPr = 1 		#; % Assemble capability cost of nonprintable components.
BaseCost_Pr = 2 			#; % Base robot cost of printable components.
PrintCost_Pr = 2 			#; % Print capability cost of printable components.
AssembleCost_Pr = 2 		#; % Assemble capability cost of printable components.
BaseCost_Time = 2 			#; % Base robot cost of build time (in time-steps).
PrintCost_Time = 2 			#; % Print capability cost of build time (in time-steps).
AssembleCost_Time = 2 		#; % Assemble capability cost of build time (in time-steps).
Print_Efficiency = 1.0 		#; % Factor that scales raw printing materials to printable components.
Print_Amount = 1.0 			#; % Amount of raw materials converted per print task.
Collect_Amount = 1.0 		#; % Raw printing materials per collecting robot per timestep.
QualityThreshold = 0.5 		#; % Robots with a quality below this are non-functional.
Quality_incr_Chance = 5.0 	#; % Chance that a new robot’s build quality will increase.
Quality_incr_Lower = 0.01 	#; % Lower bound for quality increase amount.
Quality_incr_Upper = 0.05 	#; % Upper bound for quality increase amount.
Quality_decr_Chance = 50.0 	#; % Chance that a new robot s build quality will decrease.
Quality_decr_Lower = 0.01 	#; % Lower bound for quality decrease amount.
Quality_decr_Upper = 0.25 	#; % Upper bound for quality decrease amount.
RiskAmount_Collect = 1.0 	#; % Risk chance for the collect task type.
RiskAmount_Assemble = 0.1 	#; % Risk chance for the assemble task type.
RiskAmount_Print = 0.1 		#; % Risk chance for the print task type.
RiskQuality_Modifier = 1 	#; % Multiplier for impact of quality defects on risk amount.
RiskFactory_Modifier = 0.2 	#; % Multiplier for impact of factory-made robots on risk amount
RiskThreshold = 3.0
# [replicator,normal,assembler,printer]
cost_Pr = [6,2,4,4]			#; % Total cost printable
cost_NonPr = [3,1,2,2]		#; % Total cost nonprintable

timecost_base = 2			#; % time cost basic
timecost_print = 2			#; % time cost print capability
timecost_assemble = 2		#; % time cost assemble capability

timecost_normal = timecost_base
timecost_replicator = timecost_base+timecost_assemble+timecost_print
timecost_printer = timecost_base+timecost_print
timecost_assembler = timecost_base+timecost_assemble

timecost_repair_base = 1
timecost_repair_normal = timecost_repair_base
timecost_repair_replicator = timecost_repair_base
timecost_repair_printer = timecost_repair_base
timecost_repair_assembler = timecost_repair_base

table_columns = ["Time","NonPr","Printable","Materials","Env_Materials",
                "#Replicator","#Normal","#Assembler","#Printer",
                "#Assembling","#Printing","#Collecting","#Idle","#Repair",
                "#In","#Out",
                "Average Build Quality in-service","Average Build Quality of System",
                "#WasteReplicator","#WasteNormal","#WasteAssembler","#WastePrinter",
                "Environment Exhaust Time", "Printable Exhaust Time",
                "NonPr Exhaust Time","Material Exhaust Time","Average Risk"]

def resetGlobal(t,r,n,a,p):
    global rid,nid,aid,pid,Num_Steps,NonPr,Printable,Materials,Env_Materials
    # global variables
    rid = r
    nid = n
    aid = a
    pid = p
    # simulation parameters
    Num_Steps = 100				#; % Number of iterations/time-steps that the simulation goes through.
    NonPr = 300.0 				#; % The robot system=s starting quantity of nonprintable components.
    Printable = 100.0 			#; % The robot system’s starting quantity of printable components.
    Materials = 50.0 			#; % The robot system’s starting quantity of raw printing materials.
    Env_Materials = 500.0 		#; % The environment’s quantity of collectable raw printing materials.
    timesteps = t

'''
Class::Robot
'''
# robot object
class Robot:
    def __init__(self,type,build_qual,id):
        self.time = 0
        self.type = type
        self.current_task = "idle"
        self.prev_task = "idle"
        self.next_task = ""
        self.id = self.type[0]+str(id)
        self.build_qual = round(build_qual,decimalPlaces)
        self.factory_made = True
        self.tasks_dur = 0
        self.taskindex = 0
        self.previouslyBuilt = ""
        self.prevTaskDur = 0
        self.curr_repair_task_dur = 0
        self.prev_repair_task_dur = 0
        self.factory = False
        self.riskAmount = 0
        self.riskSet = False
        self.numTasksSuccess = 0
        self.numTasksFailed = 0
        self.numTasksPerformed = 0
        self.downTime = 0
        self.failureTimes = [0]
        self.operationalTimes = [0]
        self.operationalTime = 0
        self.MTBF = 0
        self.MTTR = 0
        self.MDT = 0
        self.Aoss = 0
        self.numRepairs = 0
        self.beingBuilt = ""
        self.numTasksBeforeFailure = 2
        self.numTasksRemainingBeforeFailure = 2
        if(self.type == "Replicator"):
            self.tasks = ["Assemble","Print","Collect","Repair"]
            self.beingbuiltlist = []
        if(self.type == "Normal"):
            self.tasks = ["Collect","Repairing"]
        if(self.type == "Assembler"):
            self.tasks = ["Assemble","Collect","Repair"]
            self.beingbuiltlist = []
        if(self.type == "Printer"):
            self.tasks = ["Print","Collect","Repair"]
        self.num_tasks = len(self.tasks)
    # robot methods/functions definitions
    def reduceNumTasksRemainingBeforeFailure(self):
        self.numTasksRemainingBeforeFailure=self.numTasksRemainingBeforeFailure-1
    def resetNumTasksRemainingBeforeFailure(self):
        self.numTasksRemainingBeforeFailure=self.numTasksBeforeFailure
    def setNumTasksBeforeFailure(self,val):
        self.numTasksBeforeFailure = val
    def getNumTasksBeforeFailure(self):
        return self.numTasksBeforeFailure
    def getNumTasksRemainingBeforeFailure(self):
        return self.numTasksRemainingBeforeFailure
    def setNumTasksRemainingBeforeFailure(self,val):
        self.numTasksRemainingBeforeFailure = val
    def set_being_built(self,robottype):
        self.beingBuilt = robottype
    def get_being_built(self):
        return self.beingBuilt
    def set_previously_built(self, val):
        self.previouslyBuilt = val
    def get_previously_built(self):
        return self.previouslyBuilt
    def setNumTasksPerformed(self):
        self.numTasksPerformed = self.numTasksFailed+self.numTasksSuccess
    def getNumTasksPerformed(self):
        return self.numTasksPerformed
    def computeMTBF(self):
        try:
            if(self.operationalTime==0 and self.numTasksFailed>0):
                self.MTBF = math.inf #np.nan
            else:
                self.MTBF = self.operationalTime/self.numTasksFailed
        except:
            if self.getNumTasksPerformed() == 0:
                self.MTBF = math.inf # np.nan
            else:
                self.MTBF = self.operationalTime
    def computeMTTR(self):
        try:
            self.MTTR = self.downTime/self.numRepairs
        except:
            if self.getNumTasksPerformed() == 0:
                self.MTTR = math.inf #np.nan
            elif(self.downTime == 0 or self.numRepairs==0):
                self.MTTR = self.getMTBF()
    def computeMDT(self):
        try:
            self.MDT = self.downTime/self.numTasksFailed
        except:
            if self.getNumTasksPerformed() == 0:
                self.MDT = math.inf #np.nan
            elif(self.downTime == 0):
                self.MDT = math.inf
    def computeAoss(self):
        try:
            if(self.numTasksFailed == 0 and self.downTime == 0):
                self.Aoss =  self.MTBF/(self.MTBF+0)
            else:
                self.Aoss =  self.MTBF/(self.MTBF+self.MDT)
        except:
#             if self.getNumTasksPerformed() == 0:
                self.Aoss = np.nan
    def computeRAM(self):
        self.setNumTasksPerformed()
        self.computeMTBF()
        self.computeMTTR()
        self.computeMDT()
        self.computeAoss()
    def printRAM(self):
        return (f'{self.id} - MTBF:{self.MTBF:.2f}, MTTR:{self.MTTR:.2f}, MDT:{self.MDT:.2f}, Aoss:{self.Aoss}')
    def getMTBF(self):
        return self.MTBF
    def getMTTR(self):
        return self.MTTR
    def getMDT(self):
        return self.MDT
    def getAoss(self):
        return self.Aoss
    def addNumRepairs(self):
        self.numRepairs += 1
    def taskFail(self):
        self.numTasksFailed += 1
    def taskSuccess(self):
        self.numTasksSuccess += 1
    def gettaskFail(self):
        return self.numTasksFailed
    def gettaskSuccess(self):
        return self.numTasksSuccess
    def get_type(self):
        return self.type
    def __str__(self):
        try:
            return str(f'{self.id},{self.current_task},{self.tasks_dur},tp:{self.gettaskSuccess()}')
        except:
            return None
    def set_curr_task(self,tasktype):
        self.current_task = tasktype
        if(self.current_task == "idle"):
            self.tasks_dur = 0
        if(self.current_task == "collecting"):
            self.tasks_dur = 1
        if(self.current_task == "assembling"):
            self.tasks_dur = 2
        if(self.current_task == "printing"):
            self.tasks_dur = 2
        if(self.current_task == "repair"):
            self.failureTimes.append(self.getRobotTime())
            if(self.prev_task == "repair"):
                self.curr_repair_task_dur = self.get_task_dur()
                self.prev_repair_task_dur = self.curr_repair_task_dur
                self.tasks_dur = self.get_prev_task_dur() + 1
            else:
                self.tasks_dur = self.get_prev_task_dur()
            self.curr_repair_task_dur = self.tasks_dur
    def addDownTime(self,duration):
        self.downTime += duration
    def getDownTime(self):
        return self.downTime
    def addUpTime(self):
        self.upTime += 1
    def getUpTime(self):
        return self.upTime
    def resetUpTime(self):
        self.upTime = 0
    def addOperationalTime(self,duration):
        self.operationalTime += duration
    def getOperationalTime(self):
        return self.operationalTime
    def setFactory(self):
        self.factory = True
    def setRobotTime(self,time):
        self.time = time
    def getRobotTime(self):
        return self.time
    def set_prev_task(self,tasktype):
        self.prev_task = tasktype
    def set_next_task(self,tasktype):
        self.next_task = tasktype
    def set_task_dur(self,task_dur):
        self.tasks_dur = task_dur
    def get_task_dur(self):
        return self.tasks_dur
    def get_robot_id(self):
        return self.id
    def get_buid_qual(self):
        return self.build_qual
    def get_curr_task(self):
        return self.current_task
    def get_prev_task(self):
        return self.prev_task
    def get_next_task(self):
        return self.next_task
    def get_task_dur(self):
        return self.tasks_dur
    def get_prev_task_dur(self):
        if(self.get_prev_task() == "idle"):
            return 0
        if(self.get_prev_task() == "collecting"):
            return 1
        if(self.get_prev_task() == "assembling"):
            return 2
        if(self.get_prev_task() == "printing"):
            return 2
        if(self.get_prev_task() == "repair"):
            return self.prev_repair_task_dur
    def setRiskAmount(self,risk):
        self.riskAmount = risk
        if risk>0.0:
            self.riskSet = True
        else:
            self.riskSet = False
    def getRiskAmount(self):
        return self.riskAmount
    def getRisk(self):
        return self.riskSet

'''
Function::Configuration Handler
'''

def configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat):
        n_replicator = 0
        n_normal = 0
        n_assembler = 0
        n_printer = 0

        c_flag = 0
        p_flag = 0
        a_flag = 0
        i_flag = 0
        repair_flag = 0

        useless_c_flag = 0
        useless_p_flag = 0
        useless_a_flag = 0
        useless_r_flag = 0

        tot_build_qual_inservice = 0
        tot_build_qual_inoutservice = 0

        build_quality_list = []

        for i in totlist:
            if(i.get_buid_qual()>=0.5):
                tot_build_qual_inoutservice = tot_build_qual_inoutservice + i.get_buid_qual()
                tot_build_qual_inservice = tot_build_qual_inservice + i.get_buid_qual()
            else:
                tot_build_qual_inoutservice = tot_build_qual_inoutservice + i.get_buid_qual()
            build_quality_list.append(i.get_buid_qual())

        avg_risk = 0
        for i in robotlist:
            if i.get_curr_task()=="collecting":
                c_flag+=1
            elif i.get_curr_task()=="printing":
                p_flag+=1
            elif i.get_curr_task()=="assembling":
                a_flag+=1
            elif i.get_curr_task()=="idle":
                # print(i)
                i_flag+=1
            elif i.get_curr_task()=="repair":
                # print(i)
                repair_flag+=1

            if(checkType(i,"Replicator")):
                n_replicator += 1;
            elif(checkType(i, "Normal")):
                n_normal += 1;
            elif(checkType(i, "Assembler")):
                n_assembler += 1;
            elif(checkType(i, "Printer")):
                n_printer += 1;

            avg_risk += i.getRisk()
        avg_risk = avg_risk/len(robotlist)

        for i in useless:
            if(checkType(i,"Replicator")):
                useless_r_flag += 1;
            elif(checkType(i, "Normal")):
                useless_c_flag += 1;
            elif(checkType(i, "Assembler")):
                useless_a_flag += 1;
            elif(checkType(i, "Printer")):
                useless_p_flag += 1;



        avg_build_qual_inservice = round(tot_build_qual_inservice/len(robotlist),decimalPlaces)
        avg_build_qual_inoutservice = round(tot_build_qual_inoutservice/len(totlist),decimalPlaces)

        neatPrint = False
        if neatPrint:
            print("="*50)
            print(t,":\t\t",len(robotlist),[NonPr,Printable,Materials,Env_Materials])
            print("Time\t\t",t)
            print("#Replicator:\t",n_replicator)
            print("#Normal:\t",n_normal)
            print("#Assembling:\t",n_assembler)
            print("#Printing:\t",n_printer)
            print("#Robots\t\t",len(robotlist))
            print("Materials\t",[NonPr,Printable,Materials,Env_Materials])
            print("#Assembling:\t",a_flag)
            print("#Printing:\t",p_flag)
            print("#Collecting:\t",c_flag)
            print("#Idle:\t\t",i_flag)
            print("#Repair:\t\t",repair_flag)

        ids=[]
        for j in totlist:
            isWaste = False
            if j.build_qual<=QualityThreshold:
                isWaste = True
            ids.append(j.id)

#         if (Env_Materials == 0 and checkENV == 0):
#             checkENV = t
#         if (Printable == 0 and checkPrint == 0):
#             checkPrint = t
#         if (NonPr == 0 and checkNonPr == 0):
#             checkNonPr = t
#         if (Materials <= 1 and checkMat == 0):
#             checkMat = t

        return build_quality_list,[n_replicator,n_normal,n_assembler,n_printer,
        a_flag,p_flag,c_flag,i_flag,repair_flag,
        len(robotlist),len(useless),
        avg_build_qual_inservice,avg_build_qual_inoutservice,
        useless_r_flag,useless_c_flag,useless_a_flag,useless_p_flag,
        checkENV,checkPrint,checkNonPr,checkMat,avg_risk]


'''
Function::Tasks
'''

# print current resources
def printResources():
    print(NonPr,Printable,Materials,Env_Materials)

# check if robot can collect from Env_Materials
def collectCheck(robot):
    global Materials, Env_Materials, Collect_Amount
    if (Env_Materials - Collect_Amount >= 0):
        robot.setRiskAmount(taskRisk(robot))
        return True
    else:
        robot.setRiskAmount(0)
        return False

# task function - collecting
def collecting(robot):
    global Materials, Env_Materials, Collect_Amount, RiskThreshold,mc,numTasksBeforeFail
    robot.set_prev_task(robot.get_curr_task())
    robot.set_curr_task("collecting")
    robot.set_task_dur(1)
    flag = 1
    if not mc:
        if robot.getNumTasksRemainingBeforeFailure()==0:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            Materials = Materials + Collect_Amount
            Env_Materials = Env_Materials - Collect_Amount
            robot.taskSuccess()
            robot.reduceNumTasksRemainingBeforeFailure()
    if mc:
        if robot.getRisk() == False:
            robot.setRiskAmount(taskRisk(robot))
        elif robot.getRiskAmount() > RiskThreshold:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            Materials = Materials + Collect_Amount
            Env_Materials = Env_Materials - Collect_Amount
            robot.taskSuccess()

def assembleCheck(robot,tobuild):
    if(tobuild == "Replicator"):
        i=0
    if(tobuild == "Normal"):
        i=1
    if(tobuild == "Assembler"):
        i=2
    if(tobuild == "Printer"):
        i=3
    if Printable - cost_Pr[i] >= 0 and NonPr - cost_NonPr[i] >= 0:
        if(robot.getRisk() == False):
            robot.setRiskAmount(taskRisk(robot))
        return True
    else:
        robot.setRiskAmount(0)
        return False


def assembling(robot,tobuild):
    global rid,nid,aid,pid,Printable,NonPr,Quality_incr_Chance,Quality_incr_Lower, Quality_incr_Upper,RiskThreshold,mc,numTasksBeforeFail
    if(tobuild == "Replicator"):
        i=0
        taskDur = timecost_replicator
    if(tobuild == "Normal"):
        i=1
        taskDur = timecost_normal
    if(tobuild == "Assembler"):
        i=2
        taskDur = timecost_assembler
    if(tobuild == "Printer"):
        i=3
        taskDur = timecost_printer
    robot.set_prev_task(robot.get_curr_task())
    robot.set_curr_task("assembling")
    robot.set_task_dur(taskDur)
    flag = 1
    if not mc:
        if robot.getNumTasksRemainingBeforeFailure()==0:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            if(robot.type=="Assembler" or robot.type=="Replicator"):
                if(tobuild == "Replicator"):
                    i=0
                    rid = rid+1
                    robotid = rid
                if(tobuild == "Normal"):
                    i=1
                    nid = nid+1
                    robotid = nid
                if(tobuild == "Assembler"):
                    i=2
                    aid = aid+1
                    robotid = aid
                if(tobuild == "Printer"):
                    i=3
                    pid = pid+1
                    robotid = pid
                # subtract resources
                Printable = Printable - cost_Pr[i]
                NonPr = NonPr - cost_NonPr[i]
                robot.beingbuiltlist.append(tobuild[0]+str(robotid))
                robot.set_previously_built(tobuild)
                robot.reduceNumTasksRemainingBeforeFailure()
                return True
        else:
            return False
    if mc:
        if robot.getRisk() == True and robot.get_prev_task()=="assembling":
            robot.setRiskAmount(taskRisk(robot))
        if robot.getRiskAmount() > RiskThreshold:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            if(robot.getRisk() == True and robot.get_task_dur() - 1 == 0):
                robot.setRiskAmount(0)

            if(robot.type=="Assembler" or robot.type=="Replicator"):
                if(tobuild == "Replicator"):
                    i=0
                    rid = rid+1
                    robotid = rid
                if(tobuild == "Normal"):
                    i=1
                    nid = nid+1
                    robotid = nid
                if(tobuild == "Assembler"):
                    i=2
                    aid = aid+1
                    robotid = aid
                if(tobuild == "Printer"):
                    i=3
                    pid = pid+1
                    robotid = pid
                # subtract resources
                Printable = Printable - cost_Pr[i]
                NonPr = NonPr - cost_NonPr[i]
                robot.beingbuiltlist.append(tobuild[0]+str(robotid))
                robot.set_previously_built(tobuild)
                return True
        else:
            robot.set_prev_task(robot.get_curr_task())
            robot.set_curr_task("idle")
            robot.set_task_dur(0)
            robot.setRiskAmount(0)
            return False

def assemble(builder,tobuild):
    global rid,nid,aid,pid,Printable,NonPr,Quality_incr_Chance,Quality_incr_Lower, Quality_incr_Upper, mc
    if(builder.type=="Assembler" or builder.type=="Replicator"):
        if(tobuild == "Replicator"):
            i=0
        if(tobuild == "Normal"):
            i=1
        if(tobuild == "Assembler"):
            i=2
        if(tobuild == "Printer"):
            i=3
        AssemblerQuality = builder.get_buid_qual()
        # robot's build quality
        if not mc:
            RobotQuality = AssemblerQuality
        if mc:
            rand = round(random.uniform(0,1),decimalPlaces)
            if rand > round((1.0 - Quality_incr_Chance/100),decimalPlaces):
                RobotQuality = AssemblerQuality + random.uniform(Quality_incr_Lower, Quality_incr_Upper)
            elif rand < Quality_decr_Chance :
                RobotQuality = AssemblerQuality - random.uniform(Quality_decr_Lower, Quality_decr_Upper)
            else :
                RobotQuality = AssemblerQuality
        newRobot = Robot(tobuild,RobotQuality,builder.beingbuiltlist.pop(0)[1:])
        builder.taskSuccess()
        return newRobot
    else:
        return None


def printCheck(robot):
    if(robot.type=="Replicator" or robot.type=="Printer"):
        global Print_Efficiency, Print_Amount, Materials, Printable
        if Materials - (Print_Efficiency*Print_Amount) > 0:
            return True
        else:
            return False
    else:
        return False

def printing(robot):
    global Print_Efficiency, Print_Amount, Materials, Printable,mc,numTasksBeforeFail
    robot.set_prev_task(robot.get_curr_task())
    robot.set_curr_task("printing")
    robot.set_task_dur(PrintCost_Time)
    flag = 1
    if not mc:
        if robot.getNumTasksRemainingBeforeFailure()==0:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            robot.taskSuccess()
            Materials = Materials - (Print_Efficiency*Print_Amount)
            Printable = Printable + (Print_Efficiency*Print_Amount)
            robot.reduceNumTasksRemainingBeforeFailure()
    if mc:
        if robot.getRisk() == False:
            robot.setRiskAmount(taskRisk(robot))
        if robot.getRiskAmount() > RiskThreshold:
            robot.taskFail()
            flag = 0
            repairing(robot)
        if flag:
            robot.addOperationalTime(robot.get_task_dur())
            if(robot.getRisk() == True and robot.get_task_dur() - 1 == 0):
                robot.taskSuccess()
                robot.setRiskAmount(0)
            Materials = Materials - (Print_Efficiency*Print_Amount)
            Printable = Printable + (Print_Efficiency*Print_Amount)

def repairing(robot):
    global mc
    robot.set_next_task(robot.get_curr_task())
    robot.set_prev_task(robot.get_curr_task())
    repair_task_dur = robot.get_task_dur() # + basecost to repair?
    robot.set_curr_task("repair")
    robot.addNumRepairs()
    robot.set_task_dur(repair_task_dur)
    robot.addDownTime(repair_task_dur)
    if not mc:
        robot.resetNumTasksRemainingBeforeFailure()

def resetTasks(robot):
    robot.set_prev_task(robot.get_curr_task())
    robot.set_task_dur(0)
    robot.set_curr_task("idle")

def checkCurrentTask(robot,current_task):
    return robot.get_curr_task() == current_task
def checkPreviousTask(robot,previous_task):
    return robot.get_prev_task() == previous_task

def checkType(robot,robot_type):
    return robot.get_type() == robot_type



'''
Function::TaskRisk
'''

def taskRisk(robot):
    rand = round(random.uniform(0,1),decimalPlaces)
    if robot.factory == True:
        currTask = robot.get_curr_task()
        if(currTask == "idle"):
            RiskTask_Type = 0
        elif(currTask == "collecting"):
            RiskTask_Type = 1
        elif(currTask == "assembling"):
            RiskTask_Type = 1
        elif(currTask == "printing"):
            RiskTask_Type = 1
        elif(currTask == "repair"):
            RiskTask_Type = 0
        riskTask = (1.0 - robot.get_buid_qual()) * (RiskTask_Type + rand * RiskFactory_Modifier)
#         riskTask = (1.0 - rand) * (RiskTask_Type + (1.0 - robot.get_buid_qual()) * RiskFactory_Modifier)
    else:
        currTask = robot.get_curr_task()
        if(currTask == "idle"):
            RiskTask_Type = 0
        elif(currTask == "collecting"):
            RiskTask_Type = 1
        elif(currTask == "assembling"):
            RiskTask_Type = 1
        elif(currTask == "printing"):
            RiskTask_Type = 1
        elif(currTask == "repair"):
            RiskTask_Type = 0
        riskTask = (1.0 - robot.get_buid_qual()) * (RiskTask_Type + rand * RiskQuality_Modifier)
#         riskTask = (1.0 - rand) * (RiskTask_Type + (1.0 - robot.get_buid_qual()) * RiskQuality_Modifier)
    return riskTask

'''
Function::computeRAMMetrics
'''

def computeRAMMetrics(robotlist):
    MTBFlist = []
    MTTRlist = []
    MDTlist = []
    Aosslist = []
    for robot in robotlist:
        robot.computeRAM()
        if math.isnan(robot.getAoss())==False:
            MTBFlist.append(robot.getMTBF())
            MTTRlist.append(robot.getMTTR())
            MDTlist.append(robot.getMDT())
            Aosslist.append(robot.getAoss())
    MTBFlist=np.array(MTBFlist)
    MTTRlist=np.array(MTTRlist)
    MDTlist=np.array(MDTlist)
    lambda_robots = np.reciprocal(MTBFlist)
    mu_robots = np.reciprocal(MTTRlist)
    MDT_SRRS = sum(np.reciprocal(MDTlist))
    sigma_lambda = sum(lambda_robots)
    pi_lambda = np.prod(lambda_robots)
    sigma_mu = sum(mu_robots)
    pi_mu = np.prod(mu_robots)


    lambda_SRRS = pi_lambda*sigma_mu/pi_mu


#     roundup = 4
#     pi_lambda = round(pi_lambda,roundup)
#     sigma_mu = round(sigma_mu,roundup)
#     pi_mu = round(pi_mu,roundup)
#     if math.isnan(lambda_SRRS):
#         lambda_SRRS = math.inf
#     else:
#         lambda_SRRS = round(lambda_SRRS,roundup)

#     print(f'pi_lambda:{pi_lambda},{type(pi_lambda)}')
#     print(f'sigma_mu:{sigma_mu},{type(sigma_mu)}')
#     print(f'pi_mu:{pi_mu},{type(pi_mu)}')
#     print(f'lambda_SRRS:{lambda_SRRS},{type(lambda_SRRS)}')

    mu_SRRS = sigma_mu
    MTBF_SRRS = 1/lambda_SRRS
    MTTR_SRRS= 1/mu_SRRS
    try:
        Aoss_SRRS = MTBF_SRRS/(MTBF_SRRS+MDT_SRRS)
    except:
        Aoss_SRRS = np.nan
#     print(f'MTBF_SRRS:{MTBF_SRRS}')
#     print(f'MTTR_SRRS:{MTTR_SRRS}')
#     print(f'MDT_SRRS:{MDT_SRRS}')
#     print(f'Aoss_SRRS:{Aoss_SRRS}')

    return MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS


def CHO(timesteps,df,init_build_qual,printRAMmetrics=True,mc=False):
    global numTasksBeforeFail
    resetGlobal(timesteps,1,0,0,0)
    robot = Robot("Replicator",init_build_qual,rid)
    robot.setFactory()
    totlist = [robot]
    robotlist = [robot]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0

    for t in range(0,timesteps):
        for i in range(len(robotlist)):
            # assign risks for tasks
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # IDLE
            if(robotlist[i].get_curr_task()=="idle"):
                # Replicator
                if(robotlist[i].type == "Replicator"):
                    if(assembleCheck(robotlist[i],"Normal")):
                        isAssembling = assembling(robotlist[i],"Normal")
                    elif(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Normal
                elif(robotlist[i].type == "Normal"):
                    if (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
            # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of replicator in CHO
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Replicator"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Normal")):
                        assembling(robotlist[i],"Normal")
                    elif(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of normal in CHO
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Normal"):
                    if(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Replicator
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Replicator"):
                    # check if it can keep assembling next time step
                    if(assembleCheck(robotlist[i],"Normal")):
                        isAssembling = assembling(robotlist[i],"Normal")
                    elif(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                    # it enters this loop only when it has to pop a new robot
                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        newbot = assemble(robotlist[i],"Normal")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if(newbot.type == "Normal"):
                                canCollect = collectCheck(newbot)
                                if canCollect:
                                    collecting(newbot)
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)
                # Normal
                elif(robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    if(canCollect):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t

#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)



        #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)

    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def DHO(timesteps,df,init_build_qual):
    resetGlobal(timesteps,1,0,0,0)
    robot = Robot("Replicator",init_build_qual,rid)
    robot.setFactory()
    totlist = [robot]
    robotlist = [robot]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0
    for t in range(0,timesteps):

        for i in range(len(robotlist)):
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # IDLE
            if(robotlist[i].current_task=="idle"):

                # Replicator
                if(robotlist[i].type == "Replicator"):
                    if(assembleCheck(robotlist[i],"Replicator")):
                        assembling(robotlist[i],"Replicator")
                    elif(printCheck(robotlist[i])):
                        printing(robotlist[i])
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Normal
                elif(robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    # print(t,robotlist[i].id,canCollect)
                    if canCollect:
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
         # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of replicator in DHO
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Replicator"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Replicator")):
                        assembling(robotlist[i],"Replicator")
                    elif(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    elif(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)

            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Replicator
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Replicator"):
                    # check if it can keep assembling next time step
                    if(assembleCheck(robotlist[i],"Replicator")):
                        isAssembling = assembling(robotlist[i],"Replicator")
                    elif(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        newbot = assemble(robotlist[i],"Replicator")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if(newbot.type == "Replicator"):
                                if(assembleCheck(newbot,"Replicator")):
                                    assembling(newbot,"Replicator")
                                elif(printCheck(robotlist[i])):
                                    printing(robotlist[i])
                                elif(collectCheck(robotlist[i])):
                                    collecting(robotlist[i])
                                else:
                                    newbot.set_prev_task(robotlist[i].get_curr_task())
                                    newbot.set_task_dur(0)
                                    newbot.set_curr_task("idle")
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t
#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)

         #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)


    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def HHO(timesteps,df,init_build_qual):
    resetGlobal(timesteps,1,0,0,0)
    robot = Robot("Replicator",init_build_qual,rid)
    robot.setFactory()
    totlist = [robot]
    robotlist = [robot]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0

    for t in range(0,timesteps):
        for i in range(len(robotlist)):
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # IDLE
            if(robotlist[i].current_task=="idle"):
                # Replicator
                if(robotlist[i].type == "Replicator"):
                    if (robotlist[i].get_previously_built() == ""):
                        if (assembleCheck(robotlist[i],"Replicator")):
                            isAssembling = assembling(robotlist[i], "Replicator")
                        elif (assembleCheck(robotlist[i],"Normal")):
                            isAssembling = assembling(robotlist[i], "Normal")
                        elif (printCheck(robotlist[i])):
                            printing(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")
                    else:
                        if (assembleCheck(robotlist[i],"Normal") and robotlist[i].get_previously_built() == "Replicator"):
                            isAssembling=assembling(robotlist[i], "Normal")
                        elif (assembleCheck(robotlist[i],"Replicator") and robotlist[i].get_previously_built() == "Normal"):
                            isAssembling=assembling(robotlist[i], "Replicator")
                        elif (printCheck(robotlist[i])):
                            printing(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")

                # Normal
                elif(robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    # print(t,robotlist[i].id,canCollect)
                    if canCollect:
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
         # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of replicator in HHO
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Replicator"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Replicator") and robotlist[i].get_previously_built() == "Normal"):
                        assembling(robotlist[i],"Replicator")
                    elif(nextTask=="assembling" and assembleCheck(robotlist[i],"Normal") and robotlist[i].get_previously_built() == "Replicator"):
                        assembling(robotlist[i],"Normal")
                    elif(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    elif(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of normal in HHO
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Normal"):
                    if(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)

            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Normal
                elif (robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    if (canCollect):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

                # Replicator
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Replicator"):
                    # check if it can keep assembling next time step
                    if (assembleCheck(robotlist[i],"Normal") and robotlist[i].get_previously_built() == "Replicator"):
                        isAssembling=assembling(robotlist[i], "Normal")
                    elif (assembleCheck(robotlist[i],"Replicator") and robotlist[i].get_previously_built() == "Normal"):
                        isAssembling=assembling(robotlist[i], "Replicator")
                    elif (printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        if (robotlist[i].get_previously_built() == "Normal"):
                            newbot = assemble(robotlist[i], "Replicator")
                        elif (robotlist[i].get_previously_built() == "Replicator"):
                            newbot = assemble(robotlist[i], "Normal")
                        else:
                            newbot = assemble(robotlist[i], "Replicator")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if (newbot.type == "Normal"):
                                canCollect = collectCheck(newbot)
                                if canCollect:
                                    collecting(newbot)
                            if(newbot.type == "Replicator"):
                                if (newbot.get_previously_built() == ""):
                                    if (assembleCheck(robotlist[i],"Replicator")):
                                        isAssembling = assembling(newbot, "Replicator")
                                    elif (assembleCheck(robotlist[i],"Normal")):
                                        isAssembling = assembling(newbot, "Normal")
                                    elif (printCheck(newbot)):
                                        printing(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                                else:
                                    if (assembleCheck(robotlist[i],"Normal") and newbot.get_previously_built() == "Replicator"):
                                        assembling(newbot, "Normal")
                                    elif (assembleCheck(robotlist[i],"Replicator") and newbot.get_previously_built() == "Normal"):
                                        assembling(newbot, "Replicator")
                                    # checking if robot can collect
                                    elif (printCheck(newbot)):
                                        printing(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t
#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)

         #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)


    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def CHE(timesteps,df,init_build_qual):
    resetGlobal(timesteps,0,0,1,1)
    robot1 = Robot("Printer",init_build_qual,pid)
    robot2 = Robot("Assembler",init_build_qual,aid)
    totlist = [robot1,robot2]
    robotlist = [robot1,robot2]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0

    for t in range(0,timesteps):
        for i in range(len(robotlist)):
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # if idle
            if(robotlist[i].get_curr_task()=="idle"):
                # If idle and Replicator
                if(robotlist[i].type == "Replicator"):
                    if(assembleCheck(robotlist[i],"Normal")):
                        isAssembling = assembling(robotlist[i],"Normal")
                    elif(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # if idle and Normal
                elif(robotlist[i].type == "Normal"):
                    if (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # if idle and printer
                elif(robotlist[i].type == "Printer"):
                    if(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # if idle and assembler
                elif(robotlist[i].type == "Assembler"):
                    if(assembleCheck(robotlist[i],"Normal")):
                        isAssembling = assembling(robotlist[i],"Normal")
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")


            # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of assembler in CHE
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Assembler"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Normal")):
                        assembling(robotlist[i],"Normal")
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of printer in CHE
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Printer"):
                    if(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of normal in CHE
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Normal"):
                    if(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)

            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Assembler
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Assembler"):
                    # check if it can keep assembling next time step
                    if(assembleCheck(robotlist[i],"Normal")):
                        isAssembling = assembling(robotlist[i],"Normal")
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                    # it enters this loop only when it has to pop a new robot
                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        newbot = assemble(robotlist[i],"Normal")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if(newbot.type == "Normal"):
                                canCollect = collectCheck(newbot)
                                if canCollect:
                                    collecting(newbot)
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)
                # Printer
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Printer"):
                    if(printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Normal
                elif(robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    if(canCollect):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t

#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)

        #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)


    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def DHE(timesteps,df,init_build_qual):
    resetGlobal(timesteps,0,0,1,1)
    robot1 = Robot("Printer",init_build_qual,pid)
    robot2 = Robot("Assembler",init_build_qual,aid)
    totlist = [robot1,robot2]
    robotlist = [robot1,robot2]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0
    for t in range(0,timesteps):
        for i in range(len(robotlist)):
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # IDLE
            if(robotlist[i].current_task=="idle"):
                # if idle and printer
                if (robotlist[i].type == "Printer"):
                    if (printCheck(robotlist[i])):
                        printing(robotlist[i])
                    elif (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # if idle and assembler
                elif (robotlist[i].type == "Assembler"):
                    if (robotlist[i].get_previously_built() == ""):
                        if (assembleCheck(robotlist[i],"Assembler")):
                            isAssembling = assembling(robotlist[i], "Assembler")
                        elif (assembleCheck(robotlist[i],"Printer")):
                            isAssembling = assembling(robotlist[i], "Printer")
                        elif (collectCheck(robotlist[i])):
                            collecting(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")
                    else:
                        if (assembleCheck(robotlist[i],"Printer") and robotlist[i].get_previously_built() == "Assembler"):
                            isAssembling = assembling(robotlist[i], "Printer")
                        elif (assembleCheck(robotlist[i],"Assembler") and robotlist[i].get_previously_built() == "Printer"):
                            isAssembling = assembling(robotlist[i], "Assembler")
                        elif (collectCheck(robotlist[i])):
                            collecting(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")
            # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of assembler in DHE
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Assembler"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Assembler") and robotlist[i].get_previously_built() == "Printer"):
                        assembling(robotlist[i],"Assembler")
                    elif(nextTask=="assembling" and assembleCheck(robotlist[i],"Printer") and robotlist[i].get_previously_built() == "Assembler"):
                        assembling(robotlist[i],"Printer")
                    elif(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of printer in DHE
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Printer"):
                    if(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Printer
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Printer"):
                    if(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Assembler
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Assembler"):
                    # check if it can keep assembling next time step
                    if (assembleCheck(robotlist[i],"Assembler") and robotlist[i].get_previously_built() == "Printer"):
                        isAssembling=assembling(robotlist[i], "Assembler")
                    elif (assembleCheck(robotlist[i],"Printer") and robotlist[i].get_previously_built() == "Assembler"):
                        isAssembling=assembling(robotlist[i], "Printer")
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                    # it enters this loop only when it has to pop a new robot
                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        if (robotlist[i].get_previously_built() == "Printer"):
                            newbot = assemble(robotlist[i], "Assembler")
                        elif (robotlist[i].get_previously_built() == "Assembler"):
                            newbot = assemble(robotlist[i], "Printer")
                        else:
                            newbot = assemble(robotlist[i], "Assembler")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if(newbot.type == "Assembler"):
                                if (newbot.get_previously_built() == ""):
                                    if (assembleCheck(robotlist[i],"Assembler")):
                                        isAssembling = assembling(newbot, "Assembler")
                                    elif (assembleCheck(robotlist[i],"Printer")):
                                        isAssembling = assembling(newbot, "Printer")
                                    # checking if robot can collect
                                    elif (collectCheck(newbot)):
                                        collecting(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                                else:
                                    if (assembleCheck(robotlist[i],"Printer") and newbot.get_previously_built() == "Assembler"):
                                        assembling(newbot, "Printer")
                                    elif (assembleCheck(robotlist[i],"Assembler") and newbot.get_previously_built() == "Printer"):
                                        assembling(newbot, "Assembler")
                                    # checking if robot can collect
                                    elif (collectCheck(newbot)):
                                        collecting(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t
#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)

         #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)

    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def HHE(timesteps,df,init_build_qual):
    resetGlobal(timesteps,0,0,1,1)
    robot1 = Robot("Printer",init_build_qual,pid)
    robot2 = Robot("Assembler",init_build_qual,aid)
    totlist = [robot1,robot2]
    robotlist = [robot1,robot2]
    useless = []
    # number of bots working
    listnumCollecting = []
    listnumPrinting = []
    listnumAssembling = []
    # use lists
    tcoordslist = []
    rcoordslist = []
    wastecoordslist = []
    t_build_quality_list = []
    #Lists used for visualization
    checkENV = 0
    checkPrint = 0
    checkNonPr = 0
    checkMat = 0

    for t in range(0,timesteps):
        for i in range(len(robotlist)):
            robotlist[i].setRobotTime(t)
            robotlist[i].setNumTasksBeforeFailure(numTasksBeforeFail)
            # IDLE
            if(robotlist[i].current_task=="idle"):
                # If idle and printer
                if (robotlist[i].type == "Printer"):
                    if (printCheck(robotlist[i])):
                        printing(robotlist[i])
                    elif (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # If idle and assembler
                if (robotlist[i].type == "Assembler"):
                    if (robotlist[i].get_previously_built() == ""):
                        if (assembleCheck(robotlist[i],"Normal")):
                            isAssembling = assembling(robotlist[i], "Normal")
                        elif (assembleCheck(robotlist[i],"Assembler")):
                            isAssembling = assembling(robotlist[i], "Assembler")
                        elif (assembleCheck(robotlist[i],"Printer")):
                            isAssembling = assembling(robotlist[i], "Printer")
                        elif (collectCheck(robotlist[i])):
                            collecting(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")
                    else:
                        if (robotlist[i].get_previously_built() == "Assembler" and assembleCheck(robotlist[i],"Printer")):
                            isAssembling = assembling(robotlist[i], "Printer")
                        elif (robotlist[i].get_previously_built() == "Printer" and assembleCheck(robotlist[i],"Normal")):
                            isAssembling = assembling(robotlist[i], "Normal")
                        elif (robotlist[i].get_previously_built() == "Normal" and assembleCheck(robotlist[i],"Assembler")):
                            isAssembling = assembling(robotlist[i], "Assembler")
                        elif (collectCheck(robotlist[i])):
                            collecting(robotlist[i])
                        else:
                            robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                            robotlist[i].set_task_dur(0)
                            robotlist[i].set_curr_task("idle")

                # If idle and collector
                if (robotlist[i].type == "Normal"):
                    if (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
         # REPAIR
            elif(robotlist[i].get_curr_task()=="repair"):
                nextTask = robotlist[i].get_next_task()
                # tasks of assembler in HHE
                if(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Assembler"):
                    if(nextTask=="assembling" and assembleCheck(robotlist[i],"Assembler") and robotlist[i].get_previously_built() == "Printer"):
                        assembling(robotlist[i],"Assembler")
                    elif(nextTask=="assembling" and assembleCheck(robotlist[i],"Printer") and robotlist[i].get_previously_built() == "Normal"):
                        assembling(robotlist[i],"Printer")
                    elif(nextTask=="assembling" and assembleCheck(robotlist[i],"Normal") and robotlist[i].get_previously_built() == "Assembler"):
                        assembling(robotlist[i],"Normal")
                    elif(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # tasks of printer in HHE
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Printer"):
                    if(nextTask=="printing" and printCheck(robotlist[i])):
                        printing(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                elif(robotlist[i].get_task_dur() - 1 == 0 and robotlist[i].type == "Normal"):
                    if(nextTask=="collecting" and collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                else:
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)

            # NOT IDLE
            else:
                # reduce task duration every time step
                if(robotlist[i].tasks_dur - 1 != 0):
                    robotlist[i].set_task_dur(robotlist[i].get_task_dur() - 1)
                # Normal
                elif (robotlist[i].type == "Normal"):
                    canCollect = collectCheck(robotlist[i])
                    if (canCollect):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Printer
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Printer"):
                    if(printCheck(robotlist[i])):
                        isPrinting = printing(robotlist[i])
                    elif(collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")
                # Replicator
                elif(robotlist[i].tasks_dur - 1 == 0 and robotlist[i].type == "Assembler"):
                    if (assembleCheck(robotlist[i],"Normal") and robotlist[i].get_previously_built() == "Printer"):
                        assembling(robotlist[i], "Normal")
                    elif (assembleCheck(robotlist[i],"Printer") and robotlist[i].get_previously_built() == "Assembler"):
                        assembling(robotlist[i], "Printer")
                    elif (assembleCheck(robotlist[i],"Assembler") and robotlist[i].get_previously_built() == "Normal"):
                        assembling(robotlist[i], "Assembler")
                    elif (collectCheck(robotlist[i])):
                        collecting(robotlist[i])
                    else:
                        robotlist[i].set_prev_task(robotlist[i].get_curr_task())
                        robotlist[i].set_task_dur(0)
                        robotlist[i].set_curr_task("idle")

                    if(len(robotlist[i].beingbuiltlist)>0 and robotlist[i].get_prev_task()=="assembling"):
                        # Build a new robot in a fixed pattern
                        if (robotlist[i].get_previously_built() == ""):
                            newbot = assemble(robotlist[i], "Normal")
                        elif (robotlist[i].get_previously_built() == "Normal"):
                            newbot = assemble(robotlist[i], "Printer")
                        elif (robotlist[i].get_previously_built() == "Printer"):
                            newbot = assemble(robotlist[i], "Assembler")
                        elif (robotlist[i].get_previously_built() == "Assembler"):
                            newbot = assemble(robotlist[i], "Normal")
                        else:
                            newbot = assemble(robotlist[i], "Normal")
                        if newbot and newbot.build_qual>=QualityThreshold:
                            if (newbot.type == "Normal"):
                                canCollect = collectCheck(newbot)
                                if canCollect:
                                    collecting(newbot)
                            elif (newbot.type == "Printer"):
                                if (printCheck(newbot)):
                                    printing(newbot)
                                elif (collectCheck(newbot)):
                                    collecting(newbot)
                                else:
                                    newbot.set_prev_task(newbot.get_curr_task())
                                    newbot.set_task_dur(0)
                                    newbot.set_curr_task("idle")
                            elif(newbot.type == "Assembler"):
                                if (newbot.get_previously_built() == ""):
                                    if (assembleCheck(newbot,"Normal")):
                                        isAssembling = assembling(newbot, "Normal")
                                    elif (assembleCheck(newbot,"Assembler")):
                                        isAssembling = assembling(newbot, "Assembler")
                                    elif (assembleCheck(newbot,"Printer")):
                                        isAssembling = assembling(newbot, "Printer")
                                    elif (collectCheck(newbot)):
                                        collecting(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                                else:
                                    if (newbot[i].get_previously_built() == "Assembler" and assembleCheck("Printer")):
                                        isAssembling = assembling(newbot, "Printer")
                                    elif (newbot[i].get_previously_built() == "Printer" and assembleCheck("Normal")):
                                        isAssembling = assembling(newbot, "Normal")
                                    elif (newbot[i].get_previously_built() == "Normal" and assembleCheck("Printer")):
                                        isAssembling = assembling(newbot, "Printer")
                                    elif (collectCheck(newbot)):
                                        collecting(newbot)
                                    else:
                                        newbot.set_prev_task(newbot.get_curr_task())
                                        newbot.set_task_dur(0)
                                        newbot.set_curr_task("idle")
                            totlist.append(newbot)
                            robotlist.append(newbot)
                        else:
                            totlist.append(newbot)
                            useless.append(newbot)
                        robotlist[i].set_prev_task(robotlist[i].current_task)

        if (Env_Materials == 0 and checkENV == 0):
                checkENV = t
        if (Printable <= 0 and checkPrint == 0):
            checkPrint = t
        if (NonPr <= 1 and checkNonPr == 0):
            checkNonPr = t
        if (Materials <= 1 and checkMat == 0):
            checkMat = t
#         print("Time",t,"w/",len(robotlist),"Robots")
#         for j in robotlist:
#             print(j)
#         print("-"*50)

         #after simulation record
        build_quality_list,vals = configHandler(t,totlist,robotlist,useless,checkENV,checkPrint,checkNonPr,checkMat)
        df.loc[len(df)] = [t,NonPr,Printable,Materials,Env_Materials]+vals
        tcoordslist.append(t)
        rcoordslist.append(len(robotlist))
        wastecoordslist.append(len(useless))
        t_build_quality_list.append(build_quality_list)

    # setup RAM metrics of robots
    MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS = computeRAMMetrics(robotlist)

    df["Print Capacity"] = df[["#Printer", "#Replicator"]].sum(axis=1)
    df["Assembling Capacity"] = df[["#Assembler", "#Replicator"]].sum(axis=1)
    df["Collection Capacity"] = df[["#Printer", "#Replicator", "#Assembler", "#Normal"]].sum(axis=1)
    df["#Tasks before failure"] = robotlist[0].getNumTasksBeforeFailure()
    ram_df = pd.DataFrame(columns=["MTBF","MTTR","MDT","Aoss"],data=[[MTBF_SRRS,MTTR_SRRS,MDT_SRRS,Aoss_SRRS]])
    return df,ram_df

def SRRS(config,timesteps,plot=False):
    if not os.path.exists("./Deterministic_Mode/"+config):
        os.makedirs("./Deterministic_Mode/"+config)
    df = pd.DataFrame(columns = table_columns)
    build_qual_range = [0.85,0.95]
    init_build_qual = random.uniform(build_qual_range[0],build_qual_range[1])
    if config=="CHO":
        df,ram_df = CHO(timesteps,df,init_build_qual)
    elif config=="DHO":
        df,ram_df = DHO(timesteps,df,init_build_qual)
    elif config=="HHO":
        df,ram_df = HHO(timesteps,df,init_build_qual)
    elif config=="CHE":
        df,ram_df = CHE(timesteps,df,init_build_qual)
    elif config=="DHE":
        df,ram_df = DHE(timesteps,df,init_build_qual)
    elif config=="HHE":
        df,ram_df = HHE(timesteps,df,init_build_qual)

    # if(plot):
    #     graphOutputs(config,df)
    return df,ram_df

def SRRSmc(config,timesteps,mc_num_steps,plot=True):
    if not os.path.exists("./MC_Mode/"+config):
        os.makedirs("./MC_Mode/"+config)
    mcSimCols = ['Time', 'NonPr', 'Printable', 'Materials', 'Env_Materials',
           '#Replicator', '#Normal', '#Assembler', '#Printer', '#Assembling',
           '#Printing', '#Collecting', '#Idle', '#Repair', '#In', '#Out',
           'Average Build Quality in-service', 'Average Build Quality of System',
           '#WasteReplicator', '#WasteNormal', '#WasteAssembler', '#WastePrinter',
           'Environment Exhaust Time', 'Printable Exhaust Time',
           'NonPr Exhaust Time', 'Material Exhaust Time', 'Average Risk',
           'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
           'MTBF','MTTR', 'MDT', 'Aoss']

    mcdfsim = pd.DataFrame(columns=mcSimCols)
    i=1
    while i <= mc_num_steps:
#     for i in range(1,mc_num_steps+1):
        sys.stdout.write("\rRunning iteration: {0}".format(i))
        sys.stdout.flush()
#         print(f'Running iteration: {i}')
        df,ram_df = SRRS(config,timesteps,plot)

        if(math.isnan(ram_df["Aoss"].to_list()[0])==True):
            print("Redo.")
        else:
            ext="MC_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)+"_mcIteration_"+str(i)
            graphOutputsMatplotlib(config,df,ram_df,"./MC_Mode/"+config+"/",ext)
            df_stats = df.describe()
            avg_avgRisk = df_stats.iloc[1]["Average Risk"]
            last_row = df.tail(1)
            last_row["Average Risk"].values[:] = avg_avgRisk
            cols = df.columns
            mcdf = pd.DataFrame(columns=cols)
            mcdf = pd.concat([mcdf,last_row], ignore_index=True)
            mcdf = pd.concat([mcdf, ram_df], axis=1, join='inner')
            last_row = mcdf.tail(1)
            mcdfsim = pd.concat([mcdfsim, last_row], ignore_index=True)
#             print("="*20)
            i+=1
    return mcdfsim

def printSRRSConfigRAMmetrics(ram_df):
    display(ram_df)

def graph_RobotTasks(config,df,path=None,ext=None):
    fig = px.bar(df, x="Time", y=['#Printing','#Assembling','#Collecting', '#Idle', '#Repair'], title=config+" Robot Tasks vs Time") #,labels={'#In':'#in-service','#Out':'#out-service'})
    fig.update_layout(hovermode="x")
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='#Robots')
    if path:
        fig.write_html(path+"/graph_RobotTasks_"+ext+".html",auto_open=False)
#         fig.write_image(path+"/graph_RobotTasks_"+ext+".png")
    # else:
    #     fig.show()

def graph_InOutServiceRobots(config,df,path=None,ext=None):
    fig = px.bar(df, x="Time", y=['#In','#Out'], title=config+" Robots in service vs Time") #,labels={'#In':'#in-service','#Out':'#out-service'})
    fig.update_layout(hovermode="x")
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='#Robots')
    if path:
        fig.write_html(path+"/graph_InOutServiceRobots_"+ext+".html",auto_open=False)
#         fig.write_image(path+"/graph_InOutServiceRobots_"+ext+".png")
    # else:
    #     fig.show()

def graph_RobotTypes(config,df,path=None,ext=None):
    fig = px.bar(df, x="Time", y=['#Replicator', '#Normal', '#Assembler', '#Printer'], title=config+" Robots Types vs Time") #,labels={'#In':'#in-service','#Out':'#out-service'})
    fig.update_layout(hovermode="x")
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='#Robots')
    if path:
        fig.write_html(path+"/graph_RobotTypes_"+ext+".html",auto_open=False)
#         fig.write_image(path+"/graph_RobotTypes_"+ext+".png")
    # else:
    #     fig.show()

def graph_Resources(config,df,path=None,ext=None):
#     fig = px.bar(df, x="Time", y=['NonPr', 'Printable', 'Materials', 'Env_Materials'], title="Resources vs Time") #,labels={'#In':'#in-service','#Out':'#out-service'})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time"], y=df['NonPr'], mode="lines",name='NonPr'))
    fig.add_trace(go.Scatter(x=df["Time"], y=df['Printable'], mode="lines",name='Printable'))
    fig.add_trace(go.Scatter(x=df["Time"], y=df['Materials'], mode="lines",name='Materials'))
    fig.add_trace(go.Scatter(x=df["Time"], y=df['Env_Materials'], mode="lines",name='Env_Materials'))
    fig.update_layout(hovermode="x",title=config+" Resources vs Time")
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Resources')
    if path:
        fig.write_html(path+"/graph_Resources_"+ext+".html",auto_open=False)
#         fig.write_image(path+"/graph_Resources_"+ext+".png")
    # else:
    #     fig.show()

def graph_AvgBuildQuality(config,df,path=None,ext=None):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Time"], y=df['Average Build Quality in-service'], mode="lines",name='Avg. Build Quality-In Service'))
    fig.add_trace(go.Scatter(x=df["Time"], y=df['Average Build Quality of System'], mode="lines",name='Avg. Build Quality-System'))
    fig.update_layout(hovermode="x",title=config+" Robot Build Quality vs Time")
    fig.update_xaxes(title_text='Time')
    fig.update_yaxes(title_text='Build Quality')
    if path:
        fig.write_html(path+"/graph_AvgBuildQuality_"+ext+".html",auto_open=False)
#         fig.write_image(path+"/graph_AvgBuildQuality_"+ext+".png")
    # else:
    #     fig.show()

def graphOutputs(config,df,path=None,ext=None):
    graph_RobotTasks(config,df,path,ext)
    graph_InOutServiceRobots(config,df,path,ext)
    graph_RobotTypes(config,df,path,ext)
    graph_Resources(config,df,path,ext)
    graph_AvgBuildQuality(config,df,path,ext)

def graphOutputsMatplotlib(config,df,ram_df,path,ext):
    plt.subplot(3, 2, 1)
    plt.grid()
    plt.plot(df['Time'], df['#Printing'], label="#Printing")
    plt.plot(df['Time'], df['#Assembling'], label="#Assembling")
    plt.plot(df['Time'], df['#Collecting'], label="#Collecting")
    plt.plot(df['Time'], df['#Idle'], label="#Idle")
    plt.plot(df['Time'], df['#Repair'], label="#Repair")
    plt.xlim([df['Time'].min(), df['Time'].max()])
    plt.title("Robot tasks vs Time")
    plt.xlabel('Timesteps')
    plt.ylabel('#Robots')
    plt.legend()

    plt.subplot(3, 2, 2)
    plt.grid()
    plt.plot(df['Time'], df['#In'], label="#In")
    plt.plot(df['Time'], df['#Out'], label="#Out")
    plt.xlim([df['Time'].min(), df['Time'].max()])
    plt.title("Robots in and out of service vs Time")
    plt.xlabel('Timesteps')
    plt.ylabel('#Robots')
    plt.legend()

    plt.subplot(3, 2, 3)
    plt.grid()
    plt.plot(df['Time'], df['#Printer'], label="#Printer")
    plt.plot(df['Time'], df['#Assembler'], label="#Assembler")
    plt.plot(df['Time'], df['#Replicator'], label="#Replicator")
    plt.plot(df['Time'], df['#Normal'], label="#Normal")
    plt.xlim([df['Time'].min(), df['Time'].max()])
    plt.title("Types of Robots vs Time")
    plt.xlabel('Timesteps')
    plt.ylabel('#Robots')
    plt.legend()

    plt.subplot(3, 2, 4)
    plt.grid()
    plt.plot(df['Time'], df['NonPr'], label="NonPr")
    plt.plot(df['Time'], df['Printable'], label="Printable")
    plt.plot(df['Time'], df['Materials'], label="Materials")
    plt.plot(df['Time'], df['Env_Materials'], label="Env_Materials")
    plt.xlim([df['Time'].min(), df['Time'].max()])
    plt.title("Resources vs Time")
    plt.xlabel('Timesteps')
    plt.ylabel('Resources values')
    plt.legend()

    plt.subplot(3, 2, 5)
    plt.grid()
    plt.plot(df['Time'], df['Average Build Quality in-service'], label="In service")
    plt.plot(df['Time'], df['Average Build Quality of System'], label="Total System")
    plt.xlim([df['Time'].min(), df['Time'].max()])
    plt.title("Average build quality of Robots vs Time")
    plt.xlabel('Timesteps')
    plt.ylabel('Average Build Quality')
    plt.legend()

    plt.subplot(3,2,6)
    plt.title("Reliability, Availability and Maintainability Metrics")
    cell_text = []
    for row in range(len(ram_df)):
        cell_text.append(ram_df.iloc[row])

    plt.table(cellText=cell_text, colLabels=ram_df.columns, loc='center')
    plt.axis('off')

#     plt.show()
    fig = plt.gcf()
    fig.set_size_inches(20, 15)
    fig.suptitle(ext)
    plt.tight_layout()
    fig.savefig(path+ext+".png",dpi=300)
    fig.clear()

def plotDistribution(config,df,path,ext):
#     ['Average Build Quality in-service', 'Average Build Quality of System',
#     '#Replicator', '#Normal', '#Assembler', '#Printer',
#     'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
#     'MTBF','MTTR', 'MDT', 'Aoss']
#     fig = go.Figure()
#     fig.add_trace(px.histogram(mcdf, x="Aoss", y="MTBF", marginal="rug",
#                    hover_data=['MTBF','MTTR', 'MDT', 'Aoss']))
# #     fig.add_trace(go.Histogram(x=mcdf['Aoss'],hovertemplate="<b>Bin Edges:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>"))
#     fig = make_subplots(rows=3, cols=2,subplot_titles=('MTBF','MTTR', 'MDT', 'Aoss','Average Build Quality in-service', 'Average Build Quality of System'))
#     trace0 = go.Histogram(x=mcdf['MTBF'])
#     trace1 = go.Histogram(x=mcdf['MTTR'])
#     trace2 = go.Histogram(x=mcdf['MDT'])
#     trace3 = go.Histogram(x=mcdf['Aoss'])
#     trace4 = go.Histogram(x=mcdf['Average Build Quality in-service'])
#     trace5 = go.Histogram(x=mcdf['Average Build Quality of System'])
#     fig.append_trace(trace0, 1, 1)
#     fig.append_trace(trace1, 1, 2)
#     fig.append_trace(trace2, 2, 1)
#     fig.append_trace(trace3, 2, 2)
#     fig.append_trace(trace4, 3, 1)
#     fig.append_trace(trace5, 3, 2)
#     fig.update_layout(hovermode="x",title=config,margin=dict(t=30))
#     fig.update_xaxes(title_text='Values')
#     fig.update_yaxes(title_text='Count')
#     fig.show()
#     print(df.isnull().any(axis=1).sum())
    if(df.isnull().values.any()):
        df.dropna()


    plt.subplot(3, 2, 1)
    plt.hist(df['Average Build Quality in-service'],bins=20)
    plt.xlabel('Average Build Quality in-service')
    plt.ylabel('Frequency')
    plt.title('Average Build Quality in-service')

    plt.subplot(3, 2, 2)
    plt.hist(df['Average Build Quality of System'],bins=20)
    plt.xlabel('Average Build Quality of System')
    plt.ylabel('Frequency')
    plt.title('Average Build Quality of System')

    plt.subplot(3, 2, 3)
    plt.hist(df['MTBF'],bins=20)
    plt.xlabel('MTBF')
    plt.ylabel('Frequency')
    plt.title('MTBF')

    plt.subplot(3, 2, 4)
    plt.hist(df['MTTR'],bins=20)
    plt.xlabel('MTTR')
    plt.ylabel('Frequency')
    plt.title('MTTR')

    plt.subplot(3, 2, 5)
    plt.hist(df['MDT'],bins=20)
    plt.xlabel('MDT')
    plt.ylabel('Frequency')
    plt.title('MDT')

    plt.subplot(3, 2, 6)
    plt.hist(df['Aoss'],bins=20)
    plt.xlabel('Aoss')
    plt.ylabel('Frequency')
    plt.title('Aoss')

    fig = plt.gcf()
    fig.set_size_inches(20, 15)
    fig.suptitle(ext)
    plt.tight_layout()
    fig.savefig(path+ext+".png",dpi=300)
#     plt.show()
    fig.clear()

def saveMCMode(mcdf,config,timesteps,RiskThreshold,timetaken):
    if not os.path.exists("./MC_Mode/"+config):
        os.makedirs("./MC_Mode/"+config)
    filename = "./MC_Mode/"+config+"/MC_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)
    ext="MC_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)
    mcdf.to_csv(filename+".csv")
    plotDistribution(config,mcdf,"./MC_Mode/"+config,ext)
    mcdf_stats = saveMCModeStatsResults(mcdf,config,timesteps,RiskThreshold,timetaken)

    return mcdf_stats

def saveMCModeStatsResults(mcdf,config,timesteps,RiskThreshold,timetaken):
#     print(mcdf.columns)
#     ['Time', 'NonPr', 'Printable', 'Materials', 'Env_Materials',
#        '#Replicator', '#Normal', '#Assembler', '#Printer', '#Assembling',
#        '#Printing', '#Collecting', '#Idle', '#Repair', '#In', '#Out',
#        'Average Build Quality in-service', 'Average Build Quality of System',
#        '#WasteReplicator', '#WasteNormal', '#WasteAssembler', '#WastePrinter',
#        'Environment Exhaust Time', 'Printable Exhaust Time',
#        'NonPr Exhaust Time', 'Material Exhaust Time', 'Average Risk',
#        'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
#        'MTBF','MTTR', 'MDT', 'Aoss', '#Tasks before failure']
    filename = "./MC_Mode/"+config+"/MC_Stats_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)
    mcdf = mcdf.apply(pd.to_numeric)
    mcdf_stats = mcdf.describe(include="all")
    mcdf_stats = mcdf_stats.loc[['count','mean','std','min','max']]
    mcdf_stats = mcdf_stats[['MTBF','MTTR', 'MDT', 'Aoss',
                            'Average Build Quality in-service', 'Average Build Quality of System',
                             'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
                             'Environment Exhaust Time','Printable Exhaust Time',
                             'NonPr Exhaust Time', 'Material Exhaust Time',
                            '#Replicator', '#Normal', '#Assembler', '#Printer']]
    mcdf_stats.to_csv(filename+".csv")
    return mcdf_stats

def saveMCModeResults(test_mean_table,test_std_table):
    if not os.path.exists("./MC_Mode/"):
        os.makedirs("./MC_Mode/")

    test_mean_table = test_mean_table[['Configuration','Number of MC Runs','Execution Time (ms)',
                                       'MTBF', 'MTTR', 'MDT', 'Aoss',
                                       'Average Build Quality in-service','Average Build Quality of System',
                                       'Print Capacity','Assembling Capacity', 'Collection Capacity',
                                       'Environment Exhaust Time','Printable Exhaust Time',
                             'NonPr Exhaust Time', 'Material Exhaust Time',
                                       '#Replicator', '#Normal','#Assembler', '#Printer']]
    filename = "./MC_Mode/MC-Scenarios-TestCases-Mean.csv"
    print(f'saving {filename}...')
    test_mean_table.to_csv(filename)
    test_std_table = test_std_table[['Configuration','Number of MC Runs',
                                       'MTBF', 'MTTR', 'MDT', 'Aoss',
                                       'Average Build Quality in-service','Average Build Quality of System',
                                       'Print Capacity','Assembling Capacity', 'Collection Capacity',
                                     'Environment Exhaust Time', 'Printable Exhaust Time',
                           'NonPr Exhaust Time', 'Material Exhaust Time',
                                       '#Replicator', '#Normal','#Assembler', '#Printer']]
    filename = "./MC_Mode/MC-Scenarios-TestCases-StdDev.csv"
    print(f'saving {filename}...')
    test_std_table.to_csv(filename)

    display(test_mean_table)
#     display(test_std_table)
    confidence_percentage = [80,85,90,95]
    cvals = [1.282,1.440,1.645,1.960]

    confidence_table = pd.DataFrame(columns = ["Config","Confidence %","Aoss(Mu)","Aoss(ME)","Range","MC Iterations"])
    for c in range(len(confidence_percentage)):
        for i in range(len(test_mean_table)):
            mc_num_steps = test_mean_table.loc[i]['Number of MC Runs']
            config = test_mean_table.loc[i]['Configuration']
            mean_aoss = test_mean_table.loc[i]['Aoss']
            mean_mtbf = test_mean_table.loc[i]['MTBF']
            mean_mttr = test_mean_table.loc[i]['MTTR']
            mean_mdt = test_mean_table.loc[i]['MDT']
            std_aoss = test_std_table.loc[i]['Aoss']
            std_mtbf = test_std_table.loc[i]['MTBF']
            std_mttr = test_std_table.loc[i]['MTTR']
            std_mdt = test_std_table.loc[i]['MDT']

            me_aoss = cvals[c]*std_aoss/mc_num_steps
            exec_time = test_mean_table.loc[i]['Execution Time (ms)']

            avg_build_qual_in = test_mean_table.loc[i]['Average Build Quality in-service']
            avg_build_qual_tot = test_mean_table.loc[i]['Average Build Quality of System']
            pc = test_mean_table.loc[i]['Print Capacity']
            ac = test_mean_table.loc[i]['Assembling Capacity']
            cc = test_mean_table.loc[i]['Collection Capacity']
            replicator = test_mean_table.loc[i]['#Replicator']
            normal = test_mean_table.loc[i]['#Normal']
            assembler = test_mean_table.loc[i]['#Assembler']
            printer = test_mean_table.loc[i]['#Printer']


            mean_aoss = round(mean_aoss,4)
            me_aoss = round(me_aoss,4)


            print(f'{config}: {confidence_percentage[c]}% CI - {mean_aoss:.4f} [{mean_aoss-me_aoss:.4f},{mean_aoss+me_aoss:.4f}], based on {mc_num_steps} samples.')
            rmin = round(mean_aoss-me_aoss,4)
            rmax = round(mean_aoss+me_aoss,4)
            cdf = pd.DataFrame(columns=["Config","Confidence %","Aoss(Mu)","Aoss(ME)","Range","MC Iterations"],
                               data=[[config,confidence_percentage[c],mean_aoss,me_aoss,[rmin,rmax],mc_num_steps]])
            confidence_table = pd.concat([confidence_table,cdf],ignore_index=True)

    display(confidence_table)
    filename = "./MC_Mode/MC-Scenarios-TestCases-ConfidenceIntervals.csv"
    print(f'saving {filename}...')
    confidence_table.to_csv(filename)




def saveDetMode(df,ram_df,config,timesteps,RiskThreshold,numTasksBeforeFail):
    if not os.path.exists("./Deterministic_Mode/"+config):
        os.makedirs("./Deterministic_Mode/"+config)
    filename = "./Deterministic_Mode/"+config+"/Determinisitic_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)+"_numTaskBeforeFail_"+str(numTasksBeforeFail)
    ext="Determinisitic_"+str(config)+"_time_"+str(timesteps)+"_risk_"+str(RiskThreshold)+"_numTaskBeforeFail_"+str(numTasksBeforeFail)
    df.to_csv(filename+".csv")
    graphOutputsMatplotlib(config,df,ram_df,"./Deterministic_Mode/"+config,ext)
    # graphOutputs(config,df,"./Deterministic_Mode/"+config+"/",ext)

def saveDetModeResults(test_table):
    if not os.path.exists("./Deterministic_Mode/"):
        os.makedirs("./Deterministic_Mode/")
    filename = "./Deterministic_Mode/Deterministic-Scenarios-TestCases.csv"
    print(f'saving {filename}...')
    test_table.to_csv(filename)

checkconfiglist = ["CHO","DHO","HHO","CHE","DHE","HHE"]
print("Please input any configuration from the list below.")
for i in range(len(checkconfiglist)):
    print(str(i+1)+".",checkconfiglist[i])


while(1):
    configurations = input("Enter configurations separated by commas and press Enter. For e.g: CHO,DHO. \n --> ")
    configurations = configurations.split(",")
    flag =  all(item in checkconfiglist for item in configurations)
    if flag:
        break

while(1):
    mode = input("Enter D for Deterministic mode and MC for Monte-Carlo mode. [D/MC]?: \n --> ")
    if mode=="D":
        mc = False
        numTasksBeforeFaillist = int(input("Input Number of Tasks to be performed before failing: (Suggested values < 5) \n --> "))
        numTasksBeforeFaillist = [numTasksBeforeFaillist]
        break
    elif mode=="MC":
        mc = True
        numTasksBeforeFaillist = [0]
        mc_num_steps = int(input("Input number of Monte-Carlo runs for the simulation: \n --> "))
        break
    else:
        continue



timestepslist = int(input("Input number of time-steps for each run of simulation: \n --> "))
timestepslist = [timestepslist]
QualityThreshold = float(input("Input Build Quality Threshold for the Robots between (0,1): (Suggested value = 0.5)\n --> "))
RiskThresholds = float(input("Input Risk Value Threshold for the Robots between (0,1): (Suggested value = 0.5)\n --> "))
RiskThresholds = [RiskThresholds]

configlist = configurations

test_table = pd.DataFrame()
test_mean_table = pd.DataFrame()
test_std_table = pd.DataFrame()
if mc:
    numTasksBeforeFaillist=[0]
for config in configlist:
    for risk in RiskThresholds:
        RiskThreshold = risk
        for timestep in timestepslist:
            timesteps = timestep
            for numTasks in numTasksBeforeFaillist:
                numTasksBeforeFail = numTasks
                try:
                    if mc:
                        start_time = time.time()
                        print(f'\nMC {config}, Risk:{RiskThreshold}, t:{timesteps}')
                        mcdf = SRRSmc(config,timesteps,mc_num_steps,False)
                        mean_mcdf = mcdf[['Print Capacity', 'Assembling Capacity', 'Collection Capacity', 'MTBF','MTTR', 'MDT', 'Aoss','#In', '#Out','Average Build Quality of System']].mean()
                        finish_time = time.time()
                        result = mcdf.tail(1).reset_index(drop=True)
                        result['Configuration'] = config
                        result = result[['Configuration','Time', 'NonPr', 'Printable', 'Materials', 'Env_Materials',
                        '#Replicator', '#Normal', '#Assembler', '#Printer', '#Assembling',
                        '#Printing', '#Collecting', '#Idle', '#Repair', '#In', '#Out',
                        'Average Build Quality in-service', 'Average Build Quality of System',
                        '#WasteReplicator', '#WasteNormal', '#WasteAssembler', '#WastePrinter',
                        'Environment Exhaust Time', 'Printable Exhaust Time',
                        'NonPr Exhaust Time', 'Material Exhaust Time', 'Average Risk',
                        'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
                        'MTBF','MTTR', 'MDT', 'Aoss']]
                        timetaken = (finish_time-start_time)*10**3
                        result['Execution Time (ms)'] = timetaken
                        print(f" - Iterations: \tTime taken: {timetaken:.03f}ms")
                        mcdf_stats = saveMCMode(mcdf,config,timesteps,RiskThreshold,timetaken)
                        mean_table = mcdf_stats[['MTBF', 'MTTR', 'MDT', 'Aoss', 'Average Build Quality in-service',
                        'Average Build Quality of System', 'Environment Exhaust Time', 'Printable Exhaust Time',
                        'NonPr Exhaust Time', 'Material Exhaust Time','Print Capacity',
                        'Assembling Capacity', 'Collection Capacity', '#Replicator', '#Normal',
                        '#Assembler', '#Printer']].loc[['mean']]
                        std_table = mcdf_stats[['MTBF', 'MTTR', 'MDT', 'Aoss', 'Average Build Quality in-service',
                        'Average Build Quality of System', 'Environment Exhaust Time', 'Printable Exhaust Time',
                        'NonPr Exhaust Time', 'Material Exhaust Time','Print Capacity',
                        'Assembling Capacity', 'Collection Capacity', '#Replicator', '#Normal',
                        '#Assembler', '#Printer']].loc[['std']]
                        mean_table['Execution Time (ms)'] = timetaken
                        mean_table['Configuration'] = config
                        std_table['Configuration'] = config
                        mean_table['RiskThreshold'] = RiskThreshold
                        std_table['RiskThreshold'] = RiskThreshold
                        mean_table['Number of MC Runs'] = mc_num_steps
                        std_table['Number of MC Runs'] = mc_num_steps
                        test_mean_table = pd.concat([test_mean_table,mean_table],ignore_index=True)
                        test_std_table = pd.concat([test_std_table,std_table],ignore_index=True)
                    else:
                        start_time = time.time()
                        print(f'Deterministic {config}, Risk:{RiskThreshold}, t:{timesteps}, #Tasks Before Fail:{numTasksBeforeFail}')
                        df,ram_df = SRRS(config,timesteps,True)
                        saveDetMode(df,ram_df,config,timesteps,RiskThreshold,numTasksBeforeFail)
                        result = df.tail(1).reset_index(drop=True)
                        result = pd.concat([result,ram_df], axis=1)
                        result['RiskThreshold'] = RiskThreshold
                        result['Configuration'] = config
                        result = result[['Configuration','RiskThreshold','Time', 'NonPr', 'Printable', 'Materials', 'Env_Materials',
                        '#Replicator', '#Normal', '#Assembler', '#Printer', '#Assembling',
                        '#Printing', '#Collecting', '#Idle', '#Repair', '#In', '#Out',
                        'Average Build Quality in-service', 'Average Build Quality of System',
                        '#WasteReplicator', '#WasteNormal', '#WasteAssembler', '#WastePrinter',
                        'Environment Exhaust Time', 'Printable Exhaust Time',
                        'NonPr Exhaust Time', 'Material Exhaust Time', 'Average Risk',
                        'Print Capacity', 'Assembling Capacity', 'Collection Capacity',
                        'MTBF', 'MTTR', 'MDT', 'Aoss']]
                        finish_time = time.time()
                        timetaken = (finish_time-start_time)*10**3
                        result['Execution Time (ms)'] = timetaken
                        print(f"Iteration: \tTime taken: {timetaken:.03f}ms")
                        test_table = pd.concat([test_table,result],ignore_index=True)
                except Exception as err:
                    print(f"Unexpected {err=}, {type(err)=}")
                    raise
if mc:
    saveMCModeResults(test_mean_table,test_std_table)
else:
    saveDetModeResults(test_table)
