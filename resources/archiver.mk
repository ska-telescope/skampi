.PHONY: get_archwizard_link get_archviewer_link


ARCHWIZ_IP=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc| grep archwizard | awk '{print $$4}')
ARCHWIZ_PORT=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc|grep archwizard |awk '{print $$5}'| cut -d ":" -f 1)
ARCHVIEWER_IP=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc| grep archviewer| awk '{print $$4}')
ARCHVIEWER_PORT=$(shell kubectl --kubeconfig=$(KUBECONFIG) get svc|grep archviewer |awk '{print $$5}'| cut -d ":" -f 1)

#VPN is required
#Provides ip and port for archwizard console
#Requries paramater KUBECONFIG
get_archwizard_link:
	$(info User must connect to VPN and click below link to access archwizard)
	@echo "http://$(ARCHWIZ_IP):$(ARCHWIZ_PORT)"
 

get_archviewer_link:
	$(info User must connect to VPN and click below link to access archviewer)	
	@echo "http://$(ARCHVIEWER_IP):$(ARCHVIEWER_PORT)"
