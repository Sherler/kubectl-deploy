import sys
import argparse
from yaml import load,dump,dump_all

#加载yaml文件
def load_config_file(filedir):
    with open(filedir,'r') as stream:
        return load(stream)

#写yaml到文件或打印
def dump_new_file(data,fileDir=None):
    if fileDir is not None:
        with open(fileDir,'w') as stream:
            dump_all(data,stream, default_flow_style=False)
    else:
      print(dump_all(data, default_flow_style=False))

#根据stage判断应当部署的namespace
def namespace_by_stage(stage):
    if stage == "production":
        return "wenwen"
    elif stage == "grey":
        return "wenwen"
    else:
        return "default"


basic_configmap_str = '''
kind: ConfigMap
apiVersion: v1
metadata:
  name: unknown
  namespace: unknown
'''
def as_configmap(data,stage='stage'):
    config = load(basic_configmap_str)#基本结构
    
    #元数据
    config['metadata']['name'] = data['projectName']+"-config"
    config['metadata']['namespace'] = namespace_by_stage(stage)

    #默认详细配置移入
    if data.get('configMapData',None) is not None:
        config['data'] = data['configMapData']
    else:
        return {}

    #按stage填写差异化信息
    if data.get(stage, None) is not None:
        if data[stage].get('namespace',None) is not None:   
            config['metadata']['namespace'] = data[stage]['namespace']

        if data[stage].get('configMapData',None) is not None:  
            config['data'] = data[stage]['configMapData']

basic_deploy_str = '''
apiVersion: apps/v1
kind: Deployment
metadata:
  name: unknown
  labels:
    app: unknown
spec:
  replicas: 1
  strategy:   
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1 
      maxUnavailable: 1
  selector:
    matchLabels:
      app: unknown
      stage: unknown
  template:
    metadata:
      labels:
        app: unknown
        stage: unknown
'''
#生成Deployment或者StatefulSet配置
def as_deploy(data,image,stage='test'):
    deploy = load( basic_deploy_str )#基本结构
    
    #基本元数据填写
    deploy['metadata']['name'] = data['projectName']+'-'+stage
    deploy['metadata']['labels']['app'] = data['projectName']
    deploy['metadata']['namespace'] = namespace_by_stage(stage)
    
    #选择器标签
    deploy['spec']['selector']['matchLabels']['app'] = data['projectName']
    deploy['spec']['selector']['matchLabels']['stage'] = stage
    deploy['spec']['template']['metadata']['labels']['app'] = data['projectName']
    deploy['spec']['template']['metadata']['labels']['stage'] = stage
 
    #容器配置信息填写，移入template spec
    deploy['spec']['template']['spec'] = data['spec']['template']['spec']

    #部署类型
    if data.get('deployKind','Deployment') == 'StatefulSet':
        deploy['kind'] = 'StatefulSet'
        deploy['spec']['volumeClaimTemplates'] = data['spec']['volumeClaimTemplates']
    
    #按stage填写差异化信息
    if data.get(stage, None) is not None:
        if data[stage].get('replicas',None) is not None:
    	    deploy['spec']['replicas'] = int(data[stage]['replicas'])
        if data[stage].get('namespace',None) is not None:
            deploy['metadata']['namespace'] = data[stage]['namespace']
        
        #若stage指定了特定的部署信息移入覆盖:
        if data[stage].get('spec',None) is not None:
            if data[stage]['spec'].get('template',None) is not None \
            and deploy['spec']['template'].get('spec',None):
                deploy['spec']['template']['spec'] = data[stage]['spec']['template']['spec']
            
            if data[stage]['spec'].get('volumeClaimTemplates',None) is not None :
                deploy['spec']['volumeClaimTemplates'] = data[stage]['spec']['volumeClaimTemplates']
    
    #最后写主容器的镜像信息
    for container in deploy['spec']['template']['spec']['containers']:
        if container['name'] == data['projectName']:
            container['image'] = image

    return deploy


basic_ingress_str = '''
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: unknown
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/limit-whitelist: "10.0.0.0/8"
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/app-root: /unknown
spec:
  rules:
  - host: rsync.common.alps.sjs.ted
    http:
      paths:
      - path: /unknown
        backend:
          serviceName: unknown
          servicePort: unknown
  - host: rsync.common01.alps.sjs.ted
    http:
      paths:
      - path: /unknown
        backend:
          serviceName: unknown
          servicePort: unknown
  - host: rsync.common03.alps.tc.ted
    http:
      paths:
      - path: /unknown
        backend:
          serviceName: unknown
          servicePort: unknown
  - host: rsync.common02.alps.tc.ted
    http:
      paths:
      - path: /unknown
        backend:
          serviceName: unknown
          servicePort: unknown
'''
#生成ingress部署配置
def as_ingress(data, path, stage='test'):
    ingress = load(basic_ingress_str)#基本结构

    ingress['metadata']['name'] = data['projectName']+"-"+path.replace("_", "-")+"-ingress"
    ingress['metadata']['namespace'] = namespace_by_stage(stage)
    ingress['metadata']['annotations']['nginx.ingress.kubernetes.io/app-root'] = '/'+path
    
    for rule in ingress['spec']['rules']:
        rule['http']['paths'][0]['path'] = '/'+path
        rule['http']['paths'][0]['backend']['serviceName'] = data['projectName']+'-'+stage
        rule['http']['paths'][0]['backend']['servicePort'] = data['serviceSpec']['ports'][0]['port']

    return ingress

basic_service_str = '''
apiVersion: v1
kind: Service
metadata:
  name: unknown
'''

#生成服务部署信息
def as_service(data, stage='test'):
    service = load( basic_service_str ) #基本结构

    #写元数据
    service['metadata']['name'] = data['projectName']+'-'+stage
    service['metadata']['namespace'] = namespace_by_stage(stage)

    #移入具体端口声明
    service['spec'] = data['serviceSpec']
    
    #差异化信息
    if data.get(stage, None) is not None:
        if data[stage].get('namespace',None) is not None:
            service['metadata']['namespace'] = data[stage]['namespace']
        if data[stage].get('nodePort',None) is not None:
            service['spec']['type'] = 'NodePort'
            service['spec']['ports'][0]['nodePort'] = data[stage]['nodePort']
    
    if stage != 'production':
        service['spec']['selector'] = {"app":data['projectName'],"stage":stage}
    else:
        service['spec']['selector'] = {"app":data['projectName']}
    
    return service
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(
	description='generate kube deploy files.', 
	usage='%(prog)s file -t type [options]')
    
    parser.add_argument(
	'file', 
	nargs='?', 
	help='the config file to generate deploy file')

    parser.add_argument(
	'-s','--stage', 
	nargs='?' ,required=True, 
	choices=['test','grey','production'], 
	help='the stage of the deploy file, allowed values: [test,grey,production]')
    
    parser.add_argument('-d', action='store_true', help=' gen deployment yaml file')
    parser.add_argument('-c', action='store_true', help=' gen configmap yaml file')
    parser.add_argument('-v', action='store_true', help=' gen service yaml file')
    parser.add_argument('-n', action='store_true', help=' gen ingress yaml file')

    parser.add_argument(
	'-i','--image', 
	nargs='?',
        default='busybox', 
	help = 'the project image to be deployed')
    
    parser.add_argument(
	'-p','--path', 
	nargs='?',  
	help = 'the service route subpath ')
    
    parser.add_argument(
	'-o','--output', 
	nargs='?', 
	help = 'the output file name')
    
    args = vars(parser.parse_args())
    config_file = args['file']
    stage = args['stage']
    path = args['path']
    output = args['output']
    image = args['image']
    
    config = load_config_file(config_file)
    yamls = []
    if args['d'] :
        yamls.append(as_deploy(config,image,stage))
    
    if args['v'] :
        yamls.append(as_service(config,stage))

    if args['n'] :
        yamls.append(as_ingress(config,path,stage))

    if args['c'] :
        yamls.append(as_configmap(config,stage))
    
    dump_new_file(yamls,output)

