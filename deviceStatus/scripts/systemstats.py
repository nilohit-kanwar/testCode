import urllib.request
import deviceInfo
from datetime import datetime as date
import subprocess
from os.path import exists
import csv
import json

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
        'connectivity': "False",
        'signal': 0
    }
    host = 'http://google.com'
    try:
        urllib.request.urlopen(host)
        connected = True
    except:
        connected = False

    if connected:
        ret['connectivity'] = "True"
    
    signal_str = subprocess.run("mmcli -m 0 | \
        awk '/signal quality/ {print $4}'", \
        shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('%\n')

    ret['signal'] = signal_str
    return ret

def data_usage_info():
    ret = {
        "ethernet": {
            "rx": 0,
            "tx": 0
        },
        "wwan": {
            "rx": 0,
            "tx": 0
        }
    }
    data = subprocess.run("vnstat -i eth0 --json y", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')
    try:
        dataj = json.loads(data)
        ret['ethernet']['rx'] = dataj["interfaces"][0]["traffic"]["total"]["rx"]/(1024*1024)
        ret['ethernet']['tx'] = dataj["interfaces"][0]["traffic"]["total"]["tx"]/(1024*1024)
    except:
        ret['ethernet']['rx'] = 0
        ret['ethernet']['tx'] = 0

    data = subprocess.run("vnstat -i wwan0 --json y", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')

    try:
        dataj = json.loads(data)
        ret['wwan']['rx'] = dataj["interfaces"][0]["traffic"]["total"]["rx"]/(1024*1024)
        ret['wwan']['tx'] = dataj["interfaces"][0]["traffic"]["total"]["tx"]/(1024*1024)
    except:
        ret['wwan']['rx'] = 0
        ret['wwan']['tx'] = 0

    return ret

def power_info():
    ret = {
            "battery_temp": 0,
            "voltage": 0,
            "avg_current": 0,
            "current": 0
        }

    if(exists("/tmp/battery_parameters")):
        temp = subprocess.run("cat /tmp/battery_parameters | awk '/Temperature/ {print $3}'", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')
        temp = float(temp)

        voltage = subprocess.run("cat /tmp/battery_parameters | awk '/Voltage/ {print $3}'", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')
        voltage = float(voltage)/1000

        avg_current = subprocess.run("cat /tmp/battery_parameters | awk '/Average Current/ {print $4}'", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')
        avg_current = float(avg_current)/1000

        current = subprocess.run("cat /tmp/battery_parameters | awk 'NR == 4 {print $3}'", shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout.rstrip('\n')
        current = float(current)/1000

        ret['battery_temp'] = temp
        ret['voltage'] = voltage
        ret['avg_current'] = avg_current
        ret['current'] = current

        return ret
    else:
        return ret

def get_allinfo():
    getCpu = cpu_info()
    getGpu = gpu_info()
    getRam = ram_info()
    getGeneral = general_info()
    getInternet = internet_info()
    getData = data_usage_info()
    getPower = power_info()

    ret = {
        "time" : date.isoformat(date.now()),
        "cpuInfo": getCpu,
        "gpuInfo": getGpu,
        "ramInfo": getRam,
        "generalInfo": getGeneral,
        "internet": getInternet,
        "dataInfo": getData,
        "powerInfo": getPower
    }

    return ret

if __name__ == '__main__':

    while True:
        if (exists("/media/mmcblk1p1/devicestats.csv")):
            status = get_allinfo()
            # write to file every 10 seconds
            if (((date.now().second)%10) == 0):
                with open(f"/var/tmp/devicestats", 'w') as file:
                    json.dump(status, file, indent=4, separators=(',', ':'))
            
            # write to file every 60 seconds
            if (((date.now().second)%60) == 0):
                with open('/media/mmcblk1p1/devicestats.csv', mode='a') as csv_file:
                    fieldnames = ['Date', 'Time', 'Battery-Temp', 'Voltage', 'Avg-Current', 'Current', 'CPU-Usage', 'A53-Temp', 'A53-0-Usage', 'A53-1-Usage', 'A53-2-Usage', 'A53-3-Usage', 'A72-Temp', 'A72-0-Usage', 'A72-1-Usage', 'GPU0-Temp', 'GPU1-Temp', 'GPU-Usage', 'RAM-Usage', 'Ethernet-RX', 'Ethernet-TX', 'WWAN-RX', 'WWAN-TX']
                    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                    writer.writerow({'Date': date.today().strftime("%d/%m/%Y"), 'Time': date.now().strftime("%H:%M:%S"), 'Battery-Temp': status['powerInfo']['battery_temp'], 'Voltage': status['powerInfo']['voltage'], 'Avg-Current': status['powerInfo']['avg_current'], 'Current': status['powerInfo']['current'], 'CPU-Usage': status['cpuInfo']['usage'], 'A53-Temp':status['cpuInfo']['temperatures']['A53'], 'A53-0-Usage': status['cpuInfo']['usageDetailed']['A53-0'], 'A53-1-Usage': status['cpuInfo']['usageDetailed']['A53-1'], 'A53-2-Usage': status['cpuInfo']['usageDetailed']['A53-2'], 'A53-3-Usage': status['cpuInfo']['usageDetailed']['A53-3'], 'A72-Temp': status['cpuInfo']['temperatures']['A72'], 'A72-0-Usage': status['cpuInfo']['usageDetailed']['A72-0'], 'A72-1-Usage': status['cpuInfo']['usageDetailed']['A72-1'], 'GPU0-Temp': status['gpuInfo']['temperatures']['GPU0'], 'GPU1-Temp': status['gpuInfo']['temperatures']['GPU0'], 'GPU-Usage': status['gpuInfo']['memoryUsage'], 'RAM-Usage': status['ramInfo']['usage'], 'Ethernet-RX':status['dataInfo']['ethernet']['rx'], 'Ethernet-TX': status['dataInfo']['ethernet']['tx'], 'WWAN-RX': status['dataInfo']['wwan']['rx'], 'WWAN-TX': status['dataInfo']['wwan']['tx']})

        else:
            with open('/media/mmcblk1p1/devicestats.csv', mode='w') as csv_file:
                fieldnames = ['Date', 'Time', 'Battery-Temp', 'Voltage', 'Avg-Current', 'Current', 'CPU-Usage', 'A53-Temp', 'A53-0-Usage', 'A53-1-Usage', 'A53-2-Usage', 'A53-3-Usage', 'A72-Temp', 'A72-0-Usage', 'A72-1-Usage', 'GPU0-Temp', 'GPU1-Temp', 'GPU-Usage', 'RAM-Usage', 'Ethernet-RX', 'Ethernet-TX', 'WWAN-RX', 'WWAN-TX']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
