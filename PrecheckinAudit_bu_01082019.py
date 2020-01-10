import requests
import json
import pprint
#import certifi
#certifi.where()
#'/Library/Frameworks/Python.framework/Versions/3.8/lib/python3.8/site-packages/certifi/cacert.pem'

#AutobuildId main_precheckin: 4869
#AutobuildId 224_patch_precheckin: 28001 (main -2 precheckin, aka will this id remain the same?)
#TestId main: testNapiliHomeAndLogin(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 70123236
#TestId 224 patch: testNapiliHomeAndLogin(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 259252737
#TestId main: testVerifyBuilderLoads(ui.aura.components.selfservice.sites.NapiliPrecheckinTest): 70197630


class PrecheckinAudit:

    # the api endpoint.  we will format/merge the testId we wabt to audit and the runCount (how many runs we want to audit)
    apiEndPoint = 'https://lunadas.prod.ci.sfdc.net/api/results/v1/q/test-history?test-id={testId}&show-skipped-runs=true&load-all=false&start-index=0&row-count={runCount}'

    ## slack - post to a 'webhook url'.  Create one from the slack api 'Incoming Webhooks' while signed in to salesforce slack.  https://api.slack.com/apps/ASAL2RZSB/incoming-webhooks?success=1
    eric_webhook_url = 'https://hooks.slack.com/services/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'
    app_webhook_url = 'https://hooks.slack.com/services/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'
    precheck_webhook_url = 'https://hooks.slack.com/services/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'
    ##q3_webhook_url = 'https://hooks.slack.com/services/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'
    
    # initializer / instance attributes
    def __init__(self, testId, autoBuildName, runCount):
        
        if runCount == None:
            self.runCount = 50
        else:
            self.runCount = runCount

        self.url = PrecheckinAudit.apiEndPoint.format(testId=testId, runCount=runCount)
        self.autoBuildName = autoBuildName
        self.testId = testId
        self.successCount = 0
        self.failCount = 0
        self.runTimeList = []
        self.runTimesTotal = 0
        self.response = None
        self.precheckins = []
        self.failPrecheckins = []
        self.averageRunTime = 0;
        self.testName = ''


    def precheckinAudit(self):
        self.response = requests.get(self.url, verify=False)
        self.precheckins = json.loads(self.response.text)
        # print(self.response.text)





        # mock failures to test failure reporting
##        self.failPrecheckins.append({
##            'owner': 'ewulff',
##            'changelist': 'cl fubar123',
##            'running-time': 428,
##            'uniqueTestName': 'testDesignTime'
##            })
##
##        self.failPrecheckins.append({
##            'owner': 'ewulff',
##            'changelist': 'cl fubar456',
##            'running-time': 475,
##            'uniqueTestName': 'testDesignTime'
##            })





        # make it a function/method 
        # process precheckins audit data
        for precheckin in self.precheckins:
            runTimeStr = precheckin["running-time"]

            # make it a function/method - strip the 's' from the end and turn it back to an int
            runTimeStrLen = len(runTimeStr)
            runTime = int(runTimeStr[:(runTimeStrLen - 1)])

            self.runTimesTotal += runTime
            self.runTimeList.append(runTime)

            if precheckin["status"] == "SUCCESS":
                self.successCount += 1

            # if we find a precheckin failure, then parse and append cl data
            if precheckin["status"] == "FAILURE":
                self.failCount += 1
                self.failPrecheckins.append({
                    'owner': precheckin["owner"],
                    'changelist': precheckin['changelist'],
                    'running-time': precheckin['running-time'],
                    'uniqueTestName': precheckin['uniqueTestName']
                })

        self.averageRunTime = self.runTimesTotal / len(self.runTimeList)

        self.testName = ''
        # get and set the test name
        if (len(self.precheckins) >= 1):
            self.testName = self.precheckins[0]['uniqueTestName']

        self.precheckinAuditResult = "precheckin test: " + self.autoBuildName + " - " + self.testName + ": " \
            + "run count: " + str(self.runCount) + "; " \
            + "average runtime: " + str(self.averageRunTime)[:3] + "s; " \
            + "success count: " + str(self.successCount) + "; " \
            + "failure count: " + str(self.failCount)

        # build the test failures text string
        self.testFailures = ''
        for failPrecheckin in self.failPrecheckins:

            # format: prepend with 'failures'
            if (len(self.testFailures) == 0):
                self.testFailures += "**failures: "

            # format: add a comma between test failures
            if (len(self.testFailures) > 0):
                self.testFailures += ", "

            # content: add a precheckin failure's info
            self.testFailures += str(failPrecheckin)

        # trim the comma from the end of the test failures test string
        # add the test failures string to the precheckin audit result text string
        if (len(self.testFailures) > 0):
##            self.testFailures = str(self.testFailures)[:len(self.testFailures) - 1]
            self.precheckinAuditResult += self.testFailures

        self.slack_data = {'text': self.precheckinAuditResult}
##        print(self.slack_data)
        requests.post(PrecheckinAudit.precheck_webhook_url, json=self.slack_data)


runCount = 50
autoBuildNameMain = 'main'
autoBuildName224Patch = '224Patch'

testIdCommRunTimeMain = str(70123236)
testIdCommDesignTimeMain = str(70197630)
testIdCommRunTime224Patch = str(259252737)
testIdCommDesignTime224Patch = str(259252984)

commPrecheckinRuntimeMain = PrecheckinAudit(testIdCommRunTimeMain, autoBuildNameMain, runCount)
commPrecheckinRuntimeMain.precheckinAudit()

commPrecheckinDesignTimeMain = PrecheckinAudit(testIdCommDesignTimeMain, autoBuildNameMain, runCount)
commPrecheckinDesignTimeMain.precheckinAudit()

commPrecheckinRuntime224Patch = PrecheckinAudit(testIdCommRunTime224Patch, autoBuildName224Patch, runCount)
commPrecheckinRuntime224Patch.precheckinAudit()

commPrecheckinDesignTime224Patch = PrecheckinAudit(testIdCommDesignTime224Patch, autoBuildName224Patch, runCount)
commPrecheckinDesignTime224Patch.precheckinAudit()
