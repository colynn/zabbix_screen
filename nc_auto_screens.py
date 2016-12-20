#!/usr/bin/env python
import sys
import getpass

sys.path.append('./lib')

from zabbix_api import ZabbixAPI, ZabbixAPIException

url = 'https://zabbix.service.examplecloud.com'
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
    hosts.sort()
    if not hosts:
        print "hosts list is empty, exit..."
        sys.exit(1)
    graphs_stand_list = [ 'CPU %', 'Memory Usage','IOStat', 'Vmstat Swap In-Out', 
                        'Ethx Network Traffic',
                        'Nginx', 'Apache', 'PHP-FPM Processes',
                        'MySQL*Connections', 'MySQL*Queries', 'MySQL*InnoDB',
                        'Tomcat*Heap Memory usage', 'Tomcat*Worker Threads', 'Tomcat*Sessions',
                        'Java*Heap Memory usage', 'Java*Worker Threads', 'Java*Sessions',
                        'HaProxy back/front session',
                        'Redis*Connections',
                        'Memcache*Connections',
                        'MongoDB*Queries-Requests', 'MongoDB*Connections', 'MongoDB*Performance'
                        'Postgres*Connections', 'Postgres*Cache Hit/Read'
                        ]
    try:
        from collections import OrderedDict
    except ImportError:
        from ordereddict import OrderedDict
    graphs_dict = OrderedDict()

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
        host_graphs_list.sort()
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

    print "Successfully Create Screen: %s!" % screen_name


def delete_screen(screen_name, HostList):
    screen_name = '~Customer - ' + screen_name
    # Check if Screen exist
    result = zapi.screen.exists({"name": screen_name})
    if not result:
        info = 1
        print screen_name + " not exists "
    screen_id = zapi.screen.get({"output": "screenid", "filter": {"name": screen_name}})[0]['screenid']
    screen_arr = [screen_id]
    try:
        info = zapi.screen.delete(screen_arr)
    except ZabbixAPIException, e:
        info = e
    if type(info) == "tuple":
        print "failed, " + e 
    else:
        print "okay."

if __name__=='__main__':
    Login()
    HostIDs=GetHostID()
    HostList=graphsForScreens(HostIDs)
    CreateScreen(CustomerName, HostList)
    # delete_screen(CustomerName, HostList)
