# -*- mode: ruby -*-

Vagrant.configure(2) do |config|
  config.vm.box = "dongweiming/code"

  config.vm.network :forwarded_port, guest: 8200, host: 8200
  for i in 29000..30000
    config.vm.network :forwarded_port, guest: i, host: i
  end
end
