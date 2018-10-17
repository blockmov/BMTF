# CBS

## 项目介绍
BLOCK系统

## 软件架构
略


## 安装教程
将源码上传到/opt目录中，项目名字为cbs。

### 1. 安装python依赖包
	# cd /opt/cbs
	# pip install -r requirements.txt

### 2. 配置网站
	以下安装步骤以Ubuntu 16.04为例子。

	1. 安装supervisor工具
		# apt install supervisor

	2. 复制conf/cbs.conf文件到/etc/supervisor/conf.d目录中
		# cp conf/cbs.conf /etc/supervisor/conf.d

	3. 开启supervisor服务进程
		# systemctl enable supervisor
		# systemctl start supervisor
		# supervisorctl update
	
	4. 浏览器登录访问网页
		浏览器访问http://x.x.x.x:9001

# 使用说明
略


