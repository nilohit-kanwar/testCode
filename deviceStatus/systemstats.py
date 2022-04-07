import urllib.request
import json
import deviceInfo
from datetime import datetime as date
import sys
import time

deviceInfo = deviceInfo.DeviceInfo()

def cpu_info():
    ret = {
        'temperatures': {
            'A53': 0.0,
            'A72': 0.0
        },
        'usage': 0.0,
        'usageDetailed': {
            'A53-0': 0.0,
            'A53-1': 0.0,
            'A53-2': 0.0,
            'A53-3': 0.0,
            'A72-0': 0.0,
            'A72-1': 0.0
        }
    }
    
    ret['temperatures'] = {
        'A53': deviceInfo.getTemperatureCPUA53(),
        'A72': deviceInfo.getTemperatureCPUA72()
    }

    ret['usage'] = deviceInfo.getCPUUsage()

    det = deviceInfo.getCPUUsageDetailed()
    ret['usageDetailed'] = {
        'A53-0': det[0],
        'A53-1': det[1],
        'A53-2': det[2],
        'A53-3': det[3],
        'A72-0': det[4],
        'A72-1': det[5],
    }

    return ret

def gpu_info():
    ret = {
        'cores': 2, 
        'temperatures': [],
        'memoryUsage': deviceInfo.getGPUMemoryUsage()
    }
    
    ret['temperatures'] = {
        'GPU0': deviceInfo.getTemperatureGPU0(),
        'GPU1': deviceInfo.getTemperatureGPU1()
    }

    return ret

def ram_info():
    ret = {
        'total': deviceInfo.getRAMTotal(), 
        'usage': deviceInfo.getRAMUsage(),
        'free': deviceInfo.getRAMFree()
    }

    return ret

def general_info():
    ret = {
        'board-serial': deviceInfo.getTdxSerialNumber(),
        'board-type': deviceInfo.getTdxProductID(),
        'board-revision': deviceInfo.getTdxProductRevision()
    }
    
    return ret

def internet_info():
    ret = {
        'connectivity': "False"
    }
    host = 'http://google.com'
    try:
        urllib.request.urlopen(host)
        connected = True
    except:
        connected = False

    if connected:
        ret['connectivity'] = "True"
    
    return ret

def get_allinfo():
    getCpu = cpu_info()
    getGpu = gpu_info()
    getRam = ram_info()
    getGeneral = general_info()
    getInternet = internet_info()

    ret = {
        "time" : date.isoformat(date.now()),
        "cpuInfo": getCpu,
        "gpuInfo": getGpu,
        "ramInfo": getRam,
        "generalInfo": getGeneral,
        "internet": getInternet
    }

    return ret

if __name__ == '__main__':

    while True:
        status = get_allinfo()

        try: 
            with open(f"/home/root/ws/config.conf", 'r') as file:
                data = json.load(file)
                ramInterval = data["configuration"]["RAMUPDATE"]
                diskInterval = data["configuration"]["DISKUPDATE"]
        except FileNotFoundError:
            sys.stderr.write("Config File Not found")

        minute = date.now().minute

        if(minute % ramInterval) == 0:
            try: 
                with open(f"/tmp/deviceStatus.conf", 'w') as file:
                    json.dump(status, file, indent=4, separators=(',', ':'))            
                    print("ram written")
            except:
                sys.stderr.write("Ram Exception")

        if(minute % diskInterval) == 0:
            try:
                with open(f"/var/tmp/deviceStatus.conf", 'a') as file:
                    json.dump(status, file, indent=4, separators=(',', ':'))
                    print("disk written")
            except:
                sys.stderr.write("Disk Exception")
        
        time.sleep(10)