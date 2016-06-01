# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.require_version ">= 1.8"

if ["up", "provision", "status"].include?(ARGV.first)
  require_relative "deployment/vagrant/ansible_galaxy_helper"

  AnsibleGalaxyHelper.install_dependent_roles("deployment/ansible")
end

Vagrant.configure(2) do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.synced_folder "./", "/home/vagrant/climate-change-api"

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
  config.vm.network :forwarded_port, guest: 8080, host: Integer(ENV.fetch("CC_PORT_8080", 8080))
  config.vm.network :forwarded_port, guest: 8088, host: Integer(ENV.fetch("CC_PORT_8088", 8088))

  # django runserver/debugging
  config.vm.network :forwarded_port, guest: 8082, host: Integer(ENV.fetch("CC_PORT_8082", 8082))

  config.ssh.forward_x11 = true

  config.vm.provision "shell" do |s|
    s.inline = <<-SHELL
      if [ ! -x /usr/local/bin/ansible ]; then
        sudo apt-get update -qq
        sudo apt-get install python-pip python-dev -y
        sudo pip install paramiko==1.16.0
        sudo pip install ansible==2.0.2.0
      fi

      cd /vagrant/deployment/ansible && \
      ANSIBLE_FORCE_COLOR=1 PYTHONUNBUFFERED=1 ANSIBLE_CALLBACK_WHITELIST=profile_tasks \
      ansible-playbook -u vagrant -i 'localhost,' --extra-vars "dev_user=#{ENV.fetch("USER", "vagrant")} aws_profile=climate" \
          cc-api.yml
      cd /home/vagrant/climate-change-api
      su vagrant ./scripts/console django './manage.py migrate'
    SHELL
  end
end
