import pandas as pd
import datetime
from collections import defaultdict
import numpy as np
import ts_anomaly_detection as esd

def detect(traces,kpis):
    df = process(traces)
    
    groups = df.groupby(['cmdb_id','serviceName'])
    print(list(df['cmdb_id'].unique()), list(df['serviceName'].unique()))
    table = pd.DataFrame(columns=sorted(list(df['cmdb_id'].unique())), index=sorted(list(df['serviceName'].unique())))
    # print(table)
    for group, groupdf in groups:
        # print(group)
        series = groupdf['elapsedTime'].resample('60S').mean()
        val = esd.esd_test(series, 6) # frequency should be different?
        # print(val[1])
        
        host, service = group
        table.at[service,host] = val[1]

    table = table.fillna(0)
    # print(table)

    threshold = table.values.max() / 2 # 50%
    # print(threshold)
    values = np.where(table.values > threshold)
    
    pairs = []
    pairs.append(list(map(lambda x: table.index[x], values[0])))
    pairs.append(list(map(lambda x: table.columns[x], values[1])))
    
    pairs = [x for x in zip(*pairs)]
    print(pairs)

    return analyze(pairs, kpis)

transitions = defaultdict(lambda: None ,{
    'redis_003':'os_003',
    'redis_001':'os_003',
    'redis_004':'os_003',
    'redis_002':'os_003',
    'redis_005':'os_004',
    'redis_006':'os_004',
    'redis_007':'os_004',
    'redis_008':'os_004',
    'redis_009':'os_005',
    'redis_010':'os_005',
    'redis_011':'os_005',
    'redis_012':'os_005',
    'docker_001':'os_017',
    'docker_002':'os_018',
    'docker_003':'os_019',
    'docker_004':'os_020',
    'docker_005':'os_017',
    'docker_006':'os_018',
    'docker_007':'os_019',
    'docker_008':'os_020',
})


def analyze(pairs, kpis):
    res = []
    dbs = list(filter(lambda x: 'db' in x[0], pairs))
    normal_servs = list(filter(lambda x: 'db' not in x[0], pairs))
    
    #network errors
    lines = defaultdict(int)
    for pair in normal_servs:
        lines[pair[0]] += 1

    #hosts to check KPIs
    columns = defaultdict(int)
    for pair in normal_servs:
        columns[pair[1]] += 1

    #containers to check KPIs
    containers = list(filter(lambda x: x[0] == x[1], normal_servs))

    def p(d):
        return map(lambda x: x[0], filter(lambda x: x[1] > 1, d.items()))

    networks = set([x for x in p(lines)])
    cmdbs = set([transitions[x] for x in p(columns)] + [x[0] for x in containers]) - networks
    
    dbs = [x[0] for x in dbs]

    vm = set(["os_001"]) if cmdbs and list(filter(lambda x: 'os' in x, cmdbs)) else set()

    # specific case
    # if csf needs to find one of the hosts 17-20
    csf_hosts = set(['os_017','os_018','os_019','os_020'])
    if any(map(lambda x: 'csf' in x[0], normal_servs)):
        cmdbs = cmdbs.union(csf_hosts)

    kpis = process_kpis(kpis)
    
    #one big list...
    result = []
    hosts = cmdbs.union(dbs).union(vm)
    kpis = dict(tuple(kpis.groupby('cmdb_id')))
    print('Checking ', hosts)
    for host in hosts:
        if host in kpis:
            kpidf = kpis[host]
            res = get_kpi_given_host(host, kpidf)
            result.extend([[host, kpi] for kpi in res])
        
    return [[host, None] for host in networks] + result


def process_kpis(kpis):
    kpis_df = kpis.copy(deep=True)
    kpis_df['timestamp'] = kpis_df['timestamp'].apply(lambda x: datetime.datetime.fromtimestamp(x/ 1000.0))
    kpis_df = kpis_df.set_index('timestamp')
    return kpis_df
    
def get_kpi_given_host(host, kpis):
    groups = kpis.groupby(['name'])
    # print(kpis)
    table = pd.DataFrame(columns=[host], index=sorted(list(kpis['name'].unique())))

    for group, groupdf in groups:
        series = groupdf['value'].resample('60S').mean()
        series = series.fillna(0)
        # print(group, series)
        val = esd.esd_test(series, 6) 
        kip_name = group
        table.at[group, host] = val[1]
    
    table = table.fillna(0)
    threshold = table.values.max() / 2 # 50%
    values = np.where(table.values > threshold)
    # print(values)
    try:
        return set(list(map(lambda x: table.index[x].values[0], values)))
    except:
        return set()



def process(traces):
    traces_df = traces.copy(deep=True)
    ids = traces_df[traces_df['callType'] == 'CSF']['id'].values

    traces_df['startTime'] = traces_df['startTime'].apply(lambda x: datetime.datetime.fromtimestamp(x / 1000.0))
    traces_df = traces_df.set_index('startTime')
    # print(traces_df)
    # print(ids)
    relationship = {}
    
    def parse(row):
        # parent -> child
        if row['callType'] == 'CSF' and row['pid'] in ids:
            # relationship[row['pid']] = row['cmdb_id']
            child_host = row['cmdb_id']
        else:
            child_host = ''

        # Following 4 lines only for running local tests
        # if row['callType'] in ['LOCAL','JDBC']:
        #          row['serviceName'] = row['dsName']
        # elif row['callType'] == 'OSB' or row['callType'] == 'RemoteProcess':
        #          row['serviceName'] = row['cmdb_id']
        
        if row['pid'] not in relationship:
            relationship[row['pid']] = [row['elapsedTime'], child_host]
        else:
            relationship[row['pid']][0] += row['elapsedTime']
        # relationship[row['pid']].append(row['elapsedTime'])

        return row

    def apply(row):
        # time of current becomes time of current minus children
        
        if row['id'] in relationship:
            row['elapsedTime'] = row['elapsedTime'] - relationship[row['id']][0]
        
        # Following 4 lines only for running local tests
        # if row['callType'] == 'LOCAL' or row['callType'] == 'JDBC':
        #     row['serviceName'] = row['dsName']
        # elif row['callType'] == 'OSB' or row['callType'] == 'RemoteProcess':
        #     row['serviceName'] = row['cmdb_id']
        
        # # parent -> new_parent
        if row['callType'] != 'CSF':
            return row
        else:
            if row['id'] in relationship and relationship[row['id']][1] != '':
                row['serviceName'] = relationship[row['id']][1]
            return row

    traces_df = traces_df.apply(parse, axis=1) # transform dsName
    return traces_df.apply(apply, axis=1)


if __name__ == '__main__':
    import sys
    path = sys.argv[1]
    import os
    anoms = []
    for file in os.listdir(path):
        print(file)
        kpis = pd.read_csv(path + '/' + file + '/kpi.csv')
        traces = pd.read_csv(path + '/' + file +'/trace.csv')
        # print("Kpi data has")
        # print(len(kpis), "rows", 'and', np.round((np.max(kpis['timestamp'])-np.min(kpis['timestamp']))/60000), "minute window size")
        # print("Trace data has")
        # print(len(traces), "rows", 'and', np.round((np.max(traces['startTime'])-np.min(traces['startTime']))/60000), "minute window size")

        anoms.append(detect(traces,kpis))
    print('Detected anomalies:', anoms)