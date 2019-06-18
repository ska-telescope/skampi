# setup defaults
vbox = ENV['V_BOX'] || "ubuntu/bionic64"
vsize = ENV['V_DISK_SIZE'] || "50GB"
vmem = (ENV['V_MEMORY'] || 4096).to_i
vcpus = (ENV['V_CPUS'] || 2).to_i
vip = ENV['V_IP'] || "172.200.0.25"

Vagrant.configure("2") do |config|
    config.vm.box = vbox
    config.disksize.size = vsize
    config.vm.synced_folder ".", "/vagrant"
    config.vm.network "private_network", ip: vip
    config.vm.provider "virtualbox" do |v|
       v.gui = false
       v.name = "minikube"
       v.memory = vmem
       v.cpus = vcpus
    end
    # Run ansible from within the Vagrant VM
    config.vm.provision "ansible_local" do |ansible|
       ansible.verbose = "v"
       ansible.inventory_path = "playbooks/hosts"
       ansible.config_file = "playbooks/ansible-local.cfg"
       ansible.limit = "development"
       ansible.playbook = "playbooks/deploy_minikube.yml"
       ansible.extra_vars = { use_driver: false }
     end
 end
