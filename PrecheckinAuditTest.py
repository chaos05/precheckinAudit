import json
import os.path
import requests
import pprint

from Precheckin import Precheckin

#import certifi
#certifi.where()
#'/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/certifi/cacert.pem'

#AutobuildId main_precheckin: 4869
#AutobuildId 224_patch_precheckin: 28001 (main -2 precheckin, aka will this id remain the same?)
#TestId main: testNapiliHomeAndLogin(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 70123236
#TestId 224 patch: testNapiliHomeAndLogin(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 259252737
#TestId main: testVerifyBuilderLoads(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 70197630


class PrecheckinAuditTest:

    autoBuildNameMain = "main"
    autoBuildName224Patch = "224Patch"
    
    communityRuntime = "runtime"
    communityDesignTime = "design time"

    # The api endpoint.  We will format/merge the testId we want to audit and the requestedRunCount (how many runs we are want to audit)
    apiEndPoint = 'https://lunadas.prod.ci.sfdc.net/api/results/v1/q/test-history?test-id={testId}&show-skipped-runs=true&load-all=false&start-index=0&row-count={requestedRunCount}'

    blah = "test"
    file_name_last_audit_main_runtime = blah + "last_audit_main_runtime_time-stamp.json"
    file_name_last_audit_main_design_time = blah + "last_audit_main_design_time_time-stamp.json"
    file_name_last_audit_224_runtime = blah + "last_audit_224_runtime_time-stamp.json"
    file_name_last_audit_224_design_time = blah + "last_audit_224_design_time_time-stamp.json"
    
    ## slack - post to a 'webhook url'.  Create one from the slack api 'Incoming Webhooks' while signed in to salesforce slack.  https://api.slack.com/apps/ASAL2RZSB/incoming-webhooks?success=1
    # For testing - post to the my slack channel
    eric_webhook_url = 'https://hooks.slack.com/services/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'
    # For testing - post to the precheck app's message channel
    app_webhook_url = 'https://hooks.slack.com/services/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'
    # Production - post to our communities precheck slack channel
    precheck_webhook_url = 'https://hooks.slack.com/services/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'
    ##q3_webhook_url = 'https://hooks.slack.com/services/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'
    
    # initializer / instance attributes
    def __init__(self, testId, communityDesignOrRuntime, autoBuildName, requestedRunCount):
        
        if requestedRunCount == None:
            self.requestedRunCount = 50
        else:
            self.requestedRunCount = requestedRunCount

        self.url = PrecheckinAuditTest.apiEndPoint.format(testId=testId, requestedRunCount=requestedRunCount)
        self.communityDesignOrRuntime = communityDesignOrRuntime
        self.autoBuildName = autoBuildName
        self.testId = testId
        self.successCount = 0
        self.failCount = 0
        self.executionTimeList = []
        self.executionTimesTotal = 0
        self.response = None
        self.pyPrecheckins = []
        self.precheckins = []
        self.failPrecheckins = []
        self.averageExecutionTime = 0
        self.testName = ''


    def precheckinAudit(self):
        self.response = requests.get(self.url, verify=False)
        
        # deserialize json - convert from json to python objects (dicts)
        self.pyPrecheckins = json.loads(self.response.text)

        latest_time_stamp = None
        self.file_name_latest_precheckin = None
        if ( self.communityDesignOrRuntime == PrecheckinAuditTest.communityRuntime and self.autoBuildName == PrecheckinAuditTest.autoBuildNameMain):
            self.file_name_latest_precheckin = PrecheckinAuditTest.file_name_last_audit_main_runtime
        elif ((self.communityDesignOrRuntime == PrecheckinAuditTest.communityDesignTime) and self.autoBuildName == PrecheckinAuditTest.autoBuildNameMain):
            self.file_name_latest_precheckin = PrecheckinAuditTest.file_name_last_audit_main_design_time
        elif ((self.communityDesignOrRuntime == PrecheckinAuditTest.communityRuntime) and self.autoBuildName == PrecheckinAuditTest.autoBuildName224Patch):
            self.file_name_latest_precheckin = PrecheckinAuditTest.file_name_last_audit_224_runtime
        elif ((self.communityDesignOrRuntime == PrecheckinAuditTest.communityDesignTime) and self.autoBuildName == PrecheckinAuditTest.autoBuildName224Patch):
            self.file_name_latest_precheckin = PrecheckinAuditTest.file_name_last_audit_224_design_time
        else:
            # add an error
            pass
        
        if (os.path.isfile(self.file_name_latest_precheckin)):
            with open(self.file_name_latest_precheckin, "r") as read_file:
                latest_time_stamp = json.load(read_file)
                # print(latest_time_stamp)

        # make it a function/method 
        # process precheckins audit data (a precheckin obj?)
        for pyPrecheckin in self.pyPrecheckins:
            
            this_time_stamp = pyPrecheckin['end-date']
            # if we have the time stamp from the previous audit
            if (latest_time_stamp):
                if (this_time_stamp == latest_time_stamp):
                    break

            # make it a function/method
            runTimeStr = pyPrecheckin['running-time']
            # strip the 's' from the end and turn it back to an int
            runTimeStrLen = len(runTimeStr)
            runTime = int(runTimeStr[:(runTimeStrLen - 1)])

            # instantiate a precheckin here
            precheckin = Precheckin(pyPrecheckin['uniqueTestName'], pyPrecheckin['changelist'], pyPrecheckin['owner'], \
                                    pyPrecheckin['status'], runTime, this_time_stamp, pyPrecheckin['apiaryLogUrl'])
            
            self.precheckins.append(precheckin)

            self.executionTimesTotal += precheckin.executionTime
            self.executionTimeList.append(runTime)

            if precheckin.status == Precheckin.status_success:
                self.successCount += 1
            # if we find a precheckin failure, then parse and append cl data
            elif precheckin.status == Precheckin.status_failure:
                self.failCount += 1
                self.failPrecheckins.append(precheckin)
            else:
                # some type of error report?
                pass


        # Only process the precheckin runs if there are new ones since the last audit
        if (len(self.precheckins) > 0):
            # factor out to a method
            # Write out the latest precheckin for reference.  Each run of this script should only process precheckins that have yet to process (up until the last latest)
            # print("time stamp of first precheckin: " + self.precheckins[0].timeStamp)
            with open(self.file_name_latest_precheckin, "w") as data_file:
                json.dump(self.precheckins[0].timeStamp, data_file)

            self.averageExecutionTime = self.executionTimesTotal / len(self.executionTimeList)

            # get and set the test name
            self.testName = self.precheckins[0].testName

            precheckinCount = len(self.precheckins)
            failedPrecheckinCount = len(self.failPrecheckins)
            self.precheckinAuditResult = "time stamp: " + self.precheckins[0].timeStamp + "; " \
                + "precheckin test: " + self.autoBuildName + " - " + self.testName + ": " \
                    + "precheckins since last audit: " + str(precheckinCount) + "; " \
                        + "average execution time: " + str(self.averageExecutionTime)[:3] + "s; " \
                            + "success count: " + str(precheckinCount - failedPrecheckinCount) + "; " \
                                + "failure count: " + str(failedPrecheckinCount)

        
            # build the text string with info about the test failures
            self.testFailureInfo = ''
            ix = 0
            for failPrecheckin in self.failPrecheckins:

                # format: prepend with 'failures'
                if (len(self.testFailureInfo) == 0):
                    self.testFailureInfo += "; ** failure **: "

                # content: add a precheckin failure's info
                self.testFailureInfo += "owner: " + failPrecheckin.owner + "; " \
                    + "cl: " + str(failPrecheckin.cl) + "; " \
                        + "execution time: " + str(failPrecheckin.executionTime) + "s; " \
                            + "time stamp: " + str(failPrecheckin.timeStamp) + "; " \
                                + "logs: " + failPrecheckin.apiaryLogUrl

                # format: add a comma between test failures
                if (ix > 0):
                    ix += 1
                    self.testFailureInfo += ", "


            # trim the comma from the end of the test failures test string
            # add the test failures string to the precheckin audit result text string
            if (len(self.testFailureInfo) > 0):
                # self.testFailureInfo = str(self.testFailureInfo)[:len(self.testFailureInfo) - 1]
                self.precheckinAuditResult += self.testFailureInfo

        else:
            self.precheckinAuditResult = "There are no precheckin runs since the last audit - " + self.autoBuildName + " - " + self.communityDesignOrRuntime

        if (len(self.precheckinAuditResult) > 0):
            self.slack_data = {'text': self.precheckinAuditResult}
            requests.post(PrecheckinAuditTest.eric_webhook_url, json=self.slack_data)


requestedRunCount = 10

testIdCommRunTimeMain = str(70123236)
testIdCommDesignTimeMain = str(70197630)
testIdCommRunTime224Patch = str(259252737)
testIdCommDesignTime224Patch = str(259252984)

commPrecheckinRuntimeMain = PrecheckinAuditTest(testIdCommRunTimeMain, PrecheckinAuditTest.communityRuntime, PrecheckinAuditTest.autoBuildNameMain, requestedRunCount)
commPrecheckinRuntimeMain.precheckinAudit()

commPrecheckinDesignTimeMain = PrecheckinAuditTest(testIdCommDesignTimeMain, PrecheckinAuditTest.communityDesignTime, PrecheckinAuditTest.autoBuildNameMain, requestedRunCount)
commPrecheckinDesignTimeMain.precheckinAudit()

commPrecheckinRuntime224Patch = PrecheckinAuditTest(testIdCommRunTime224Patch, PrecheckinAuditTest.communityRuntime, PrecheckinAuditTest.autoBuildName224Patch, requestedRunCount)
commPrecheckinRuntime224Patch.precheckinAudit()

commPrecheckinDesignTime224Patch = PrecheckinAuditTest(testIdCommDesignTime224Patch, PrecheckinAuditTest.communityDesignTime, PrecheckinAuditTest.autoBuildName224Patch, requestedRunCount)
commPrecheckinDesignTime224Patch.precheckinAudit()
