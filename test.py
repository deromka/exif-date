#!/usr/bin/env python

import os,sys,json,re,datetime,collections

env_props_file = dict(drm_tierId=70144,
            drms_chipIdToStbIdConversionFactor=0x0,
            sgp_SdllgFacade='SdllgFacade',
            sgp_tcpClienthost=['10.0.0.1','10.0.0.2', '10.0.0.3'],
            drms_cmcmProxy='drmsDkmAdaptor',
            upm_host='undef',
            drms_sacchipBasedenable='true',
            ssh_chipType=0x10B8,
            service_sshhost='undef',
            sensu_server_host='sensu-server')


fragmentJson= [
    "set service.DrmsPcServlet.http.port 6081"
    ,"set service.SacServer.http.port 6080"
    ,"set httpClient.keyStore.1.port 6341"
    ,"set ssa.FE.enable %{ssa_enabled}"
    ,"set channelsCacheManager.httpClient.ecms.1.host %{ecms_host}"
    ,"set httpClient.keyStore.1.host %{keystore_host}"
    ,"set sgp.SdllgFacade %{sgp_SdllgFacade}"
    ,"set sgp.tcpClient.1.port 1113"
    ,"set sgp.tcpClient.1.host %{sgp_tcpClienthost}"
    ,"set sgp.tcpClient.1.timeout 3000"
    ,"set service.ssh.1.host %{service_sshhost}"
    ,"set httpClient.concurrencySrv.1.host %{cdl_host}"
    ,"set httpClient.concurrencySrv.1.port 6730"
    ,"set dkm.ReportDeviceFeatureName %{drms_reportDeviceFeature}"
    ,"set dkm.persistencyReportDevice.httpclient.0.host %{upm_host}"
    ,"set dkm.persistencyReportDevice.httpclient.0.port 6040"
    ,"set drms.sac.chipBased.enable %{drms_sacchipBasedenable}"
    ,"set ssh.chipType %{ssh_chipType}"
    ,"set service.mxagentRegistry.monitoringEnabled %{drms_monitoring}"
    ,"set service.DrmsPcServlet.http.monitoringFilter.isEnabled %{drms_monitoring}"
    ,"set service.SacServer.http.monitoringFilter.isEnabled %{drms_monitoring}"
]

tokenPattern=re.compile("\%\{(\w+)\}")
def getToken(string):
    m = tokenPattern.search(string)
    if m:
        return m.group(1)
    else:
        return None


def saveFragmentProperties(fragmentJson, props):
    env_set = set()
    #print props
    for elem in fragmentJson:
        upd = elem.strip().replace("set ","",1).strip().replace(" ","=",1)
        key = getToken(upd)
        if key is None or not key:
            env_set.add(upd)
        else:
            value=props.get(key)
            if value is not None:
                # test for multiple values
                if isinstance(value, list) and (("0.host" in upd) or ("1.host" in upd)):
                    origIndex = 0 if "0.host" in upd else 1
                    m = re.search("(.*){0}\.host".format(origIndex), upd)
                    prefix=m.group(1)
                    index = origIndex
                    for val in value:
                        env_set.add(upd.replace("{0}.host".format(origIndex), "{0}.host".format(index),1).replace("%{"+key+"}",val,1))
                        for item in fragmentJson:
                            if prefix in item and "{0}.host".format(origIndex) not in item:
                                env_set.add(item.strip().replace("set ","",1).strip().replace(" ","=",1).replace("{0}{1}.".format(prefix, origIndex), "{0}{1}.".format(prefix,index),1))
                        index+=1
                else:
                    env_set.add(upd.replace("%{"+key+"}",str(value),1))
    outfile = open("test1", 'w')
    outfile.write("\n".join(env_set))
    outfile.close()



def main(argv):
    saveFragmentProperties(fragmentJson, env_props_file)


if __name__ == "__main__":
    main(sys.argv[1:])
