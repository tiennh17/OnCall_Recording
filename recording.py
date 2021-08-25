# -*- coding: utf8 -*-
from datetime import datetime
from datetime import timedelta
import urllib.request
import os
import requests
import pymongo
from requests.api import request
from minio import Minio
from minio.error import S3Error
import json


class recording:

    def __init__(self):
        self.id = ""
        self.filename = ""
        self.filename_new = ""
        self.filepath = ""
        self.filepath_new = ""
        self.caller = ""
        self.callee = ""
        self.start_time = ""
        self.end_time = ""
        self.duration = ""
        self.status = ""

    def set_recording(self,id,filename,filename_new,filepath,filepath_new,caller,callee,start_time,end_time,duration,status):
        self.id = id
        self.filename = filename
        self.filename_new = filename_new
        self.filepath = filepath
        self.filepath_new = filepath_new
        self.caller = caller
        self.callee = callee
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.status = status      

    def get_path(self):
        return self.filepath  

    def get_name(self):
        return self.filename

    def get_recording(self):
        return (self.id,self.filename,self.filename_new,self.filepath,self.filepath_new,self.caller,self.callee,self.start_time,self.end_time,self.duration,self.status)

    def print_recording(self):
        print(self.filename)
        print(self.filepath)

def timenow():
    time_now = datetime.now()
    return time_now

def timeback(day):
    now = timenow()
    before_time = (now - timedelta(days = day))
    return before_time

def download(url,path):
    try:
        urllib.request.urlretrieve(url,path)
        return True
    except urllib.ValueError as error:
        print (error)
        f_out.write("-------download fail recording name: " + path + " with error code " + error + "-------")
        return False

def getToken(user_name,password):
    try:
        url = 'http://118.68.169.39:8899/api/account/credentials/verify'
        header = {
          "Content-Type": "application/json"
        }
        # authen = '''{
        #         "name":"test01",
        #         "password":"hSu!~7fN"
        # "password":"Crv@fti2021"}'''
        authen = '''{"name":"''' + user_name + '",' + '''"password":"''' + password + '''"}'''
        print(authen)
        result = requests.post(url, headers = header,data = authen)
        response = result.json()
        access_token = ""
        if result.status_code == 200:
            access_token = response['access_token']
            print(access_token)
            return access_token
        else:
            print(result.status_code)
            print("Fail to get access_token !!!")
            return access_token
    except requests.exceptions.RequestException as error:
        print (error)
        return False

def collect_listRecording(token,start_time,end_time,pagesize):
    try:
        access_token = token
        #day_collect = day
        #end = timenow().strftime("%Y-%m-%d %H:%M:%S")
        #start = timeback(day_collect).strftime("%Y-%m-%d %H:%M:%S")
        end = end_time
        start = start_time
        pagesize_collect = pagesize
        pagination = 1
        #list_recording = []
        list_response = []
        list_callleg = []
        #cdr_recording = recording()
        if access_token !="" :
            while (True):
                f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Start run API collect list recording-----\n")
                url = 'http://118.68.169.39:8899/api/recordfiles/extension/list?start_time=' + start + '&end_time=' + end + '&pagination=' + (str)(pagination) + '&pagesize=' + (str)(pagesize_collect)
                print("request url : "  +url )
                header = {
                    "Content-Type": "application/json",
                    "access_token": access_token
                }
                result = requests.get(url, headers = header)
                if result.status_code == 200:
                    print("-------du lieu cuoc goi trang " + (str)(pagination) + " ----------")
                    response = result.json()
                    print("số lượng record trả về : " + str(response['count']))
                    #xu ly collect cdr neu la trang cuoi
                    if response['count'] < pagesize_collect :
                        print("--------Đây là trang CDR cuối---------")
                        pagesize_last =  response['count']
                        list_response.append(response['records'])
                        record_page = response['records']
                        print(type(list_response))
                        print(len(list_response))    
                        #db_recording.oncall_record.insert_many(record_page)                    
                        for i in range(pagesize_last) :
                            # id = response['records'][i]['id']
                            filename = response['records'][i]['filename']
                            filepath = response['records'][i]['filepath']
                            tmp_obj = filepath,filename
                            list_path.append(tmp_obj) 
                        break
                    #xu ly collect cdr tung trang
                    else:
                        list_response.append(response['records'])
                        print(type(list_response))
                        print(len(list_response))
                        record_page = response['records']
                        #db_recording.oncall_record.insert_many(record_page)                          
                        for i in range(pagesize_collect) :
                            # id = response['records'][i]['id']
                            filename = response['records'][i]['filename']
                            filepath = response['records'][i]['filepath']
                            tmp_obj = filepath,filename
                            list_path.append(tmp_obj)                                    
                        pagination += 1                 
                else:
                    print(result.status_code)
                    print("Fail to get list recording !!!")
                    f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Collect recording fail at page " +  (str)(pagination) + " with Reason : "+ (str)(result.status_code) + "\n")
                    return list_response
            f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Collect list recording successfully-----\n")
            return list_response               
    except requests.exceptions.RequestException as error:
        print (error)
        f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Collect recording fail with exception error  " + (str)(error) + "\n")
        return list_response             

def connectMinIO(server,access_key, secret_key):
    f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Start Connect MinIO server-----\n")
    client = Minio(
        #"118.68.171.191:9000",
        #"play.min.io",
        server,
        access_key = access_key,
        secret_key = secret_key,
        # access_key="Q3AM3UQ867SPQQA43P2F",
        # secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TY",
        secure=False,
    )
    return client

def putFileMinIO(client,bucket,filename,filepath):
    try:
        client.fput_object(
        bucket, filename, filepath,
        )
        print(
        filename  + " is successfully uploaded as "
        "to bucket "  + bucket
        )
    except S3Error as exc:
        f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----error occurred upload object to MinIO: ", exc)

def insertRecord(connetion,db,listRecord):
    f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Start insert recording-----\n")
    db = connetion.oncall_record
    for page_record in listRecord :
       insert_record = db.document.insert_many(page_record)

def getInfoTenant(connection,db):
    f_out.write((timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Start get infoTenant DB----- ") + db +("\n"))
    collection = connection[db]
    document = collection.settings.find()
    InfoTenant = []
    for k in document:
        #print(k['value'])
        InfoTenant.append(k['value'])
    if len(InfoTenant) !=0 :
        return InfoTenant
    else:
       f_out.write(timenow().strftime("%Y-%m-%d %H:%M:%S") + "-----Fail get infoTenant DB----- ") + db +("\n")  


if __name__ == "__main__" :
    # token = getToken("test01","hSu!~7fN")
    # token = getToken("CRV","Crv@fti2021")
    # print(token)
    global f_out
    f_out = open("/home/OnCall/log/log_recording.txt","a+") 
    global list_path
    tmp_pathStorage = ""
    tmp_pathStorage = "/home/OnCall/recording/"
    #global db_recording
    list_path = []
    clientMinIO = connectMinIO("118.68.171.191:9000","Q3AM3UQ867SPQQA43P2F","zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TY")
    clientMogo = pymongo.MongoClient("mongodb://admin:Fti%40dmin%21%40%23123@118.69.192.97:27017/?authSource=admin")
    #clientMogo = pymongo.MongoClient("mongodb://fwork:FWork%40123@mongo.dev.fpt.work:27017/?authSource=admin&readPreference=primary&appname=MongoDB%20Compass&directConnection=true&ssl=false")
    #db_recording = clientMogo['oncall_recording']
    dbs = clientMogo.list_database_names()
    for db in dbs :
        if db[0:2] == 'FO':#DB dich vu OnCall
            count = 0
            InfoTenant = getInfoTenant(clientMogo,db)
            print(InfoTenant)
            token = getToken(InfoTenant[0],InfoTenant[1])
            start_time = timeback(1).strftime("%Y-%m-%d %H:%M:%S")
            end_time = timenow().strftime("%Y-%m-%d %H:%M:%S")
            #list_record = collect_listRecording(token,start_time,end_time,100)
            list_record = collect_listRecording(token,"2021-08-25 14:00:00","2021-08-25 17:00:59",100)
            db_recording = clientMogo[db]
            for page_record in list_record :
                insert_record = db_recording.oncall_record.insert_many(page_record)
            for record in list_path :
                url = "http://file.oncall.vn/" + str(record[0])
                if (download(url,tmp_pathStorage + str(record[1]))) == False:
                    continue
                else: 
                    count += 1
                    putFileMinIO(clientMinIO,"oncall2",str(record[1]),tmp_pathStorage + str(record[1]))
            print("\nso luong recording download success: ",count)
        else:
            continue
    #db_recording = clientMogo.oncall_recording    
    #list_path = []
    #f_out = open("log_recording.txt","a+")
    #list_record = collect_listRecording(token,"2021-07-19 00:00:00","2021-07-19 09:00:00",100)
    #print(list_path)
    #print(type(list_record))
    #print(type(list_path))
    #print(len(list_record))
    #print(list_path[2])
    # for record in list_path :
    #     url = "http://file.oncall.vn/" + str(record[0])
    #     if (download(url,"D:\\Recording_OnCall\\" + str(record[1]))) == False:
    #         continue
    #     else: 
    #         putFileMinIO(clientMinIO,"recordingoncall",str(record[1]),"D:\\Recording_OnCall\\" + str(record[1]))
#xoa file cu hon x ngay

    #db_recording.oncall_record.delete_many({})
    ## for page_record in list_record :
    ##     insert_record = db_recording.oncall_record.insert_many(page_record)