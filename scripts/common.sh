#Modify sudo's impact time
modify_sudo_time() {
    sudo sed -i 's/env_reset/env_reset, timestamp_timeout=240/g' /etc/sudoers
}

install_libmemcached() {
    #check libmemcached has installed
    if [ ! -f /usr/local/bin/memping ] ; then
        curl -L https://github.com/xtao/douban-patched/raw/master/libmemcached-douban-1.0.18.tar.gz |tar zx
        cd libmemcached-1.0.18
        ./configure && make && sudo make install
        cd ..
        rm -rf libmemcached-1.0.18
        echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf
        sudo /sbin/ldconfig
    fi
}

check_virtualenv() {
    which virtualenv > /dev/null 2>&1
    if [ $? != 0 ];then
        echo "Install virtualenv..."
        sudo pip install virtualenv
    fi
    virtualenv venv
    . venv/bin/activate
}

setup_database() {
    read -p "Please input Mysql User(default is root):" user
    if [ "${user}" = "" ];then
        user="root"
    fi
    read -p "Please input Mysql ${user}'s password(default is ''):" passwd
    echo "drop database if exists valentine" | mysql --user=${user} --password=${passwd}
    echo "create database valentine" | mysql --user=${user} --password=${passwd}
    if [b $? -ne 0 ]; then
        exit 1
    fi
    (echo "use valentine"; cat vilya/databases/schema.sql) | mysql --user=${user} --password=${passwd}
}

install_code() {
    git clone https://github.com/douban/code.git
    cd code
    echo "Setup database..."
    setup_database
    test "$CODE_ENV" != "unset" && check_virtualenv
    pip install cython  # should install first
    pip install -U setuptools  # python-libmemcached require updated setuptools
    pip install -r requirements.txt
}

start_app() {
    gunicorn -w 2 -b 127.0.0.1:8000 app:app  # web & git http daemon
}
