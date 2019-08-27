# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.8"

if ["up", "provision", "status"].include?(ARGV.first)
  require_relative "deployment/vagrant/ansible_galaxy_helper"

  AnsibleGalaxyHelper.install_dependent_roles("deployment/ansible")
end

ROOT_VM_DIR = "/home/vagrant/climate-change-api"

Vagrant.configure(2) do |config|
  config.vm.box = "bento/ubuntu-16.04"

  config.vm.synced_folder "./", ROOT_VM_DIR

  # Mount into directory to share creds
  config.vm.synced_folder "~/.aws", "/home/vagrant/.aws"

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :machine
  end

  config.vm.provider :virtualbox do |vb|
    vb.memory = 4096
    vb.cpus = 2
  end

  # django port
  config.vm.network :forwarded_port, guest: 8080, host: Integer(ENV.fetch("CC_PORT_8083", 8083))

  # nginx port
  config.vm.network :forwarded_port, guest: 8088, host: Integer(ENV.fetch("CC_PORT_8088", 8088))

  # docs port
  config.vm.network :forwarded_port, guest: 8084, host: Integer(ENV.fetch("CC_PORT_8084", 8084))

  # locust port
  config.vm.network :forwarded_port, guest: 8087, host: Integer(ENV.fetch("CC_PORT_8087", 8087))

  # django runserver/debugging
  config.vm.network :forwarded_port, guest: 8082, host: Integer(ENV.fetch("CC_PORT_8082", 8082))

  config.ssh.forward_x11 = true

  config.vm.provision "shell" do |s|
    s.path = 'deployment/vagrant/cd_shared_folder.sh'
    s.args = "'#{ROOT_VM_DIR}'"
  end

  config.vm.provision "shell" do |s|
    s.inline = <<-SHELL
      if [ ! -x /usr/local/bin/ansible ]; then
        sudo apt-get update -qq
        sudo apt-get install python-pip python-dev -y
        sudo pip install --upgrade pip
        sudo pip install ansible==2.4.6.0
      fi

      cd /vagrant/deployment/ansible && \
      ANSIBLE_FORCE_COLOR=1 PYTHONUNBUFFERED=1 ANSIBLE_CALLBACK_WHITELIST=profile_tasks \
      ansible-playbook -u vagrant -i 'localhost,' --extra-vars "dev_user=#{ENV.fetch("USER", "vagrant")} aws_profile=climate" \
          cc-api.yml
      cd "#{ROOT_VM_DIR}"
    SHELL
  end
end
