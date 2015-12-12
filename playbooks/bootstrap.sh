if [ ! -f $HOME/.ssh/id_rsa.pub ]; then
    ssh-keygen
fi

DEFAULT_SSH_PUBKEY=`cat $HOME/.ssh/id_rsa.pub`

if [ ! -d $HOME/.ssh  ]; then
      mkdir -p $HOME/.ssh
fi

chmod 0700 $HOME/.ssh
echo $DEFAULT_SSH_PUBKEY >> $HOME/.ssh/authorized_keys
chmod 0600 $HOME/.ssh/authorized_keys

sudo apt-get install ansible
