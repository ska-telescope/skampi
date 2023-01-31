import getopt, sys,yaml,logging,os

CONF_MANAGER="low-eda/cm/01"

try:
    opts, args = getopt.getopt(sys.argv[1:], "f:a:c:", ["attr_conf=","archived_file=","conf_manager="])


except getopt.GetoptError:
    print("Please provide proper arguments.")
    print("Usage: $python remove_attributes.py --attr_conf=<filepath or folder path> --archived_file=<filepath> --conf_manager=<conf_manager>")
    print("       filepath: File containing  attributes to remove from archiving")
    sys.exit(2)

for opt, arg in opts:
    if opt in ("-f", "--attr_conf"):
        ATTR_CONF = arg
        print(ATTR_CONF)
    if opt in ("-a", "--archived_file"):
        ARCHIVED_FILE = arg
    if opt in ("-c", "--conf_manager"):
        CONF_MANAGER = arg
    

try:
    if (not os.path.isdir(ATTR_CONF)): 
        attr_class={}
        with open(ATTR_CONF, 'r') as stream:
            data = yaml.load(stream,Loader=yaml.Loader)
            for conf_data in data.get('configuration'):
                attribute_list=[]
                attributes_configurations = conf_data.get("attributes")
                attribute_list=list(attributes_configurations.keys())
                if(conf_data["class"] in list(attr_class.keys())):
                    attr_class[conf_data["class"]].extend(attribute_list)
                else:   
                    attr_class[conf_data["class"]]=attribute_list

            
    else:
        attr_class={}
        for file in os.listdir(ATTR_CONF):
            with open((os.path.join(ATTR_CONF,file)), 'r') as stream:
                data = yaml.load(stream,Loader=yaml.Loader)
                for conf_data in data.get('configuration'):
                    attributes_configurations = conf_data.get("attributes")
                    attribute_list=list(attributes_configurations.keys())  
                    if(conf_data["class"] in list(attr_class.keys())):
                        attr_class[conf_data["class"]].extend(attribute_list)
                    else:   
                        attr_class[conf_data["class"]]=attribute_list


            
    with open(ARCHIVED_FILE,'r+') as arch_stream:
        data = yaml.load(arch_stream,Loader=yaml.Loader)
        classes=list(attr_class.keys())
        for conf_data in data.get('configuration'):
                if(conf_data['class']  in classes): 
                    archived_attr=[]
                    attributes_configurations = conf_data.get("attributes")
                    archived_attr=list(attributes_configurations.keys())
                    for attr in set(attr_class[conf_data['class']]): 
                        if attr.lower() in archived_attr:     
                            del conf_data.get("attributes")[attr.lower()]
                    data["manager"]=CONF_MANAGER

                    if(not conf_data["attributes"]):
                        del conf_data["attributes"]
                else:
                    continue
        
    with open(ARCHIVED_FILE,"w") as conf_stream:    
        conf_stream.write(yaml.dump(data, sort_keys=False))
        
except Exception as e:
    logging.error(e)