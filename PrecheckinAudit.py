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
##        print(self.response.text)

        # make it a function/method
        for precheckin in self.precheckins:
            runTimeStr = precheckin["running-time"]

            # make it a function/method - strip the 's' from the end and turn it back to an int
            runTimeStrLen = len(runTimeStr)
            runTime = int(runTimeStr[:(runTimeStrLen - 1)])

            self.runTimesTotal += runTime

            self.runTimeList.append(runTime)
            if precheckin["status"] == "SUCCESS":
                self.successCount += 1
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
        if (len(self.precheckins) >= 1):
            self.testName = self.precheckins[0]['uniqueTestName']
            print("precheckin test: " + self.autoBuildName + ': ' + self.testName)

        print("precheckin run count: " + str(self.runCount))
        print("precheckin average runtime len: " + str(self.averageRunTime)[:3])
        print("precheckin success count: " + str(self.successCount))
        print("precheckin failure count: " + str(self.failCount))


        #lFailPrecheckins = json.loads(failPrecheckins)
        #pp = pprint.PrettyPrinter()
        #pp.pprint(failPrecheckins)

        for failPrecheckin in self.failPrecheckins:
            print("  **failure: " + str(self.failPrecheckin))


runCount = 25
autoBuildNameMain = 'main';
autoBuildName224Patch = '224Patch';

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
