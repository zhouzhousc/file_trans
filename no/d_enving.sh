#！/bin/bash 

# Date：16:29 2020-03-09 
# Author: Create by Carl
# Description: This script function is django env 
# Version： 1.10
# no文件夹在~目录

echo "23716"|sudo -S apt update
echo "23716"|sudo -S apt upgrade -y

# 安装依赖
echo "23716"|sudo -S apt install python3-dev python3-pip python-pip memcached -y 
echo "23716"|sudo -S apt install supervisor -y
echo "23716"|sudo -S apt install nginx -y
echo "23716"|sudo -S apt-get install redis-server
echo "23716"|sudo -S apt-get install python-dev
echo "23716"|sudo -S apt-get install python3-virtualenv
echo "23716"|sudo -S apt install virtualenv
echo "23716"|sudo -S pip3 install virtualenv -i https://pypi.tuna.tsinghua.edu.cn/simple

mkdir edgeBox
echo "23716"|sudo -S cp -r ~/no/edgebox_final ~/edgeBox/
mkdir ~/edgeBox/ebenv
echo "23716"|sudo -S virtualenv -p /usr/bin/python3 ~/edgeBox/ebenv/edgebox_env
echo "23716"|sudo -S source ~/edgeBox/ebenv/edgebox_env/bin/activate

echo "23716"|sudo -S pip3 install -Ur ~/edgeBox/edgebox_final/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple && pip3 install -Ur ~/edgeBox/edgebox_final/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# gunicorn 配置
echo "23716"|sudo -S pip3 install gunicorn -i https://pypi.tuna.tsinghua.edu.cn/simple
echo "23716"|sudo -S cp ~/no/gunicorn_start.sh ~/edgeBox/ && echo "23716"|sudo -S chmod +x ~/edgeBox/gunicorn_start.sh && bash ~/edgeBox/gunicorn_start.sh

#nginx配置
# 删除默认配置
echo "23716"|sudo -S rm /etc/nginx/sites-enabled/default

#将no文件夹中edgebox_final.conf 放入/etc/nginx/sites-enabled/
echo "23716"|sudo -S cp ~/no/edgebox_final.conf /etc/nginx/sites-enabled/
echo "23716"|sudo -S cp ~/no/edgebox_vue.conf /etc/nginx/sites-enabled/

#其中edgebox_vue.conf配置文件中包含前端代码的路径，按实际更改
echo "23716"|sudo -S cp -r ~/no/dist ~/edgeBox/

#保存并退出。重启nginx:
echo "23716"|sudo -S /etc/init.d/nginx restart

#配置Supervisor
echo "23716"|sudo -S cp ~/no/supervisor_edgebox.conf /etc/nginx/sites-enabled/
echo "23716"|sudo -S mv /etc/nginx/sites-enabled/supervisor_edgebox.conf edgebox_final.conf

echo "23716"|sudo -S supervisorctl update
echo "23716"|sudo -S supervisorctl reload
echo "23716"|sudo -S /etc/init.d/memcached restart && sudo /etc/init.d/nginx restart
