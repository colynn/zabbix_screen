#!/usr/bin/env python
import sys
import getpass

sys.path.append('./lib')

from zabbix_api import ZabbixAPI, ZabbixAPIException

url = 'https://zabbix-qa.service.chinanetcloud.com'
zapi = ZabbixAPI(server=url)
graph_width = '200'
graph_height = '100'

CustomerName=raw_input('Customer Name:')
Username=raw_input('Zabbix Username:')
Password=getpass.getpass('Zabbix Password:')

def Login():
    try:
        zapi.login(Username, Password)
    except ZabbixAPIException, e:
        print("Error:Name or Password is wrong")
        sys.exit(1)
def GetHostID():
    try:
        GroupID = zapi.hostgroup.get({ "output": "groupid", "filter": { "name": CustomerName} })[0]['groupid']
    except IndexError as msg:
        print ("Unable find the customer : %s" % CustomerName)
        sys.exit(1)
    HostIDs=zapi.host.get({ "output": "hostid", "groupids" : [ GroupID ]})
    if len(HostIDs) == 0:
        print "No server find in group %s" % CustomerName
        sys.exit(2)
    hostids=[]
    for i in HostIDs:
        hostids.append(i['hostid'])
    return hostids
def getGraphs(hostid):
    graphs = {}
    selected = '0'
    for graph in zapi.graph.get({ "output": "extend", "hostids":hostid }):
        graphs[graph['name']] = (graph['graphid'], selected)
    return graphs
def graphsForScreens(hosts):
    if not hosts:
        print "hosts list is empty, exit..."
        sys.exit(1)
    graphs_stand_list = [ 'CPU %', 'Memory Usage','IOStat', 'Ethx Network Traffic', 'nginx', 'MySQL Connections', 'Tomcat*Sessions','Vmstat Swap In-Out']
    graphs_dict = {}
    for hostid in hosts:
        host_graphs_list = []
        graphs = getGraphs(hostid)
        graphsKeys = graphs.keys()
        for key in graphsKeys:
            for g in graphs_stand_list:
                g_list = g.split("*")
                if len(g_list) == 2:
                    if ( g_list[0] in key ) and ( g_list[1] in key) :
                        host_graphs_list.append(graphs[key][0])
                else:
                    if g_list[0] in key:
                        host_graphs_list.append(graphs[key][0])
        # host graphs is empty
        if not host_graphs_list:
            continue
        graphs_dict[hostid] = host_graphs_list
    return graphs_dict
def CreateScreen(screen_name, HostList):
    screen_name='~Customer - ' + screen_name
    # Check if Screen exist
    result = zapi.screen.exists({"name":screen_name})
    if result:
        print "\nScreen %s already exists." % screen_name
        sys.exit(1)
    screen_vsize = len(HostList)
    num = []
    for i in HostList:
         num.append(len(HostList[i]))
    screen_hsize = max(num)
    zapi.screen.create({"name": screen_name, "hsize": screen_hsize, "vsize": screen_vsize})
    screenid = zapi.screen.get({ "output": "screenid", "filter": { "name": screen_name} })[0]['screenid']
    y = 0
    for h in HostList:
        x = 0
        for g in range(0,len(HostList[h])):
            screen_items = {"screenid": screenid,
                            "resourcetype": 0,
                            "resourceid": HostList[h][g],
                            "width": graph_width,
                            "height": graph_height,
                            "x": x,
                            "y": y
                            }
            zapi.screenitem.create(screen_items)
            x += 1
        y += 1

    print "Successfully create Screen %s!" % screen_name

if __name__=='__main__':
    Login()
    HostIDs=GetHostID()
    HostList=graphsForScreens(HostIDs)
    CreateScreen(CustomerName, HostList)
