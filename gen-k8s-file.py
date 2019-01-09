import sys
import argparse
from yaml import load,dump

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

basic_service_str = '''
apiVersion: v1
kind: Service
metadata:
  name: unknown
'''

def load_config_file(filedir):
    with open(filedir,'r') as stream:
        return load(stream)

def dump_new_file(data,fileDir=None):
    if fileDir is not None:
        with open(fileDir,'w') as stream:
            dump(data,stream, default_flow_style=False)
    else:
      print(dump(data, default_flow_style=False))

def as_deploy(data,image,stage='test',namespace=None):
    deploy = load( basic_deploy_str )
    
    deploy['metadata']['name'] = data['projectName']+'-'+stage
    deploy['metadata']['labels']['app'] = data['projectName']
    deploy['spec']['selector']['matchLabels']['app'] = data['projectName']
    deploy['spec']['selector']['matchLabels']['stage'] = stage
    deploy['spec']['template']['metadata']['labels']['app'] = data['projectName']
    deploy['spec']['template']['metadata']['labels']['stage'] = stage
 
    deploy['spec']['template']['spec'] = data['spec']['template']['spec']
    if data.get('deployKind','Deployment') == 'StatefulSet':
        deploy['kind'] = 'StatefulSet'
        deploy['spec']['volumeClaimTemplates'] = data['spec']['volumeClaimTemplates']
    if data.get(stage, None) is not None:
        if data[stage].get('replicas',None) is not None:
    	    deploy['spec']['replicas'] = int(data[stage]['replicas'])
        if data[stage].get('namespace',None) is not None:
            deploy['metadata']['namespace'] = data[stage]['namespace']
    
    for container in deploy['spec']['template']['spec']['containers']:
        if container['name'] == data['projectName']:
            container['image'] = image

    return deploy

 
def as_service(data, port = None, stage='test', namespace=None):
    service = load( basic_service_str )
    service['metadata']['name'] = data['projectName']+'-'+stage
    if namespace is not None:
        service['metadata']['namespace'] = namespace
    
    service['spec'] = data['serviceSpec']
    if data.get(stage, None) is not None:
        if data[stage].get('namespace',None) is not None:
            service['metadata']['namespace'] = data[stage]['namespace']
        if data[stage].get('nodePort',None) is not None:
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
	'-t','--type', 
	nargs='?' ,required=True, 
	choices=['test','test-svc','grey','grey-svc','production','production-svc'], 
	help='the type of the deploy file to be generated, allowed values: [test,test-svc,grey,grey-svc,production,production-svc]')
   parser.add_argument(
	'-i','--image', 
	nargs='?',
        default='busybox', 
	help = 'the project image to be deployed')
   parser.add_argument(
	'-p','--port', 
	nargs='?', type=int, 
	help = 'the service node port if the type is -svc')
  
   parser.add_argument(
	'-o','--output', 
	nargs='?', 
	help = 'the output file name')
   args = vars(parser.parse_args())
   stage = args['type']
   config_file = args['file']
   port = args['port']
   output = args['output']
   image = args['image']
   
   config = load_config_file(config_file)
   if stage == 'test' or stage == 'grey' or stage == 'production':
     deploy_data = as_deploy(config,image,stage)
     dump_new_file(deploy_data,output)
   elif stage == 'test-svc' or stage == 'grey-svc' or stage == 'production-svc':
     service_data = as_service(config,port,stage.replace('-svc',''))
     dump_new_file(service_data,output)

